#!/usr/bin/env python3
"""
Add bidirectional links to Obsidian markdown files based on suggestions.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import argparse
import shutil
from datetime import datetime


class LinkAdder:
    def __init__(self, vault_path: str, suggestions_file: str, link_format: str = 'markdown',
                 dry_run: bool = False, backup: bool = False):
        self.vault_path = Path(vault_path)
        self.dry_run = dry_run
        self.backup = backup
        self.link_format = link_format  # 'markdown' or 'wikilink'

        with open(suggestions_file, 'r', encoding='utf-8') as f:
            self.suggestions = json.load(f)

        self.changes_made = []

    def add_links(self, min_confidence: str = 'low') -> Dict:
        """Add links to files based on suggestions."""
        confidence_levels = {'low': 0, 'medium': 1, 'high': 2}
        min_level = confidence_levels[min_confidence]

        for file_path, suggestions in self.suggestions.items():
            # Filter by confidence
            filtered_suggestions = [
                s for s in suggestions
                if confidence_levels.get(s['confidence'], 0) >= min_level
            ]

            if not filtered_suggestions:
                continue

            self._add_links_to_file(file_path, filtered_suggestions)

        return {
            'files_modified': len(self.changes_made),
            'links_added': sum(c['links_added'] for c in self.changes_made),
            'changes': self.changes_made,
            'dry_run': self.dry_run
        }

    def _add_links_to_file(self, file_path: str, suggestions: List[Dict]):
        """Add links to a single file."""
        full_path = self.vault_path / file_path

        if not full_path.exists():
            print(f"⚠️  File not found: {file_path}")
            return

        # Backup if needed
        if self.backup and not self.dry_run:
            self._backup_file(full_path)

        try:
            content = full_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            return

        original_content = content
        links_added = 0

        # Find insertion points and add links
        for suggestion in suggestions:
            target_file = suggestion['target']
            target_title = suggestion['target_title']

            # Check if link already exists
            if self._link_exists(content, target_file, target_title):
                continue

            # Find best insertion point
            insertion_point = self._find_insertion_point(content, suggestion)

            if insertion_point is not None:
                link = self._format_link(target_file, target_title)
                content = self._insert_link(content, link, insertion_point, suggestion)
                links_added += 1

        # Write changes
        if content != original_content:
            if not self.dry_run:
                full_path.write_text(content, encoding='utf-8')
                print(f"✅ Updated: {file_path} (+{links_added} links)")
            else:
                print(f"🔍 [DRY RUN] Would update: {file_path} (+{links_added} links)")

            self.changes_made.append({
                'file': file_path,
                'links_added': links_added,
                'suggestions_applied': links_added
            })

    def _backup_file(self, file_path: Path):
        """Create a backup of the file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = file_path.with_suffix(f'.{timestamp}.bak')
        shutil.copy2(file_path, backup_path)

    def _link_exists(self, content: str, target_file: str, target_title: str) -> bool:
        """Check if link to target already exists."""
        # Check wikilinks
        if re.search(rf'\[\[{re.escape(target_title)}(?:\|[^\]]+)?\]\]', content):
            return True

        # Check markdown links
        target_pattern = re.escape(target_file).replace(r'\ ', r'\s*')
        if re.search(rf'\[([^\]]+)\]\({target_pattern}\)', content):
            return True

        return False

    def _find_insertion_point(self, content: str, suggestion: Dict) -> Tuple[int, str]:
        """Find the best insertion point for the link."""
        # Strategy 1: Find mentions of concepts in the text
        for reason in suggestion['reasons']:
            # Extract concept from reason (e.g., "共享概念: Claude Code")
            concept_match = re.search(r'[:：]\s*(.+)$', reason)
            if concept_match:
                concept = concept_match.group(1).strip()
                # Find first occurrence of concept in content
                pattern = re.compile(re.escape(concept), re.IGNORECASE)
                match = pattern.search(content)
                if match:
                    return (match.start(), 'inline')

        # Strategy 2: Add to end of file (before any trailing whitespace)
        content_stripped = content.rstrip()
        return (len(content_stripped), 'section')

    def _format_link(self, target_file: str, target_title: str) -> str:
        """Format link based on vault settings."""
        if self.link_format == 'wikilink':
            return f'[[{target_title}]]'
        else:
            # Markdown link with relative path
            return f'[{target_title}]({target_file})'

    def _insert_link(self, content: str, link: str, insertion_point: Tuple[int, str],
                     suggestion: Dict) -> str:
        """Insert link at the specified point."""
        position, insert_type = insertion_point

        if insert_type == 'inline':
            # Insert inline after the concept mention
            before = content[:position]
            after = content[position:]

            # Find end of current word/phrase
            word_end = re.search(r'[\s,;.!?)]', after)
            if word_end:
                insert_pos = position + word_end.start()
                return content[:insert_pos] + f' {link}' + content[insert_pos:]
            else:
                return content[:position] + f' {link}' + after

        elif insert_type == 'section':
            # Add as a "Related Notes" section at the end
            if not content.endswith('\n\n'):
                if content.endswith('\n'):
                    content += '\n'
                else:
                    content += '\n\n'

            # Check if "Related Notes" section exists
            related_section = re.search(r'\n## 相关笔记\n', content)
            if related_section:
                # Add to existing section
                section_start = related_section.end()
                return content[:section_start] + f'- {link}\n' + content[section_start:]
            else:
                # Create new section
                return content + f'## 相关笔记\n\n- {link}\n'

        return content


def main():
    parser = argparse.ArgumentParser(description='Add links to Obsidian vault')
    parser.add_argument('vault_path', help='Path to Obsidian vault')
    parser.add_argument('--suggestions', '-s', help='Suggestions JSON file',
                        default='link_suggestions.json')
    parser.add_argument('--format', '-f', choices=['markdown', 'wikilink'],
                        default='markdown', help='Link format')
    parser.add_argument('--confidence', '-c', choices=['low', 'medium', 'high'],
                        default='medium', help='Minimum confidence level')
    parser.add_argument('--dry-run', '-d', action='store_true',
                        help='Preview changes without modifying files')
    parser.add_argument('--backup', action='store_true',
                        help='Create backup files (.bak) before modification')
    args = parser.parse_args()

    adder = LinkAdder(
        args.vault_path,
        args.suggestions,
        link_format=args.format,
        dry_run=args.dry_run,
        backup=args.backup
    )

    result = adder.add_links(min_confidence=args.confidence)

    print(f"\n{'🔍 [DRY RUN] ' if result['dry_run'] else ''}✅ Link addition complete!")
    print(f"📊 Stats:")
    print(f"   Files modified: {result['files_modified']}")
    print(f"   Links added: {result['links_added']}")

    if result['dry_run']:
        print(f"\n💡 Run without --dry-run to apply changes")


if __name__ == '__main__':
    main()

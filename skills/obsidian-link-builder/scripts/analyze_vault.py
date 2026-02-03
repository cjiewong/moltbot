#!/usr/bin/env python3
"""
Analyze Obsidian vault to extract concepts, tags, and potential link opportunities.
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple
import argparse


class VaultAnalyzer:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.files_data = {}
        self.concept_index = defaultdict(set)  # concept -> set of files
        self.tag_index = defaultdict(set)  # tag -> set of files
        self.link_graph = defaultdict(set)  # file -> set of linked files

    def analyze(self) -> Dict:
        """Analyze all markdown files in the vault."""
        md_files = list(self.vault_path.rglob("*.md"))

        for md_file in md_files:
            if self._should_skip(md_file):
                continue

            rel_path = str(md_file.relative_to(self.vault_path))
            file_data = self._analyze_file(md_file)
            self.files_data[rel_path] = file_data

            # Build indices
            for concept in file_data['concepts']:
                self.concept_index[concept.lower()].add(rel_path)

            for tag in file_data['tags']:
                self.tag_index[tag].add(rel_path)

            for link in file_data['existing_links']:
                self.link_graph[rel_path].add(link)

        return {
            'files': self.files_data,
            'concept_index': {k: list(v) for k, v in self.concept_index.items()},
            'tag_index': {k: list(v) for k, v in self.tag_index.items()},
            'link_graph': {k: list(v) for k, v in self.link_graph.items()},
            'stats': self._calculate_stats()
        }

    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        # Skip hidden files and directories
        parts = file_path.relative_to(self.vault_path).parts
        if any(part.startswith('.') for part in parts):
            return True
        return False

    def _analyze_file(self, file_path: Path) -> Dict:
        """Analyze a single markdown file."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return self._empty_file_data()

        return {
            'path': str(file_path.relative_to(self.vault_path)),
            'title': self._extract_title(content, file_path),
            'tags': self._extract_tags(content),
            'concepts': self._extract_concepts(content),
            'existing_links': self._extract_links(content),
            'headings': self._extract_headings(content),
            'word_count': len(content.split()),
            'directory': str(file_path.parent.relative_to(self.vault_path))
        }

    def _empty_file_data(self) -> Dict:
        """Return empty file data structure."""
        return {
            'path': '',
            'title': '',
            'tags': [],
            'concepts': [],
            'existing_links': [],
            'headings': [],
            'word_count': 0,
            'directory': ''
        }

    def _extract_title(self, content: str, file_path: Path) -> str:
        """Extract title from frontmatter or first heading or filename."""
        # Try frontmatter
        frontmatter_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if frontmatter_match:
            title_match = re.search(r'title:\s*["\']?([^"\'\n]+)["\']?', frontmatter_match.group(1))
            if title_match:
                return title_match.group(1).strip()

        # Try first H1 heading
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()

        # Use filename
        return file_path.stem

    def _extract_tags(self, content: str) -> List[str]:
        """Extract tags from content."""
        tags = set()

        # Frontmatter tags
        frontmatter_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if frontmatter_match:
            tags_match = re.search(r'tags:\s*\[(.*?)\]', frontmatter_match.group(1))
            if tags_match:
                tags.update(tag.strip().strip('"\'') for tag in tags_match.group(1).split(','))

        # Inline tags (#tag)
        inline_tags = re.findall(r'#([\w\-/]+)', content)
        tags.update(inline_tags)

        return sorted(list(tags))

    def _extract_concepts(self, content: str) -> List[str]:
        """Extract key concepts from content."""
        concepts = []

        # Extract from headings (they're usually important concepts)
        headings = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
        concepts.extend(headings)

        # Extract bold/emphasized terms (often key concepts)
        bold_terms = re.findall(r'\*\*([^*]+)\*\*', content)
        concepts.extend(bold_terms)

        # Extract terms in backticks (technical terms)
        code_terms = re.findall(r'`([^`]+)`', content)
        concepts.extend([term for term in code_terms if len(term.split()) <= 3])

        # Clean HTML tags and deduplicate
        cleaned_concepts = []
        for c in concepts:
            # Remove HTML tags
            clean = re.sub(r'<[^>]+>', '', c)
            # Remove extra whitespace
            clean = ' '.join(clean.split())
            if len(clean.strip()) > 2:
                cleaned_concepts.append(clean.strip())

        return list(set(cleaned_concepts))

    def _extract_links(self, content: str) -> List[str]:
        """Extract existing wikilinks and markdown links."""
        links = []

        # Wikilinks: [[Note]] or [[Note|Alias]]
        wikilinks = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)
        links.extend(wikilinks)

        # Markdown links to .md files: [text](path.md)
        md_links = re.findall(r'\[([^\]]+)\]\(([^)]+\.md)\)', content)
        links.extend([link[1] for link in md_links])

        return list(set(links))

    def _extract_headings(self, content: str) -> List[Dict[str, str]]:
        """Extract all headings with their levels."""
        headings = []
        for match in re.finditer(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE):
            headings.append({
                'level': len(match.group(1)),
                'text': match.group(2).strip()
            })
        return headings

    def _calculate_stats(self) -> Dict:
        """Calculate vault statistics."""
        total_files = len(self.files_data)
        total_links = sum(len(links) for links in self.link_graph.values())
        files_with_links = sum(1 for links in self.link_graph.values() if links)

        return {
            'total_files': total_files,
            'total_links': total_links,
            'files_with_links': files_with_links,
            'files_without_links': total_files - files_with_links,
            'avg_links_per_file': total_links / total_files if total_files > 0 else 0,
            'total_concepts': len(self.concept_index),
            'total_tags': len(self.tag_index)
        }


def main():
    parser = argparse.ArgumentParser(description='Analyze Obsidian vault')
    parser.add_argument('vault_path', help='Path to Obsidian vault')
    parser.add_argument('--output', '-o', help='Output JSON file', default='vault_analysis.json')
    args = parser.parse_args()

    analyzer = VaultAnalyzer(args.vault_path)
    result = analyzer.analyze()

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"✅ Analysis complete!")
    print(f"📊 Stats:")
    for key, value in result['stats'].items():
        print(f"   {key}: {value}")
    print(f"💾 Results saved to: {args.output}")


if __name__ == '__main__':
    main()

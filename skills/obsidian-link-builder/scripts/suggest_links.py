#!/usr/bin/env python3
"""
Suggest bidirectional links for Obsidian vault based on multiple strategies.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import argparse


class LinkSuggester:
    def __init__(self, analysis_file: str, vault_path: str, strategy: str = 'balanced'):
        with open(analysis_file, 'r', encoding='utf-8') as f:
            self.analysis = json.load(f)

        self.vault_path = Path(vault_path)
        self.strategy = strategy
        self.suggestions = defaultdict(list)

        # Strategy thresholds
        self.thresholds = {
            'conservative': {'min_score': 0.7, 'max_links_per_file': 5},
            'balanced': {'min_score': 0.5, 'max_links_per_file': 10},
            'aggressive': {'min_score': 0.3, 'max_links_per_file': 20}
        }

    def suggest_links(self) -> Dict:
        """Generate link suggestions for all files."""
        files = self.analysis['files']

        for file_path, file_data in files.items():
            suggestions = self._suggest_for_file(file_path, file_data)
            if suggestions:
                self.suggestions[file_path] = suggestions

        return dict(self.suggestions)

    def _suggest_for_file(self, file_path: str, file_data: Dict) -> List[Dict]:
        """Suggest links for a single file."""
        candidates = []
        existing_links = set(file_data['existing_links'])

        # Strategy 1: Concept matching
        candidates.extend(self._find_by_concepts(file_path, file_data, existing_links))

        # Strategy 2: Tag similarity
        candidates.extend(self._find_by_tags(file_path, file_data, existing_links))

        # Strategy 3: Directory proximity
        candidates.extend(self._find_by_directory(file_path, file_data, existing_links))

        # Strategy 4: Title/filename similarity
        candidates.extend(self._find_by_title(file_path, file_data, existing_links))

        # Deduplicate and score
        scored_candidates = self._score_and_rank(candidates, file_data)

        # Filter by strategy threshold
        threshold = self.thresholds[self.strategy]
        filtered = [
            c for c in scored_candidates
            if c['score'] >= threshold['min_score']
        ][:threshold['max_links_per_file']]

        return filtered

    def _find_by_concepts(self, file_path: str, file_data: Dict, existing: Set) -> List[Dict]:
        """Find files sharing concepts."""
        candidates = []
        concept_index = self.analysis['concept_index']

        for concept in file_data['concepts']:
            concept_lower = concept.lower()
            if concept_lower in concept_index:
                for target_file in concept_index[concept_lower]:
                    if target_file != file_path and target_file not in existing:
                        candidates.append({
                            'target': target_file,
                            'reason': f'共享概念: {concept}',
                            'strategy': 'concept',
                            'weight': 0.4
                        })

        return candidates

    def _find_by_tags(self, file_path: str, file_data: Dict, existing: Set) -> List[Dict]:
        """Find files with similar tags."""
        candidates = []
        tag_index = self.analysis['tag_index']

        for tag in file_data['tags']:
            if tag in tag_index:
                for target_file in tag_index[tag]:
                    if target_file != file_path and target_file not in existing:
                        candidates.append({
                            'target': target_file,
                            'reason': f'共享标签: #{tag}',
                            'strategy': 'tag',
                            'weight': 0.3
                        })

        return candidates

    def _find_by_directory(self, file_path: str, file_data: Dict, existing: Set) -> List[Dict]:
        """Find files in the same or related directories."""
        candidates = []
        current_dir = file_data['directory']

        for target_file, target_data in self.analysis['files'].items():
            if target_file == file_path or target_file in existing:
                continue

            target_dir = target_data['directory']

            # Same directory
            if target_dir == current_dir:
                candidates.append({
                    'target': target_file,
                    'reason': f'同目录: {current_dir}',
                    'strategy': 'directory',
                    'weight': 0.2
                })
            # Parent/child directory
            elif target_dir.startswith(current_dir) or current_dir.startswith(target_dir):
                candidates.append({
                    'target': target_file,
                    'reason': f'相关目录',
                    'strategy': 'directory',
                    'weight': 0.1
                })

        return candidates

    def _find_by_title(self, file_path: str, file_data: Dict, existing: Set) -> List[Dict]:
        """Find files with similar titles."""
        candidates = []
        current_title = file_data['title'].lower()
        current_words = set(re.findall(r'\w+', current_title))

        for target_file, target_data in self.analysis['files'].items():
            if target_file == file_path or target_file in existing:
                continue

            target_title = target_data['title'].lower()
            target_words = set(re.findall(r'\w+', target_title))

            # Calculate word overlap
            common_words = current_words & target_words
            if len(common_words) >= 2:  # At least 2 common words
                similarity = len(common_words) / max(len(current_words), len(target_words))
                candidates.append({
                    'target': target_file,
                    'reason': f'标题相似 ({", ".join(list(common_words)[:3])})',
                    'strategy': 'title',
                    'weight': 0.3 * similarity
                })

        return candidates

    def _score_and_rank(self, candidates: List[Dict], file_data: Dict) -> List[Dict]:
        """Score and rank candidates, handling duplicates."""
        # Aggregate scores for duplicate targets
        target_scores = defaultdict(lambda: {'score': 0, 'reasons': [], 'strategies': set()})

        for candidate in candidates:
            target = candidate['target']
            target_scores[target]['score'] += candidate['weight']
            target_scores[target]['reasons'].append(candidate['reason'])
            target_scores[target]['strategies'].add(candidate['strategy'])

        # Convert to list and add target info
        scored = []
        for target, data in target_scores.items():
            target_data = self.analysis['files'].get(target, {})
            scored.append({
                'target': target,
                'target_title': target_data.get('title', Path(target).stem),
                'score': min(data['score'], 1.0),  # Cap at 1.0
                'reasons': data['reasons'],
                'strategies': list(data['strategies']),
                'confidence': self._calculate_confidence(data['score'], len(data['strategies']))
            })

        # Sort by score descending
        scored.sort(key=lambda x: x['score'], reverse=True)
        return scored

    def _calculate_confidence(self, score: float, num_strategies: int) -> str:
        """Calculate confidence level."""
        if score >= 0.7 and num_strategies >= 3:
            return 'high'
        elif score >= 0.5 and num_strategies >= 2:
            return 'medium'
        else:
            return 'low'


def main():
    parser = argparse.ArgumentParser(description='Suggest links for Obsidian vault')
    parser.add_argument('vault_path', help='Path to Obsidian vault')
    parser.add_argument('--analysis', '-a', help='Analysis JSON file', default='vault_analysis.json')
    parser.add_argument('--output', '-o', help='Output JSON file', default='link_suggestions.json')
    parser.add_argument('--strategy', '-s', choices=['conservative', 'balanced', 'aggressive'],
                        default='balanced', help='Link suggestion strategy')
    args = parser.parse_args()

    suggester = LinkSuggester(args.analysis, args.vault_path, args.strategy)
    suggestions = suggester.suggest_links()

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(suggestions, f, indent=2, ensure_ascii=False)

    total_suggestions = sum(len(s) for s in suggestions.values())
    print(f"✅ Link suggestions generated!")
    print(f"📊 Stats:")
    print(f"   Files with suggestions: {len(suggestions)}")
    print(f"   Total suggestions: {total_suggestions}")
    print(f"   Strategy: {args.strategy}")
    print(f"💾 Results saved to: {args.output}")


if __name__ == '__main__':
    main()

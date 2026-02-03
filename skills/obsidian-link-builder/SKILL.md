---
name: obsidian-link-builder
description: Analyze Obsidian vault markdown files and intelligently add bidirectional links to enhance knowledge graph connectivity. Uses multiple strategies (concept matching, tag similarity, directory proximity, title similarity) to identify related notes and suggest contextual inline links. Use when working with Obsidian vaults to build or optimize link networks, improve discoverability, or enhance graph view relationships. Triggers include requests like "add links to my notes", "analyze vault for link opportunities", "optimize knowledge graph", or "build bidirectional links between related files".
---

# Obsidian Link Builder

Intelligently analyze Obsidian vault files and add bidirectional links to enhance knowledge graph connectivity and note discoverability.

## Overview

This skill helps build a rich network of bidirectional links in Obsidian vaults by:
- Analyzing vault structure, concepts, tags, and content
- Identifying related files using multiple strategies
- Suggesting contextual link placements
- Adding links inline where concepts are mentioned
- Respecting existing links to avoid duplication

## When to Use This Skill

Invoke this skill when the user requests:
- "分析这个文件并添加相关链接"
- "优化整个 vault 的链接网络"
- "为 AI Learning 目录建立知识图谱"
- "添加双向链接"
- "分析笔记之间的关系"
- "增强 Obsidian 图谱"

## Workflow

### 1. Understand Requirements

First, clarify the scope and preferences:

```
Questions to ask:
- Which directory/files to analyze? (specific folder or entire vault)
- Link density preference? (conservative/balanced/aggressive)
- Minimum confidence level? (high/medium/low)
- Link format? (markdown or wikilink)
- Dry-run first? (preview before applying)
```

### 2. Analyze Vault

Run the analysis script to extract vault structure and content:

```bash
python scripts/analyze_vault.py <vault_path> --output vault_analysis.json
```

**What it does:**
- Scans all markdown files
- Extracts titles, tags, concepts, headings
- Identifies existing links
- Builds concept and tag indices
- Calculates vault statistics

**Output:** `vault_analysis.json` containing:
- File metadata (titles, tags, concepts, existing links)
- Concept index (which files mention which concepts)
- Tag index (which files have which tags)
- Link graph (current link relationships)
- Statistics (total files, links, coverage)

### 3. Generate Link Suggestions

Run the suggestion script with chosen strategy:

```bash
python scripts/suggest_links.py <vault_path> \
  --analysis vault_analysis.json \
  --strategy balanced \
  --output link_suggestions.json
```

**Strategies:**
- `conservative`: High-quality links only (score ≥ 0.7, max 5 per file)
- `balanced`: Moderate density (score ≥ 0.5, max 10 per file) - **Default**
- `aggressive`: Dense network (score ≥ 0.3, max 20 per file)

**What it does:**
- Applies 4 matching strategies (see [Linking Strategies](#linking-strategies))
- Scores and ranks candidates
- Filters by strategy thresholds
- Assigns confidence levels (high/medium/low)

**Output:** `link_suggestions.json` containing:
- Suggested links for each file
- Target files and titles
- Relevance scores and confidence
- Reasons for each suggestion

### 4. Review Suggestions

Present suggestions to user for review:

```
Example output format:
📄 File: 30-AI Learning/docs/claude code/SKILLS/Claude Code Skills.md
  → [SKILLS.md] (score: 0.85, confidence: high)
     Reasons: 共享概念: Skills, 共享标签: #claude-code, 同目录
  → [SubAgent.md] (score: 0.62, confidence: medium)
     Reasons: 共享概念: Claude Code, 相关目录
```

Ask user:
- Are these suggestions appropriate?
- Should we adjust the strategy?
- Any files to exclude?
- Ready to proceed?

### 5. Add Links

Apply the suggestions with user-approved settings:

```bash
python scripts/add_links.py <vault_path> \
  --suggestions link_suggestions.json \
  --format markdown \
  --confidence medium \
  --dry-run  # Remove for actual execution
```

**Parameters:**
- `--format`: `markdown` (relative paths) or `wikilink` (Obsidian native)
- `--confidence`: `high`, `medium`, or `low` (minimum confidence to apply)
- `--dry-run`: Preview changes without modifying files
- `--backup`: Create .bak backup files before modification (optional, for vaults without git)

**What it does:**
- Finds optimal insertion points (inline where concepts mentioned)
- Formats links according to vault settings
- Checks for existing links to avoid duplication
- Optionally creates backups if --backup flag is used
- Adds links and reports changes

### 6. Verify Results

After adding links:
1. Check a few modified files manually
2. Verify links work correctly
3. Assess readability and link density
4. Use Obsidian graph view to visualize improvements

## Linking Strategies

The skill uses four complementary strategies to identify related files:

### 1. Concept Matching (weight: 0.4)
Finds files sharing key concepts extracted from:
- Headings and subheadings
- **Bold text** (important terms)
- `Code terms` (technical concepts)

### 2. Tag Similarity (weight: 0.3)
Finds files with common tags from:
- Frontmatter: `tags: [ai, claude]`
- Inline: `#claude-code #skills`

### 3. Directory Proximity (weight: 0.2)
Finds files in related locations:
- Same directory: 0.2
- Parent/child directory: 0.1

### 4. Title Similarity (weight: 0.3 × similarity)
Finds files with overlapping title words:
- Requires ≥2 common words
- Weighted by overlap ratio

**Score Calculation:**
Scores accumulate when multiple strategies match. Final score capped at 1.0.

**Confidence Levels:**
- **High**: Score ≥ 0.7 AND ≥3 strategies matched
- **Medium**: Score ≥ 0.5 AND ≥2 strategies matched
- **Low**: Other matches

For detailed strategy explanations, see [references/linking-strategies.md](references/linking-strategies.md).

## Link Insertion

### Insertion Strategies

**1. Inline Insertion (Preferred)**
Insert link where the concept is first mentioned:
```markdown
Claude Code 提供了强大的 [Skills 系统](./SKILLS.md)。
```

**2. Section End**
Add "相关笔记" section at document end:
```markdown
## 相关笔记

- [Claude Code Skills](./SKILLS/Claude Code Skills.md)
- [SubAgent 功能](./SubAgent.md)
```

### Link Format

Respects vault settings (`.obsidian/app.json`):

**Markdown Links (this vault's setting):**
```markdown
[显示文本](相对路径/文件.md)
```

**Wikilinks (alternative):**
```markdown
[[文件名]]
[[文件名|显示文本]]
```

For syntax details, see [references/obsidian-syntax.md](references/obsidian-syntax.md).

## Quality Assurance

### Automatic Checks
- Avoids duplicate links
- Validates file existence
- Maintains link density limits
- Preserves existing formatting
- Git-friendly (no .bak files by default)

### Quality Standards
- **Relevance**: Links must be contextually appropriate
- **Density**: 2-4 links per 500 words (balanced strategy)
- **Readability**: Links don't disrupt reading flow
- **Bidirectionality**: Considers reciprocal links

For quality criteria, see [references/quality-criteria.md](references/quality-criteria.md).

## Common Workflows

### Workflow 1: Analyze Single Directory
```bash
# Analyze specific directory
python scripts/analyze_vault.py . --output ai_learning_analysis.json

# Generate suggestions (balanced)
python scripts/suggest_links.py . \
  --analysis ai_learning_analysis.json \
  --strategy balanced

# Preview changes
python scripts/add_links.py . \
  --format markdown \
  --confidence medium \
  --dry-run

# Apply changes
python scripts/add_links.py . \
  --format markdown \
  --confidence medium
```

### Workflow 2: Optimize Entire Vault
```bash
# Full vault analysis
python scripts/analyze_vault.py . --output vault_analysis.json

# Conservative suggestions (high quality only)
python scripts/suggest_links.py . \
  --strategy conservative

# Apply high-confidence links only
python scripts/add_links.py . \
  --confidence high
```

### Workflow 3: Iterative Improvement
```bash
# Round 1: High confidence links
python scripts/add_links.py . --confidence high

# Round 2: Medium confidence links
python scripts/add_links.py . --confidence medium

# Review and decide on low confidence links
python scripts/add_links.py . --confidence low --dry-run
```

## Important Notes

### Vault Configuration
This vault uses:
- **Link format**: Markdown links (not wikilinks)
- **Path format**: Relative paths
- **Auto-backup**: Enabled by obsidian-git plugin

Always use `--format markdown` when adding links to this vault.

### Backup and Safety
- Git version control is recommended (this vault has git enabled)
- Use `--dry-run` to preview changes before applying
- Optional: Use `--backup` flag to create .bak files if needed
- Review changes in git before committing

### Performance
- Analysis time: ~1-2 seconds per 100 files
- Suggestion time: ~2-5 seconds per 100 files
- Link addition: ~1 second per 10 files

### Limitations
- Does not use AI/embeddings for semantic similarity
- Does not analyze full content (only titles, headings, concepts)
- Does not consider temporal relationships
- May suggest links between loosely related files (filter with confidence levels)

## Troubleshooting

### Issue: Too many suggestions
**Solution:** Use `conservative` strategy or increase `--confidence` level

### Issue: Too few suggestions
**Solution:** Use `aggressive` strategy or lower `--confidence` level

### Issue: Links in wrong format
**Solution:** Check vault settings and use correct `--format` parameter

### Issue: Script errors
**Solution:** Ensure Python 3.7+ installed, check file paths are correct

## Resources

### Scripts
- `scripts/analyze_vault.py` - Vault analysis and indexing
- `scripts/suggest_links.py` - Link suggestion generation
- `scripts/add_links.py` - Link insertion and modification

### References
- `references/linking-strategies.md` - Detailed strategy explanations
- `references/obsidian-syntax.md` - Obsidian link syntax reference
- `references/quality-criteria.md` - Link quality standards

All scripts support `--help` flag for detailed usage information.

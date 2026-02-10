---
name: obsidian-huaigu
description: Search, retrieve, and summarize notes in the Obsidian vault at ~/obsidian/obsidian_huaigu (PARA-style: 00-Inbox/01-Projects/02-Areas/03-Resources/04-Atlas/05-Archive/90-Templates/99-System). Use for knowledge-base Q&A, locating where a topic is documented, listing relevant notes, extracting key excerpts, and lightweight vault upkeep (e.g., suggesting tags/links or small edits) with approval before any bulk changes.
---

# Obsidian Huaigu

Use this skill to treat `~/obsidian/obsidian_huaigu` as the user’s personal knowledge base.

## Quick start (always sync first)

0. **Sync the vault before reading/searching** (keep answers up-to-date):
   - Run `bash skills/obsidian-huaigu/scripts/vault_git_sync.sh`.
   - If `git pull --rebase` reports conflicts, **stop** and ask the user how to resolve.

1. Identify intent:
   - **Find**: “在哪写过…/给我相关笔记/搜一下关键词”
   - **Answer from notes**: “我之前怎么配置的…/那篇笔记结论是什么”
   - **Light upkeep**: “帮我整理/加链接/改标题/归档” (ask for approval before edits)

2. Search:
   - Use `scripts/vault_search.py` to locate candidate notes and relevant excerpts.

3. Read only the needed files and answer with:
   - Top relevant note paths
   - Short excerpt(s)
   - Your synthesized answer + citation (filename + section heading if possible)

## Vault map / rules

- Read `references/vault.md` for vault root + folder map + safety rules.
- Read `references/ingest.md` for ingesting DOCX/PDF/URL into the vault.

**Do not edit** `.obsidian/`, `.git/`, `.claude/` unless explicitly asked.

## Common operations

### D) Add a document/link to the knowledge base (ingest)

Use when the user sends:

- a **Word (.docx)**
- a **PDF (.pdf)**
- a **web link**

Workflow:

1. **Sync first**: `bash skills/obsidian-huaigu/scripts/vault_git_sync.sh`
   - If conflicts happen, stop and ask the user.
2. Convert to Markdown:
   - DOCX (preferred): `pandoc <file.docx> -t gfm --wrap=none -o /tmp/ingest.md`
   - DOCX (fallback): `python3 skills/obsidian-huaigu/scripts/convert_docx_to_md.py <file.docx> --title "<title>" > /tmp/ingest.md`
   - PDF: `python3 skills/obsidian-huaigu/scripts/convert_pdf_to_md.py <file.pdf> --title "<title>" > /tmp/ingest.md`
   - URL: fetch with `web_fetch(url, extractMode=markdown)` and save to `/tmp/ingest.md`
3. Propose destination (AI suggestion):
   - `python3 skills/obsidian-huaigu/scripts/suggest_destination.py --md /tmp/ingest.md --title "<title>"`
   - **Show the proposed folder + filename** and ask the user to approve.
   - If user rejects, let the user specify the destination folder/path.
   - Create folders as needed.
4. Write the markdown into the vault at the approved path.
5. Commit + push:
   - `bash skills/obsidian-huaigu/scripts/vault_git_commit_push.sh "~/obsidian/obsidian_huaigu" "kb: ingest <title>"`
   - If push rejected, sync again; if conflicts, stop and ask the user.

### A) Full-text search (recommended)

Run:

- `python3 skills/obsidian-huaigu/scripts/vault_search.py "<query>" --limit 50`

Tips:

- Use `--fixed-strings` for literal queries like `#todo` or `[[Some Link]]`.
- Use `--context 2` when you need surrounding lines.

### B) List recently updated notes

Run:

- `python3 skills/obsidian-huaigu/scripts/vault_recent.py --n 30`

### C) Light maintenance (approval required + commit/push)

Allowed only after user approval:

- Small edits to a specific note (typos, add a short section, add a link)
- Suggesting tag/link candidates (do not bulk apply without approval)

**After any edit** (even small):

1. Ensure vault is clean or you understand the diff: `git status` / `git diff`
2. Commit + push:
   - Run `bash skills/obsidian-huaigu/scripts/vault_git_commit_push.sh "~/obsidian/obsidian_huaigu" "<commit message>"`

If `git push` is rejected (non-fast-forward), run sync again and retry.

For bulk operations (rename/move/mass link insert):

1. propose plan + sample of affected files
2. wait for explicit “执行”
3. apply changes
4. commit + push

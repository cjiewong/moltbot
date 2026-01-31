# Ingest documents into the vault (DOCX/PDF/URL -> Markdown)

Goal: take an incoming **Word/PDF/link**, convert to **Markdown**, and add it to the vault.

## High-level rules

- Always `git pull --rebase` before reading OR writing.
- The agent must propose a destination folder (may create new folders), but **must ask the user to approve**.
- If the user rejects, user can:
  - pick from existing folders
  - provide an exact destination path
- After writing, commit + push.
- If sync or push results in conflicts/non-fast-forward, stop and ask user how to proceed.

## Conversion options

- DOCX -> MD:
  - Preferred: `pandoc input.docx -t gfm --wrap=none` (best quality if available)
  - Fallback: `scripts/convert_docx_to_md.py` (text-only)
- PDF -> MD: `scripts/convert_pdf_to_md.py` (via `pdftotext`).
- URL -> MD: use the agent's `web_fetch` tool (extractMode=markdown), then save.

## Destination suggestion

- Use `scripts/suggest_destination.py` on the produced markdown to propose a relative path.
- Default pattern: `<bucket>/Inbox/<title>.md`.

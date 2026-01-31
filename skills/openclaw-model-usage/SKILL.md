---
name: openclaw-model-usage
description: Check and summarize OpenClaw model/provider usage (e.g., Codex 5h/day quota remaining, reset times, plus spend) by running `openclaw status --usage` (typically via `pnpm -s openclaw status --usage` inside the OpenClaw repo). Use when the user asks things like “我的 codex 用量/额度还剩多少/什么时候重置”, “model usage”, “Codex 5h/day remaining”, or when troubleshooting provider auth warnings shown in the Usage section (e.g., MiniMax cookie missing).
---

# OpenClaw Model Usage

## Quick workflow

1. Run usage
   - Preferred (repo-local):
     - `cd /home/cjie/dev/moltbot && pnpm -s openclaw status --usage`
   - If you only need to share a full status page (sessions + usage):
     - `pnpm -s openclaw status --all`

2. Summarize the key numbers in human terms
   - For **Codex**: report **5h remaining % + reset ETA**, and **Day remaining % + reset ETA**.
   - If the output includes auth warnings (e.g. **“MiniMax: cookie is missing, log in again”**), call it out explicitly.

## Automation (script)

Use the bundled script to fetch + parse into structured JSON:

- `python3 scripts/query_usage.py --json`
- Optional:
  - `python3 scripts/query_usage.py --raw` (verbatim CLI output)
  - `OPENCLAW_REPO=/path/to/repo python3 scripts/query_usage.py --json`

The JSON format is:

- `providers.<ProviderName>.warning` (if any)
- `providers.<ProviderName>.plan` (if present)
- `providers.<ProviderName>.windows.<Window>.leftPercent`
- `providers.<ProviderName>.windows.<Window>.resetsIn`

## Notes / common gotchas

- `openclaw status --usage` may show provider-specific errors when cookies/tokens expire. If a provider fails, report the warning and suggest re-login for that provider.
- If the user wants “Codex 总花费/按模型花费” (not quota remaining), that is a different workflow (cost analytics) and may require a different skill/tooling.

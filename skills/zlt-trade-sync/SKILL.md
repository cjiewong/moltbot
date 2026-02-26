---
name: zlt-trade-sync
description: 同步涨乐通（华泰）成交邮件到 Obsidian 交易周报（trading-YYYY），自动去重并 commit+push。
---

# ZLT Trade Sync

## Quick start

Run the sync script (default: last 30 days, Asia/Shanghai; auto commit + push):

```bash
python3 skills/zlt-trade-sync/scripts/sync_zlt_trades.py
```

Dry-run (no file writes / no git changes):

```bash
python3 skills/zlt-trade-sync/scripts/sync_zlt_trades.py --dry-run
```

Common overrides:

```bash
# last 7 days
python3 skills/zlt-trade-sync/scripts/sync_zlt_trades.py --days 7

# explicit date window (Asia/Shanghai)
python3 skills/zlt-trade-sync/scripts/sync_zlt_trades.py --after 2026/01/11 --before 2026/02/11

# do not push (still commits)
python3 skills/zlt-trade-sync/scripts/sync_zlt_trades.py --no-push

# do not commit (writes only)
python3 skills/zlt-trade-sync/scripts/sync_zlt_trades.py --no-commit
```

## Workflow (guardrails)

1. **Sync the vault first**: the script runs `git pull --rebase` in the vault.
   - If conflicts occur, stop and resolve manually.

2. **Fetch emails** via `gog` Gmail search:
   - Query: `from:qqt_ufg_client@htsc.com after:<start> before:<end>`
   - Filters to `subject=订单执行情况通知`

3. **Parse HTML table rows**:
   - Direction mapping: `bid→买入`, `ask→卖出`
   - Uses **最新成交数量/最新成交价格** as qty/price.

4. **Ignore non-filled notifications**:
   - If 最新成交数量 <= 0 OR 最新成交价格 <= 0: do not write; add to review output.

5. **Write weekly note rows**:
   - Path: `01-Projects/trading-YYYY/<week>.md`
   - Auto-create missing week files with the standard 12-col header.
   - Dedup key: `交易日期 + 代码 + 方向 + 点位 + 仓位`

6. **Auto commit + push** (default):
   - `git add 01-Projects`
   - `git commit -m "kb: sync zlt trades lastXd"`
   - `git push`

## Outputs

- `/tmp/zlt-mail-index.json` — matched email index
- `/tmp/zlt-missing-trades.json` — trades that were newly written
- `/tmp/zlt-review.json` — emails/rows ignored or requiring manual inspection

## References

- Table schema + rules: `references/md_table_schema.md`

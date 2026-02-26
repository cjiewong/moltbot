# ZLT → Obsidian Trading Weekly Table Schema

## Target vault path

- Vault: `~/obsidian/obsidian_huaigu`
- Trading weekly notes live under: `01-Projects/trading-YYYY/`

## Target Markdown table (12 columns)

Column order (MUST match):

1. 交易日期
2. 交易标的
3. 代码
4. 方向
5. 点位
6. 仓位
7. Plan Risk
8. Plan Reward
9. 计划盈亏比
10. result
11. 盈利
12. 交易理由

Header + separator:

```md
| 交易日期 | 交易标的 | 代码 | 方向 | 点位 | 仓位 | Plan Risk | Plan Reward | 计划盈亏比 | result | 盈利 | 交易理由 |
| -------- | -------- | ---- | ---- | ---- | ---- | --------- | ----------- | ---------- | ------ | ---- | -------- |
```

## Direction mapping (Huatai email)

Huatai email uses `bid/ask` in the table.

- `bid` → 买入
- `ask` → 卖出

## Week file naming

- Week starts on Monday, ends on Sunday (Asia/Shanghai date)
- Filename pattern:

`YYYY-M-D-YYYY-M-D.md`

Example: `2026-2-2-2026-2-8.md`

## Dedup key (idempotency)

Use this key to detect already-synced rows:

- `交易日期 + 代码 + 方向 + 点位 + 仓位`

(Do NOT include 标的中文名 to avoid false negatives.)

## Ignore / review rules

If an email row has **最新成交数量 <= 0** OR **最新成交价格 <= 0**, treat it as **non-fill / not executed**:

- Do NOT write to weekly notes
- Record to a review JSON for manual inspection

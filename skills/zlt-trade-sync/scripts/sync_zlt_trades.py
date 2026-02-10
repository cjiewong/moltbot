#!/usr/bin/env python3
"""Sync Huatai (涨乐通) trade execution emails into Obsidian weekly trading notes.

Defaults are opinionated for cjie:
- Gmail via gog (OAuth)
- Vault: ~/obsidian/obsidian_huaigu
- Sender: qqt_ufg_client@htsc.com
- Subject: 订单执行情况通知
- Timezone: Asia/Shanghai

Writes Markdown table rows into 01-Projects/trading-YYYY/<week>.md
Then commits + pushes the vault git repo (unless --no-commit/--no-push).

Outputs:
- /tmp/zlt-mail-index.json
- /tmp/zlt-missing-trades.json
- /tmp/zlt-review.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Any, Dict, List, Tuple

from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Shanghai")

DEFAULT_VAULT = Path.home() / "obsidian" / "obsidian_huaigu"
DEFAULT_SENDER = "qqt_ufg_client@htsc.com"
DEFAULT_SUBJECT = "订单执行情况通知"

TABLE_HEADER = "|交易日期|交易标的|代码|方向|点位|仓位|Plan Risk|Plan Reward|计划盈亏比|result|盈利|交易理由|\n"
TABLE_SEP = "|---|---|---|---|---|---|---|---|---|---|---|---|\n"


def run(cmd: List[str], *, cwd: Path | None = None, check: bool = True) -> str:
    p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and p.returncode != 0:
        raise RuntimeError(f"cmd failed: {cmd}\nstdout:\n{p.stdout}\nstderr:\n{p.stderr}")
    return p.stdout


def shanghai_today() -> date:
    return datetime.now(TZ).date()


def ymd_slash(d: date) -> str:
    return f"{d.year}/{d.month:02d}/{d.day:02d}"


def ymd_md(d: date) -> str:
    return f"{d.year}/{d.month}/{d.day}"


def compute_week_range(d: date) -> Tuple[date, date]:
    start = d - timedelta(days=d.weekday())  # Monday
    end = start + timedelta(days=6)
    return start, end


def week_filename(d: date) -> str:
    s, e = compute_week_range(d)
    return f"{s.year}-{s.month}-{s.day}-{e.year}-{e.month}-{e.day}.md"


def direction_map(raw: str) -> str:
    raw = (raw or "").strip().lower()
    if raw == "bid":
        return "买入"
    if raw == "ask":
        return "卖出"
    return raw


def parse_email_date(headers_date: str) -> date:
    # Example: Fri, 6 Feb 2026 23:18:04 +0800 (CST)
    # We drop the parenthetical timezone name.
    base = headers_date.split(" (")[0].strip()
    dt = datetime.strptime(base, "%a, %d %b %Y %H:%M:%S %z")
    return dt.astimezone(TZ).date()


def strip_html(html: str) -> str:
    html = re.sub(r"<script.*?</script>", "", html, flags=re.S | re.I)
    html = re.sub(r"<style.*?</style>", "", html, flags=re.S | re.I)
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    html = re.sub(r"</p>", "\n", html, flags=re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    html = html.replace("&nbsp;", " ")
    html = re.sub(r"\s+", " ", html)
    return html.strip()


def extract_table_rows(html: str) -> List[List[str]]:
    tbodies = re.findall(r"<tbody[^>]*>(.*?)</tbody>", html, flags=re.S | re.I)
    rows: List[List[str]] = []
    for tbody in tbodies:
        trs = re.findall(r"<tr[^>]*>(.*?)</tr>", tbody, flags=re.S | re.I)
        for tr in trs:
            tds = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.S | re.I)
            tds_clean = [strip_html(td) for td in tds]
            tds_clean = [t for t in tds_clean if t != ""]
            if tds_clean:
                rows.append(tds_clean)
    return rows


def ensure_week_file(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(TABLE_HEADER + TABLE_SEP)


def parse_existing_keys(trading_dir: Path) -> set[Tuple[str, str, str, str, str]]:
    existing: set[Tuple[str, str, str, str, str]] = set()
    if not trading_dir.exists():
        return existing
    for p in sorted(trading_dir.glob("*.md")):
        txt = p.read_text(errors="ignore")
        for l in txt.splitlines():
            l = l.strip()
            if not l.startswith("|"):
                continue
            if l.startswith("|交易日期|") or l.startswith("|---"):
                continue
            parts = [c.strip() for c in l.strip("|").split("|")]
            if len(parts) < 6:
                continue
            d, code, side, price, qty = parts[0], parts[2], parts[3], parts[4], parts[5]
            existing.add((d, code, side, price, qty))
    return existing


def trade_key(t: Dict[str, str]) -> Tuple[str, str, str, str, str]:
    return (t["交易日期"], t["代码"], t["方向"], t["点位"], t["仓位"])


def append_trades(path: Path, trades: List[Dict[str, str]]) -> None:
    ensure_week_file(path)
    txt = path.read_text(errors="ignore")
    if not txt.endswith("\n"):
        txt += "\n"
    for t in trades:
        row = (
            f"|{t['交易日期']}|{t['交易标的']}|{t['代码']}|{t['方向']}|{t['点位']}|{t['仓位']}|"
            f"{t['Plan Risk']}|{t['Plan Reward']}|{t['计划盈亏比']}|{t['result']}|{t['盈利']}|{t['交易理由']}|\n"
        )
        txt += row
    path.write_text(txt)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default=str(DEFAULT_VAULT))
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--after", default=None, help="YYYY/MM/DD (Asia/Shanghai) override")
    ap.add_argument("--before", default=None, help="YYYY/MM/DD (Asia/Shanghai) override")
    ap.add_argument("--sender", default=DEFAULT_SENDER)
    ap.add_argument("--subject", default=DEFAULT_SUBJECT)
    ap.add_argument("--max", type=int, default=500)
    ap.add_argument("--cache-dir", default="/tmp/zlt_mail_cache")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-commit", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    args = ap.parse_args()

    vault = Path(args.vault).expanduser()
    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    today = shanghai_today()
    if args.after:
        after = args.after
    else:
        after = ymd_slash(today - timedelta(days=args.days))

    if args.before:
        before = args.before
    else:
        before = ymd_slash(today + timedelta(days=1))

    query = f"from:{args.sender} after:{after} before:{before}"

    # 1) Sync repo first
    run(["git", "pull", "--rebase"], cwd=vault)

    # 2) Search messages
    out = run(["gog", "gmail", "messages", "search", query, "--max", str(args.max), "--json"])
    idx = json.loads(out)
    Path("/tmp/zlt-mail-index.json").write_text(out)

    messages = idx.get("messages") or []
    messages = [m for m in messages if m.get("subject") == args.subject]

    review: List[Dict[str, Any]] = []
    parsed: List[Dict[str, str]] = []

    # 3) Parse each message
    for m in messages:
        mid = m["id"]
        cache = cache_dir / f"{mid}.json"
        if cache.exists():
            msg_json = json.loads(cache.read_text())
        else:
            msg_raw = run(["gog", "gmail", "get", mid, "--format=full", "--json"])
            cache.write_text(msg_raw)
            msg_json = json.loads(msg_raw)

        headers = msg_json.get("headers", {})
        try:
            d = parse_email_date(headers.get("date", ""))
        except Exception as e:
            review.append({"id": mid, "reason": f"bad_date:{e}", "headers": headers})
            continue

        html = msg_json.get("body", "")
        rows = extract_table_rows(html)
        if not rows:
            review.append({"id": mid, "reason": "no_rows", "date": headers.get("date"), "subject": headers.get("subject")})
            continue

        for r in rows:
            # Expected: 股份代码,订单编号,币种,买卖方向,委托数量,委托价格,最新成交数量,最新成交价格,...
            if len(r) < 8:
                review.append({"id": mid, "reason": "short_row", "row": r})
                continue
            symbol = r[0]
            side = direction_map(r[3])
            qty = r[6]
            price = r[7]

            try:
                if float(str(qty).strip() or "0") <= 0:
                    review.append({"id": mid, "reason": "qty_le_0", "row": r, "symbol": symbol})
                    continue
                if float(str(price).strip() or "0") <= 0:
                    review.append({"id": mid, "reason": "price_le_0", "row": r, "symbol": symbol})
                    continue
            except Exception:
                # keep; but still write (rare)
                pass

            parsed.append(
                {
                    "交易日期": ymd_md(d),
                    "交易标的": symbol,
                    "代码": symbol,
                    "方向": side,
                    "点位": str(price),
                    "仓位": str(qty),
                    "Plan Risk": "",
                    "Plan Reward": "",
                    "计划盈亏比": "",
                    "result": "",
                    "盈利": "",
                    "交易理由": "",
                    "_week_file": week_filename(d),
                    "_year": str(d.year),
                }
            )

    # 4) Dedup vs existing
    bydir: Dict[Path, List[Dict[str, str]]] = {}
    missing: List[Dict[str, str]] = []

    # Build existing keys per year directory as needed
    existing_cache: Dict[Path, set[Tuple[str, str, str, str, str]]] = {}

    for t in parsed:
        trading_dir = vault / "01-Projects" / f"trading-{t['_year']}"
        if trading_dir not in existing_cache:
            existing_cache[trading_dir] = parse_existing_keys(trading_dir)
        if trade_key(t) in existing_cache[trading_dir]:
            continue
        missing.append(t)
        fpath = trading_dir / t["_week_file"]
        bydir.setdefault(fpath, []).append(t)

    Path("/tmp/zlt-missing-trades.json").write_text(json.dumps({"missing": missing}, ensure_ascii=False, indent=2))
    Path("/tmp/zlt-review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2))

    if args.dry_run:
        print(f"[dry-run] messages={len(messages)} parsed={len(parsed)} missing={len(missing)} review={len(review)}")
        for fp, ts in sorted(bydir.items(), key=lambda x: str(x[0])):
            print(f"[dry-run] would_write {len(ts)} -> {fp}")
        return 0

    # 5) Write
    for fp, ts in bydir.items():
        append_trades(fp, ts)

    # 6) Commit + push
    if not args.no_commit:
        run(["git", "add", "01-Projects"], cwd=vault)
        msg = f"kb: sync zlt trades last{args.days}d"
        run(["git", "commit", "-m", msg], cwd=vault)
        if not args.no_push:
            run(["git", "push"], cwd=vault)

    print(f"messages={len(messages)} parsed={len(parsed)} missing={len(missing)} review={len(review)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

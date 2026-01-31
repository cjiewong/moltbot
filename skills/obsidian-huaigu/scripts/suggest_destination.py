#!/usr/bin/env python3
"""Suggest a destination folder (and filename) for a markdown document.

Heuristic only. The agent should still ask the user to approve/override.

Input: markdown file (or stdin) and optional title hint.
Output: a suggested relative path under the vault.

Usage:
  python3 suggest_destination.py --md /path/to/doc.md
  cat doc.md | python3 suggest_destination.py --title "Some Title"
"""

from __future__ import annotations

import argparse
import os
import re
import sys


def slugify(name: str) -> str:
    name = name.strip()
    name = re.sub(r"[\\/:*?\"<>|]", "-", name)
    name = re.sub(r"\s+", " ", name)
    name = name.replace(" ", "-")
    name = re.sub(r"-+", "-", name)
    return name[:120] if name else "note"


def guess_bucket(text: str) -> str:
    t = text
    # crude keyword routing
    if re.search(r"\b(ea|mt5|mql|python|node|typescript|k8s|docker)\b", t, re.I):
        return "20-Coding"
    if re.search(r"(交易|策略|回测|量化|套利|期权|期货|外汇|仓位|对冲)", t):
        return "10-Trading"
    if re.search(r"(旅行|酒店|机票|行程|亲子|签证)", t):
        return "40-Life"
    if re.search(r"\b20\d{2}[-/]?(0?[1-9]|1[0-2])[-/]?(0?[1-9]|[12]\d|3[01])\b", t):
        return "00-Diary"
    if re.search(r"(MBTI|LLM|prompt|agent|Claude|Gemini|OpenAI)", t, re.I):
        return "30-AI Learning"
    return "90-Others"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", help="path to markdown; if omitted, read stdin")
    ap.add_argument("--title", default=None)
    ap.add_argument("--ext", default=".md")
    args = ap.parse_args()

    if args.md:
        try:
            with open(args.md, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception as e:
            print(f"ERROR: cannot read {args.md}: {e}", file=sys.stderr)
            return 1
    else:
        text = sys.stdin.read()

    title = args.title
    if not title:
        m = re.search(r"^#\s+(.+)$", text, re.M)
        if m:
            title = m.group(1).strip()

    bucket = guess_bucket(text)

    filename = slugify(title or "note") + args.ext

    # default subfolder for loose notes
    sub = "Inbox"
    rel = os.path.join(bucket, sub, filename)
    print(rel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

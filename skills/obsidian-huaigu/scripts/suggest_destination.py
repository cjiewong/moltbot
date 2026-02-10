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
    """Return a *relative folder* under the vault.

    The vault currently follows PARA, so we route into existing PARA folders.
    Keep this conservative: prefer routing to folders that exist (or are safe to create).
    """
    t = text

    # Web clips / zhihu
    if re.search(r"^#\s*知乎摘录｜", t, re.M) or re.search(r"zhuanlan\.zhihu\.com|www\.zhihu\.com", t):
        return os.path.join("03-Resources", "Clippings")

    # Coding references
    if re.search(r"\b(ea|mt5|mql|python|node|typescript|k8s|docker|linux|sql|mysql|postgres)\b", t, re.I):
        return os.path.join("03-Resources", "Coding-References")

    # Trading
    if re.search(r"(交易|策略|回测|量化|套利|期权|期货|外汇|仓位|对冲)", t):
        # Prefer references; strategies can be more opinionated
        return os.path.join("03-Resources", "trading-references")

    # Life guides / travel
    if re.search(r"(旅行|酒店|机票|行程|亲子|签证)", t):
        return os.path.join("03-Resources", "Life-Guides")

    # Dated notes: put into Inbox by default (user can re-file later)
    if re.search(r"\b20\d{2}[-/]?(0?[1-9]|1[0-2])[-/]?(0?[1-9]|[12]\d|3[01])\b", t):
        return "00-Inbox"

    # AI learning/tools
    if re.search(r"(MBTI|LLM|prompt|agent|Claude|Gemini|OpenAI)", t, re.I):
        return os.path.join("03-Resources", "AI-Tools")

    return "00-Inbox"


def _expand(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))


def _vault_root_default() -> str:
    return _expand("~/obsidian/obsidian_huaigu")


def _dir_exists(vault_root: str, rel_dir: str) -> bool:
    return os.path.isdir(os.path.join(vault_root, rel_dir))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", help="path to markdown; if omitted, read stdin")
    ap.add_argument("--title", default=None)
    ap.add_argument("--ext", default=".md")
    ap.add_argument(
        "--vault-root",
        default=_vault_root_default(),
        help="vault root path (default: ~/obsidian/obsidian_huaigu)",
    )
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

    vault_root = _expand(args.vault_root)

    bucket = guess_bucket(text)

    # If the bucket doesn't exist in the actual vault, fall back to Inbox.
    # (We don't create folders here; this script only suggests a destination.)
    if not _dir_exists(vault_root, bucket):
        bucket = "00-Inbox"

    filename = slugify(title or "note") + args.ext

    rel = os.path.join(bucket, filename)
    print(rel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

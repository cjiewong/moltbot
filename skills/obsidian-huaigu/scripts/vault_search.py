#!/usr/bin/env python3
"""Search the obsidian_huaigu vault.

Strategy:
- Prefer ripgrep (rg) if available (fast).
- Fallback to a pure-Python scan if rg is not installed (slower but works everywhere).

Examples:
  python3 vault_search.py "MiniMax" --limit 20
  python3 vault_search.py "HSBC" --glob "*.md" --context 2
  python3 vault_search.py "#todo" --fixed-strings

Exit codes:
  0 on success (even if no matches)
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import shutil
import subprocess
import sys


def expand(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))


def iter_md_files(vault: str, pattern: str):
    for base, dirs, files in os.walk(vault):
        # skip heavy/irrelevant dirs
        dirs[:] = [d for d in dirs if d not in {".git", ".obsidian", ".claude", "node_modules"}]
        for f in files:
            if fnmatch.fnmatch(f, pattern):
                yield os.path.join(base, f)


def python_search(query: str, vault: str, glob: str, context: int, limit: int, ignore_case: bool):
    q = query if not ignore_case else query.lower()
    printed = 0
    for path in iter_md_files(vault, glob):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                lines = fp.readlines()
        except Exception:
            continue
        for i, line in enumerate(lines):
            hay = line if not ignore_case else line.lower()
            if q in hay:
                start = max(0, i - context)
                end = min(len(lines), i + context + 1)
                rel = os.path.relpath(path, vault)
                for j in range(start, end):
                    prefix = f"{rel}:{j+1}:"
                    print(prefix + lines[j].rstrip("\n"))
                    printed += 1
                    if printed >= limit:
                        return


def rg_search(rg: str, args):
    cmd = [
        rg,
        "--no-heading",
        "--line-number",
        "--color",
        "never",
        "--glob",
        args.glob,
    ]
    if args.context > 0:
        cmd += ["-C", str(args.context)]
    if args.fixed_strings:
        cmd.append("-F")
    if args.ignore_case:
        cmd.append("-i")

    cmd += [args.query, args.vault]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert proc.stdout is not None
    assert proc.stderr is not None

    printed = 0
    try:
        for line in proc.stdout:
            print(line, end="")
            printed += 1
            if printed >= args.limit:
                proc.terminate()
                break
    finally:
        _ = proc.stdout.close()

    stderr = proc.stderr.read().strip()
    _ = proc.stderr.close()
    rc = proc.wait()

    # rg returns 1 for no matches.
    if stderr and rc not in (0, 1):
        print(stderr, file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("query", help="search query")
    ap.add_argument(
        "--vault",
        default="~/obsidian/obsidian_huaigu",
        help="vault root (default: ~/obsidian/obsidian_huaigu)",
    )
    ap.add_argument("--glob", default="*.md", help="file glob (default: *.md)")
    ap.add_argument("--context", type=int, default=0, help="lines of context")
    ap.add_argument("--limit", type=int, default=50, help="max lines to print")
    ap.add_argument(
        "--fixed-strings",
        action="store_true",
        help="treat query as a literal string (best-effort for python fallback)",
    )
    ap.add_argument(
        "--ignore-case",
        action="store_true",
        help="case-insensitive",
    )
    args = ap.parse_args()

    vault = expand(args.vault)
    if not os.path.isdir(vault):
        print(f"ERROR: vault not found: {vault}", file=sys.stderr)
        return 1

    rg = shutil.which("rg")
    if rg:
        # Use rg for speed.
        args.vault = vault
        rg_search(rg, args)
        return 0

    # Python fallback.
    python_search(args.query, vault, args.glob, args.context, args.limit, args.ignore_case)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

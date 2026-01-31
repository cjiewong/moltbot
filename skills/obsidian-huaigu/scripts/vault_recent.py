#!/usr/bin/env python3
"""List recently modified markdown notes in the vault."""

from __future__ import annotations

import argparse
import os
import time


def expand(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))


def iter_files(root: str):
    for base, dirs, files in os.walk(root):
        # skip heavy/irrelevant dirs
        dirs[:] = [d for d in dirs if d not in {".git", ".obsidian", ".claude", "node_modules"}]
        for f in files:
            if f.lower().endswith(".md"):
                yield os.path.join(base, f)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default="~/obsidian/obsidian_huaigu")
    ap.add_argument("--n", type=int, default=30)
    args = ap.parse_args()

    vault = expand(args.vault)
    if not os.path.isdir(vault):
        print(f"ERROR: vault not found: {vault}")
        return 1

    rows = []
    for p in iter_files(vault):
        try:
            st = os.stat(p)
        except FileNotFoundError:
            continue
        rows.append((st.st_mtime, p))

    rows.sort(reverse=True)
    for mtime, p in rows[: args.n]:
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))
        rel = os.path.relpath(p, vault)
        print(f"{ts}\t{rel}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Query OpenClaw model usage (Codex/Claude/MiniMax/etc.) via `openclaw status --usage`.

Default execution uses pnpm in the OpenClaw repo, which is the most reliable way to
ensure the correct CLI is invoked.

Examples:
  python3 scripts/query_usage.py
  python3 scripts/query_usage.py --repo /home/cjie/dev/moltbot
  python3 scripts/query_usage.py --raw
  python3 scripts/query_usage.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    p = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return p.returncode, (p.stdout or "")


def _parse_usage(text: str) -> dict:
    # Extract the Usage block (best-effort).
    m = re.search(r"(?ms)^Usage\s*$\n(?P<body>.*?)(?:\n\s*FAQ:|\Z)", text)
    body = m.group("body") if m else text

    # The CLI may include a leading "Usage:" line inside the block; drop it.
    body_lines = body.splitlines()
    if body_lines and body_lines[0].strip() == "Usage:":
        body_lines = body_lines[1:]
    body = "\n".join(body_lines)

    result: dict = {"raw": body.strip(), "providers": {}}

    # Provider header example:
    #   Codex (plus ($0.00))
    # Followed by indented lines like:
    #   5h: 96% left · resets 2h 21m
    # Note: provider plan can contain nested parentheses (e.g. "plus ($0.00)").
    metric_line = re.compile(
        r"^(?P<window>[^:]+):\s*(?P<left>\d+)%\s+left\s+·\s+resets\s+(?P<resets>.+?)\s*$"
    )

    current_provider: str | None = None

    for line in body.splitlines():
        s = line.strip()
        if not s:
            continue

        # 1) Metrics lines (require an active provider)
        ml = metric_line.match(s)
        if ml and current_provider:
            window = ml.group("window").strip()
            left = int(ml.group("left"))
            resets = ml.group("resets").strip()
            result["providers"][current_provider].setdefault("windows", {})[window] = {
                "leftPercent": left,
                "resetsIn": resets,
            }
            continue

        # 2) Provider warnings like: "MiniMax: cookie is missing, log in again"
        if ":" in s and not metric_line.match(s):
            left, right = s.split(":", 1)
            prov = left.strip()
            msg = right.strip()
            result["providers"].setdefault(prov, {})
            result["providers"][prov]["warning"] = msg
            current_provider = None
            continue

        # 3) Provider header (usually has optional plan in parentheses)
        if ":" not in s:
            # Provider header, optionally with a plan in parentheses.
            name = s
            plan = None
            if " (" in s and s.endswith(")"):
                name, rest = s.split(" (", 1)
                plan = rest[:-1]  # drop trailing ')'
            current_provider = name.strip()
            result["providers"].setdefault(current_provider, {})
            if plan:
                result["providers"][current_provider]["plan"] = plan.strip()
            result["providers"][current_provider].setdefault("windows", {})
            continue

        current_provider = None
        continue

    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--repo",
        default=os.environ.get("OPENCLAW_REPO", "/home/cjie/dev/moltbot"),
        help="Path to the OpenClaw repo (default: /home/cjie/dev/moltbot or $OPENCLAW_REPO)",
    )
    ap.add_argument("--raw", action="store_true", help="Print raw `openclaw status --usage` output")
    ap.add_argument("--json", action="store_true", help="Print parsed usage JSON")
    args = ap.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    if not repo.exists():
        raise SystemExit(f"Repo not found: {repo}")

    # Prefer pnpm-wrapped CLI for consistency.
    code, out = _run(["pnpm", "-s", "openclaw", "status", "--usage"], cwd=repo)

    if args.raw and not args.json:
        sys.stdout.write(out)
        return code

    parsed = _parse_usage(out)
    if code != 0:
        parsed["error"] = {
            "code": code,
            "message": "openclaw status --usage failed (non-zero exit). See raw output.",
        }
    if args.json or not args.raw:
        sys.stdout.write(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n")
        return 0

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(0)

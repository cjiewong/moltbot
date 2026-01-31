#!/usr/bin/env python3
"""Convert a PDF to Markdown via pdftotext (dependency-light).

Usage:
  python3 convert_pdf_to_md.py input.pdf > out.md

Notes:
- Relies on `pdftotext` being available.
- Produces plain text wrapped as Markdown paragraphs.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf_path")
    ap.add_argument("--title", default=None)
    args = ap.parse_args()

    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        print("ERROR: pdftotext not found in PATH", file=sys.stderr)
        return 2

    # -layout keeps rough layout; '-' outputs to stdout
    cmd = [pdftotext, "-layout", args.pdf_path, "-"]
    try:
        res = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        print(f"ERROR: failed to run pdftotext: {e}", file=sys.stderr)
        return 1

    if res.returncode != 0:
        err = res.stderr.decode("utf-8", errors="ignore").strip()
        print(f"ERROR: pdftotext failed ({res.returncode}): {err}", file=sys.stderr)
        return res.returncode

    text = res.stdout.decode("utf-8", errors="ignore")
    text = "\n".join([ln.rstrip() for ln in text.splitlines()])

    if args.title:
        sys.stdout.write(f"# {args.title}\n\n")

    # Keep blank lines; markdown can handle it.
    sys.stdout.write(text.strip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

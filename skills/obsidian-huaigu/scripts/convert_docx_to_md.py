#!/usr/bin/env python3
"""Convert a .docx file to a simple Markdown document.

This is a dependency-free fallback converter:
- Extracts text from word/document.xml
- Preserves paragraph breaks

Usage:
  python3 convert_docx_to_md.py input.docx > out.md

Notes:
- Formatting (bold, tables, images) is not preserved.
- Good enough for knowledge-base ingestion when pandoc isn't available.
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
import xml.etree.ElementTree as ET


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


def iter_paragraph_text(xml_bytes: bytes) -> list[str]:
    root = ET.fromstring(xml_bytes)
    paras: list[str] = []
    for p in root.findall(".//w:p", NS):
        texts = [t.text or "" for t in p.findall(".//w:t", NS)]
        s = "".join(texts).strip()
        if s:
            paras.append(s)
    return paras


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("docx_path")
    ap.add_argument("--title", default=None)
    args = ap.parse_args()

    try:
        with zipfile.ZipFile(args.docx_path, "r") as z:
            xml_bytes = z.read("word/document.xml")
    except Exception as e:
        print(f"ERROR: failed to read docx: {e}", file=sys.stderr)
        return 1

    paras = iter_paragraph_text(xml_bytes)
    out = io.StringIO()
    if args.title:
        out.write(f"# {args.title}\n\n")

    for p in paras:
        out.write(p)
        out.write("\n\n")

    sys.stdout.write(out.getvalue().rstrip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

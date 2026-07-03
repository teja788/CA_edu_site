#!/usr/bin/env python3
"""Stamp lastChecked dates across src/data/ after a fully green link sweep.

Run by the weekly link-check workflow only when every ResourceLink URL
responded; the workflow then commits the updated dates. Matches the formats
used in the data files:

    lastChecked: '28 Jun 2026'      (JS)
    "lastChecked": "28 Jun 2026"    (JSON)
    last_checked: 2026-06-28        (YAML, e.g. sources.yaml)

Usage: update_last_checked.py [--date '3 Jul 2026'] [--root src/data]
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

PATTERNS = [
    (re.compile(r"(lastChecked:\s*')[^']*(')"), "js"),
    (re.compile(r'("lastChecked":\s*")[^"]*(")'), "json"),
    (re.compile(r"(last_checked:\s*)[^\s#]+"), "yaml"),
]


def human_date(d: date) -> str:
    return f"{d.day} {d.strftime('%b %Y')}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="date in '3 Jul 2026' form; default today")
    ap.add_argument("--root", type=Path, default=REPO / "src" / "data")
    args = ap.parse_args(argv)

    today = date.today()
    stamp = args.date or human_date(today)
    iso = today.isoformat()

    targets = [p for p in sorted(args.root.rglob("*"))
               if p.suffix in {".js", ".json", ".yaml", ".yml"} and "questions" not in p.parts]
    if (REPO / "sources.yaml").exists():
        targets.append(REPO / "sources.yaml")

    total = 0
    for path in targets:
        text = path.read_text(encoding="utf-8")
        new = text
        for pattern, kind in PATTERNS:
            value = iso if kind == "yaml" else stamp
            if kind == "yaml":
                new = pattern.sub(lambda m: m.group(1) + value, new)
            else:
                new = pattern.sub(lambda m: m.group(1) + value + m.group(2), new)
        if new != text:
            n = sum(len(p.findall(text)) for p, _ in PATTERNS)
            path.write_text(new, encoding="utf-8")
            rel = path.relative_to(REPO) if path.is_relative_to(REPO) else path
            print(f"stamped {n:3d} date(s) in {rel}")
            total += n
    print(f"{total} lastChecked date(s) updated to {stamp}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

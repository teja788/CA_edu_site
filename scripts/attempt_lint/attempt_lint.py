#!/usr/bin/env python3
"""Attempt-tagging lint (plan §6.2, §6.4 — the day-one requirement).

Law/tax content that isn't pinned to an attempt and a law-as-on date is a
liability: it silently rots when the Finance Act changes. This lint FAILS the
build when any question or note belonging to a volatile Intermediate paper
(P2 Corporate & Other Laws, P3 Taxation, P5 Auditing & Ethics) lacks its tags.

Checked:
  * Question banks   src/data/questions/intermediate/<volatile-paper>/*.json
      every entry needs non-empty `applicableAttempts` AND `lawAsOnDate`
      (case_mcq_set entries carry the tags on the set, not the sub-questions).
  * Notes (MDX)      src/pages/intermediate/<volatile-paper>/**/*.mdx
      frontmatter needs `applicable_attempts` AND `law_as_on_date`.
      Volatile-paper notes must be MDX (the NotesLayout chapter template) —
      a .astro note page under a volatile paper dir is itself flagged, since
      its frontmatter can't be linted.

Exit codes: 0 all tagged · 1 violations found · 2 usage/config error.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

VOLATILE_PAPERS = ("corporate-and-other-laws", "taxation", "auditing-and-ethics")

# Pages under a volatile paper dir that are navigation, not law content.
NON_CONTENT_STEMS = {"index", "amendments", "weightage"}


def lint_bank(path: Path) -> list[str]:
    problems: list[str] = []
    try:
        bank = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path}: invalid JSON ({exc})"]
    for q in bank.get("questions", []):
        qid = q.get("id", "<no id>")
        attempts = q.get("applicableAttempts")
        if not (isinstance(attempts, list) and attempts):
            problems.append(f"{path}: {qid} missing/empty applicableAttempts")
        if not q.get("lawAsOnDate"):
            problems.append(f"{path}: {qid} missing lawAsOnDate")
    return problems


FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---", re.DOTALL)


def lint_mdx(path: Path) -> list[str]:
    problems: list[str] = []
    match = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    frontmatter = match.group(1) if match else ""
    for key in ("applicable_attempts", "law_as_on_date"):
        if not re.search(rf"^{key}\s*:", frontmatter, re.MULTILINE):
            problems.append(f"{path}: frontmatter missing {key}")
    return problems


def main() -> int:
    root = Path(sys.argv[sys.argv.index("--root") + 1]) if "--root" in sys.argv else Path(__file__).resolve().parents[2]
    if not (root / "src").is_dir():
        print(f"attempt_lint: no src/ under {root}", file=sys.stderr)
        return 2

    problems: list[str] = []
    checked = 0
    for paper in VOLATILE_PAPERS:
        for bank in sorted((root / "src/data/questions/intermediate" / paper).glob("*.json")):
            checked += 1
            problems += lint_bank(bank)
        pages_dir = root / "src/pages/intermediate" / paper
        for note in sorted(pages_dir.rglob("*.mdx")):
            checked += 1
            problems += lint_mdx(note)
        for page in sorted(pages_dir.rglob("*.astro")):
            if page.stem not in NON_CONTENT_STEMS:
                checked += 1
                problems.append(
                    f"{page}: volatile-paper note pages must be MDX with "
                    "applicable_attempts + law_as_on_date frontmatter (found .astro)"
                )

    for p in problems:
        print(f"  FAIL {p}")
    if problems:
        print(f"\nattempt_lint: {len(problems)} violation(s) in volatile papers (P2/P3/P5).")
        print("Every law/tax question needs applicableAttempts + lawAsOnDate;")
        print("every note needs applicable_attempts + law_as_on_date frontmatter.")
        return 1
    print(f"attempt_lint: {checked} file(s) checked, all law/tax content attempt-tagged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

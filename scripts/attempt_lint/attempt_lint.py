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

import argparse
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


def frontmatter_has_value(frontmatter: str, key: str) -> bool:
    """True if `key` is present with a non-empty value.

    A bare `law_as_on_date:` is as useless as a missing one — the bank lint
    already rejects empty tags, so the MDX lint must too. Accepts either an
    inline value (`key: 2026-02-28`) or a YAML block value on the following
    indented lines (`applicable_attempts:` + `  - 'Sept 2026'`), which is how
    the real notes are written.
    """
    match = re.search(rf"^{re.escape(key)}[ \t]*:[ \t]*(.*)$", frontmatter, re.MULTILINE)
    if match is None:
        return False
    if match.group(1).strip():
        return True
    for line in frontmatter[match.end():].splitlines():
        if line.strip():
            return line[0] in (" ", "\t")
    return False


def lint_mdx(path: Path) -> list[str]:
    problems: list[str] = []
    match = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    frontmatter = match.group(1) if match else ""
    for key in ("applicable_attempts", "law_as_on_date"):
        if not frontmatter_has_value(frontmatter, key):
            problems.append(f"{path}: frontmatter missing or empty {key}")
    return problems


def stray_paper_content(root: Path, paper: str) -> list[Path]:
    """Every content file for `paper` anywhere under questions/ or pages/.

    The main loop only looks under the fixed intermediate/ paths; if someone
    renames a level or paper directory, those globs silently match nothing and
    the lint would pass vacuously forever. This sweep finds the paper dir at
    ANY depth so main() can refuse to green-light content it never checked.
    """
    hits: list[Path] = []
    questions_root = root / "src/data/questions"
    if questions_root.is_dir():
        for d in sorted(questions_root.rglob(paper)):
            if d.is_dir():
                hits += sorted(d.glob("*.json"))
    pages_root = root / "src/pages"
    if pages_root.is_dir():
        for d in sorted(pages_root.rglob(paper)):
            if d.is_dir():
                hits += sorted(d.rglob("*.mdx"))
                hits += [p for p in sorted(d.rglob("*.astro")) if p.stem not in NON_CONTENT_STEMS]
    return hits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Attempt-tagging lint for volatile CA Intermediate papers")
    ap.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="repo root to lint (default: two levels above this script)",
    )
    args = ap.parse_args(argv)
    root = args.root
    if not (root / "src").is_dir():
        print(f"attempt_lint: no src/ under {root}", file=sys.stderr)
        return 2

    problems: list[str] = []
    checked = 0
    for paper in VOLATILE_PAPERS:
        paper_checked = 0
        for bank in sorted((root / "src/data/questions/intermediate" / paper).glob("*.json")):
            paper_checked += 1
            problems += lint_bank(bank)
        pages_dir = root / "src/pages/intermediate" / paper
        for note in sorted(pages_dir.rglob("*.mdx")):
            paper_checked += 1
            problems += lint_mdx(note)
        for page in sorted(pages_dir.rglob("*.astro")):
            if page.stem not in NON_CONTENT_STEMS:
                paper_checked += 1
                problems.append(
                    f"{page}: volatile-paper note pages must be MDX with "
                    "applicable_attempts + law_as_on_date frontmatter (found .astro)"
                )
        checked += paper_checked

        # Vacuous-pass guard: content for this paper exists somewhere, but the
        # expected paths matched nothing — a renamed level/paper directory
        # must break the build, not silently exempt the paper from linting.
        if paper_checked == 0:
            stray = stray_paper_content(root, paper)
            if stray:
                print(
                    f"attempt_lint: {len(stray)} content file(s) exist for volatile paper "
                    f"'{paper}' (e.g. {stray[0]}) but 0 were checked — the lint's expected "
                    "paths no longer match the content layout. Fix the paths in "
                    "attempt_lint.py; this lint must never pass vacuously.",
                    file=sys.stderr,
                )
                return 1

    for p in problems:
        print(f"  FAIL {p}")
    if problems:
        print(f"\nattempt_lint: {len(problems)} violation(s) in volatile papers (P2/P3/P5).")
        print("Every law/tax question needs applicableAttempts + lawAsOnDate;")
        print("every note needs applicable_attempts + law_as_on_date frontmatter.")
        return 1
    if checked == 0:
        print("attempt_lint: 0 files checked — no volatile-paper content exists yet.")
        return 0
    print(f"attempt_lint: {checked} file(s) checked, all law/tax content attempt-tagged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

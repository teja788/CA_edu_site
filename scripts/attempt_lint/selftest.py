#!/usr/bin/env python3
"""Self-test for attempt_lint: a linter that can't catch a planted violation
must never green-light a build (same doctrine as verify_numerical/selftest).

Builds a throwaway tree with (a) an untagged tax question, (b) a tagged one,
(c) an MDX note missing law_as_on_date, (d) an MDX note with an EMPTY
law_as_on_date, (e) a fully tagged MDX note, and a stray .astro note page —
then asserts the lint fails on exactly the planted problems and passes once
they're fixed. Also plants a renamed level directory (content present, lint
paths blind to it) and asserts the vacuous-pass guard fails the build, and
asserts a genuinely empty tree passes with an explicit 0-files-checked note.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

LINT = Path(__file__).with_name("attempt_lint.py")

# Block-style list matches how the real notes are written; the lint must not
# mistake a value on the following indented lines for an empty value.
GOOD_MDX = """---
title: Supply under GST
applicable_attempts:
  - 'Sept 2026'
law_as_on_date: 2026-02-28
---
Body.
"""

BAD_MDX = """---
title: Charge of GST
applicable_attempts: ["Sept 2026"]
---
Missing law_as_on_date.
"""

EMPTY_DATE_MDX = """---
title: Input Tax Credit
applicable_attempts: ["Sept 2026"]
law_as_on_date:
---
law_as_on_date present but empty — as useless as missing.
"""


def build_tree(root: Path, planted: bool) -> None:
    bank_dir = root / "src/data/questions/intermediate/taxation"
    bank_dir.mkdir(parents=True, exist_ok=True)
    good_q = {"id": "q-ok", "type": "mcq", "applicableAttempts": ["Sept 2026"], "lawAsOnDate": "2026-02-28"}
    bad_q = {"id": "q-untagged", "type": "mcq"}
    questions = [good_q, bad_q] if planted else [good_q]
    (bank_dir / "supply-under-gst.json").write_text(json.dumps({"questions": questions}))

    notes_dir = root / "src/pages/intermediate/taxation"
    notes_dir.mkdir(parents=True, exist_ok=True)
    (notes_dir / "supply-under-gst.mdx").write_text(GOOD_MDX)
    bad_note = notes_dir / "charge-of-gst.mdx"
    empty_date_note = notes_dir / "input-tax-credit.mdx"
    stray_astro = notes_dir / "charge-of-gst.astro"
    if planted:
        bad_note.write_text(BAD_MDX)
        empty_date_note.write_text(EMPTY_DATE_MDX)
        stray_astro.write_text("---\n---\n<p>astro note</p>")
    else:
        bad_note.unlink(missing_ok=True)
        empty_date_note.unlink(missing_ok=True)
        stray_astro.unlink(missing_ok=True)
    # index/amendments pages must NOT be flagged
    (notes_dir / "index.astro").write_text("---\n---\n<p>hub</p>")
    (notes_dir / "amendments.astro").write_text("---\n---\n<p>tracker</p>")


def run(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(LINT), "--root", str(root)],
        capture_output=True,
        text=True,
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        build_tree(root, planted=True)
        res = run(root)
        assert res.returncode == 1, f"planted violations must fail (got {res.returncode}):\n{res.stdout}{res.stderr}"
        for marker in ("q-untagged", "law_as_on_date", "charge-of-gst.astro"):
            assert marker in res.stdout, f"expected '{marker}' in output:\n{res.stdout}"
        assert "input-tax-credit.mdx" in res.stdout, f"empty law_as_on_date not flagged:\n{res.stdout}"
        assert "q-ok" not in res.stdout, "tagged question wrongly flagged"
        assert "supply-under-gst.mdx" not in res.stdout, "block-style tagged note wrongly flagged"
        assert "index.astro" not in res.stdout, "hub page wrongly flagged"

        build_tree(root, planted=False)
        res = run(root)
        assert res.returncode == 0, f"clean tree must pass (got {res.returncode}):\n{res.stdout}{res.stderr}"

    # Vacuous-pass guard: rename the level dir so the lint's expected paths
    # match nothing while taxation content still exists — must fail, not pass.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        build_tree(root, planted=False)
        (root / "src/data/questions/intermediate").rename(root / "src/data/questions/inter")
        (root / "src/pages/intermediate").rename(root / "src/pages/inter")
        res = run(root)
        assert res.returncode == 1, f"renamed layout must fail, not pass vacuously (got {res.returncode}):\n{res.stdout}{res.stderr}"
        assert "vacuously" in res.stderr, f"expected vacuous-pass guard message:\n{res.stderr}"

    # Genuinely empty tree: no volatile-paper content anywhere → pass, but say so.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "src").mkdir()
        res = run(root)
        assert res.returncode == 0, f"empty tree must pass (got {res.returncode}):\n{res.stdout}{res.stderr}"
        assert "no volatile-paper content" in res.stdout, f"expected explicit 0-files note:\n{res.stdout}"

    print("attempt_lint selftest passed: planted violations caught (incl. empty tag value), "
          "clean tree passes, nav pages exempt, vacuous pass blocked, empty tree explicit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Self-test for attempt_lint: a linter that can't catch a planted violation
must never green-light a build (same doctrine as verify_numerical/selftest).

Builds a throwaway tree with (a) an untagged tax question, (b) a tagged one,
(c) an MDX note missing law_as_on_date, (d) a fully tagged MDX note, and a
stray .astro note page — then asserts the lint fails on exactly the planted
problems and passes once they're fixed.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

LINT = Path(__file__).with_name("attempt_lint.py")

GOOD_MDX = """---
title: Supply under GST
applicable_attempts: ["Sept 2026"]
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
    stray_astro = notes_dir / "charge-of-gst.astro"
    if planted:
        bad_note.write_text(BAD_MDX)
        stray_astro.write_text("---\n---\n<p>astro note</p>")
    else:
        bad_note.unlink(missing_ok=True)
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
        assert "q-ok" not in res.stdout, "tagged question wrongly flagged"
        assert "index.astro" not in res.stdout, "hub page wrongly flagged"

        build_tree(root, planted=False)
        res = run(root)
        assert res.returncode == 0, f"clean tree must pass (got {res.returncode}):\n{res.stdout}{res.stderr}"

    print("attempt_lint selftest passed: planted violations caught, clean tree passes, nav pages exempt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

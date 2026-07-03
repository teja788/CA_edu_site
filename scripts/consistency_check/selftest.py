#!/usr/bin/env python3
"""Self-test for the consistency checker: strips the depreciation fixture,
simulates a fresh pass that disagrees on the planted-error question, and
asserts the diff quarantines exactly that question and exits non-zero.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "consistency_check.py"
FIXTURE_BANK = HERE.parent / "verify_numerical" / "fixtures" / "depreciation-demo.json"


def run(*argv):
    return subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, text=True)


def main() -> int:
    problems = []
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        blind_path, queue_path, answered_path = td / "blind.json", td / "queue.md", td / "answered.json"

        r = run("strip", str(FIXTURE_BANK), "-o", str(blind_path))
        blind = json.loads(blind_path.read_text())
        if r.returncode != 0:
            problems.append(f"strip failed: {r.stderr}")
        if any("correct" in q or any("explanation" in o for o in q["options"]) for q in blind["questions"]):
            problems.append("strip leaked the key or explanations into the blind file")
        blind_ids = {q["id"] for q in blind["questions"]}
        if not {"q-dep-004-a", "q-dep-004-b"} <= blind_ids:
            problems.append("strip did not flatten case_mcq_set sub-questions into the blind file")
        if not any(q.get("case") for q in blind["questions"] if q["id"] == "q-dep-004-a"):
            problems.append("case sub-question is missing its case paragraph — unanswerable blind")

        # Simulated fresh pass: computes D on the planted-error question
        # (key wrongly says B) and A on the planted case-set error, agrees
        # with the key elsewhere.
        fresh = {"answers": {"q-dep-001": "D", "q-dep-002": "B", "q-dep-003": "A",
                             "q-dep-004-a": "A", "q-dep-004-b": "A"}}
        answered_path.write_text(json.dumps(fresh))

        r = run("diff", str(FIXTURE_BANK), str(answered_path), "--queue", str(queue_path))
        if r.returncode != 1:
            problems.append(f"diff should exit 1 on a mismatch, got {r.returncode}: {r.stdout}{r.stderr}")
        queue = queue_path.read_text() if queue_path.exists() else ""
        if "q-dep-001" not in queue:
            problems.append("mismatch q-dep-001 was not written to the review queue")
        if "q-dep-002" in queue:
            problems.append("agreed question q-dep-002 wrongly quarantined")

        if "q-dep-004-a" not in queue:
            problems.append("case-set mismatch q-dep-004-a was not quarantined")

        # All-agree pass must exit 0; unanswered question must exit 2.
        fresh_ok = {"answers": {"q-dep-001": "B", "q-dep-002": "B", "q-dep-003": "A",
                                "q-dep-004-a": "B", "q-dep-004-b": "A"}}
        answered_path.write_text(json.dumps(fresh_ok))
        if run("diff", str(FIXTURE_BANK), str(answered_path), "--queue", str(queue_path)).returncode != 0:
            problems.append("diff should exit 0 when every answer agrees")
        answered_path.write_text(json.dumps({"answers": {"q-dep-001": "B"}}))
        if run("diff", str(FIXTURE_BANK), str(answered_path), "--queue", str(queue_path)).returncode != 2:
            problems.append("diff should exit 2 on unanswered questions")

    if problems:
        print("SELFTEST FAILED:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("consistency_check selftest passed: strip is blind, mismatch quarantined, exit codes correct.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

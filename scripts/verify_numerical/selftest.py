#!/usr/bin/env python3
"""Self-test for the numerical runner, built around the plan's planted-error
exemplar: a question whose fluent prose defends the wrong key. Passing this
test proves the pipeline trusts the verify script over the prose.

Runs in CI on every PR. Exits non-zero if the runner misses anything.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from run import check_bank  # noqa: E402

FIXTURES = HERE / "fixtures"


def main() -> int:
    failures, checked = check_bank(FIXTURES / "depreciation-demo.json", FIXTURES)
    failed_ids = {qid for _, qid, _ in failures}

    problems = []
    if "q-dep-001" not in failed_ids:
        problems.append(
            "runner did NOT catch the planted wrong key on q-dep-001 "
            "(prose says B, computation says D) — the whole point of the toolkit"
        )
    if "q-dep-003" not in failed_ids:
        problems.append("runner did NOT flag q-dep-003, which has no verifier function")
    if "q-dep-002" in failed_ids:
        problems.append("runner wrongly failed q-dep-002, whose key is correct")
    if "q-dep-004-a" not in failed_ids:
        problems.append(
            "runner did NOT catch the planted wrong key on case-set sub-question "
            "q-dep-004-a — case_mcq_set entries must be flattened and verified"
        )
    if len(failures) != 3:
        problems.append(f"expected exactly 3 failures, got {len(failures)}: {failures}")

    if problems:
        print("SELFTEST FAILED:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("verify_numerical selftest passed: planted error caught, coverage gap caught, correct key passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

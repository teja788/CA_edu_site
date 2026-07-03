#!/usr/bin/env python3
"""Numerical-question verifier (plan §6.4: quality is a process, not an intention).

Every chapter bank in src/data/questions/ that contains questions flagged
`"numerical": true` must ship a sibling verify module:

    scripts/verify_numerical/verify_<chapterSlug>.py

The module exposes one function per numerical question, named after the
question id with dashes mapped to underscores (q-tvm-001 -> q_tvm_001).
Each function COMPUTES the answer from the stem's parameters — never
hard-codes the key — and returns either:

    "B"                                   # just the option key, or
    {"answer": "B", "computed": 90000}    # key + the computed value (preferred:
                                          # the runner prints it for reviewers)

Exit status is non-zero on ANY mismatch, missing module, missing function,
or verifier exception, so CI blocks the merge. A bank with no numerical
questions needs no module.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_BANKS_DIR = REPO / "src" / "data" / "questions"
DEFAULT_MODULES_DIR = Path(__file__).resolve().parent


def load_module(modules_dir: Path, slug: str):
    path = modules_dir / f"verify_{slug}.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location(f"verify_{slug}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_bank(bank_path: Path, modules_dir: Path):
    """Returns (failures, n_checked). Each failure is (slug, qid, message)."""
    failures = []
    checked = 0
    try:
        data = json.loads(bank_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return [(bank_path.name, "(file)", f"unparseable JSON: {e}")], 0

    slug = data.get("chapterSlug") or bank_path.stem
    # case_mcq_set entries hold linked MCQs in `questions`; each sub-question
    # carries its own `numerical` flag and verifier function like any MCQ.
    flat = []
    for q in data.get("questions", []):
        if q.get("type") == "case_mcq_set":
            flat.extend(q.get("questions", []))
        else:
            flat.append(q)
    numerical = [q for q in flat if q.get("numerical")]
    if not numerical:
        return [], 0

    mod = load_module(modules_dir, slug)
    if mod is None:
        return [
            (
                slug,
                "(module)",
                f"bank has {len(numerical)} numerical question(s) but "
                f"scripts/verify_numerical/verify_{slug}.py does not exist",
            )
        ], 0

    for q in numerical:
        qid = q.get("id", "(no id)")
        fn = getattr(mod, qid.replace("-", "_"), None)
        if fn is None:
            failures.append((slug, qid, f"no verifier function {qid.replace('-', '_')}()"))
            continue
        try:
            result = fn()
        except Exception as e:  # noqa: BLE001 — any verifier crash is a failure
            failures.append((slug, qid, f"verifier raised {e!r}"))
            continue
        if isinstance(result, dict):
            answer, computed = result.get("answer"), result.get("computed")
        else:
            answer, computed = result, None
        checked += 1
        detail = f" (computed value: {computed})" if computed is not None else ""
        if answer != q.get("correct"):
            failures.append(
                (slug, qid, f"answer key says {q.get('correct')!r} but the verifier computed {answer!r}{detail}")
            )
        else:
            print(f"  ok   {qid}: {answer}{detail}")
    return failures, checked


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bank", type=Path, help="check a single bank JSON instead of the whole tree")
    ap.add_argument("--banks-dir", type=Path, default=DEFAULT_BANKS_DIR)
    ap.add_argument("--modules-dir", type=Path, default=DEFAULT_MODULES_DIR)
    args = ap.parse_args(argv)

    banks = [args.bank] if args.bank else sorted(args.banks_dir.rglob("*.json"))
    if not banks:
        print(f"No question banks under {args.banks_dir} yet — nothing to verify.")
        return 0

    all_failures = []
    total_checked = 0
    for bank in banks:
        print(f"bank: {bank}")
        failures, checked = check_bank(bank, args.modules_dir)
        all_failures.extend(failures)
        total_checked += checked

    print(f"\n{total_checked} numerical question(s) verified, {len(all_failures)} failure(s).")
    if all_failures:
        print("\nFAILURES — fix the question or the verifier; never edit the key to match prose:")
        for slug, qid, msg in all_failures:
            print(f"  FAIL {slug} / {qid}: {msg}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

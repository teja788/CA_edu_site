#!/usr/bin/env python3
"""Independent-pass consistency check for MCQ banks (plan §6.4).

An LLM (or human) that just wrote a question knows its own intended answer;
re-answering the same questions FRESH, with the key and all explanations
stripped, catches ambiguous stems and wrong keys that fluent explanations
hide. Protocol per chapter session:

  1. strip:  python3 scripts/consistency_check/consistency_check.py strip \
                 src/data/questions/<level>/<paper>/<chapter>.json -o blind.json
  2. Answer blind.json in a FRESH reasoning pass with no access to the bank —
     a separate subagent/session that is given only blind.json. It fills
     "answer" on every question (or returns {"answers": {"q-id": "B", ...}}).
  3. diff:   python3 scripts/consistency_check/consistency_check.py diff \
                 <bank.json> <answered.json> --queue review_queue.md

`diff` exits non-zero on any mismatch or unanswered question and appends
mismatches to review_queue.md with BOTH answers shown. Mismatched questions
are quarantined there — never merged into the live bank until resolved.
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from datetime import date
from pathlib import Path

BLIND_INSTRUCTIONS = (
    "Answer every MCQ from first principles. You have no access to the answer "
    "key or explanations — that is the point. For each question return your "
    "option key in the 'answer' field, plus 'confidence': 'high'|'medium'|'low'. "
    "If a stem is ambiguous or has no single defensible answer, set answer to "
    "'AMBIGUOUS' and say why in a 'note' field."
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def flatten_mcqs(bank: dict):
    """Yield (mcq, case_text) for every MCQ, entering case_mcq_set entries.

    Case sub-questions are unanswerable without their case paragraph, so the
    blind copy must carry it; standalone MCQs get case_text=None.
    """
    for q in bank.get("questions", []):
        if q.get("type") == "case_mcq_set":
            for sub in q.get("questions", []):
                yield sub, q.get("case")
        elif q.get("type", "mcq") == "mcq":
            yield q, None


def cmd_strip(args) -> int:
    bank = load(args.bank)
    blind = {
        "chapterSlug": bank.get("chapterSlug", args.bank.stem),
        "instructions": BLIND_INSTRUCTIONS,
        "questions": [
            {
                "id": q["id"],
                **({"case": case} if case else {}),
                "stem": q["stem"],
                "options": [{"key": o["key"], "text": o["text"]} for o in q["options"]],
                "answer": None,
            }
            for q, case in flatten_mcqs(bank)
        ],
    }
    out = json.dumps(blind, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(out + "\n", encoding="utf-8")
        print(f"{len(blind['questions'])} question(s) stripped -> {args.output}")
    else:
        print(out)
    return 0


def extract_answers(answered: dict) -> dict:
    if "answers" in answered:
        return {qid: {"answer": a} if isinstance(a, str) else a for qid, a in answered["answers"].items()}
    return {
        q["id"]: {"answer": q.get("answer"), "confidence": q.get("confidence"), "note": q.get("note")}
        for q in answered.get("questions", [])
    }


def cmd_diff(args) -> int:
    bank = load(args.bank)
    answers = extract_answers(load(args.answered))
    slug = bank.get("chapterSlug", args.bank.stem)

    mismatches, unanswered, agreed = [], [], 0
    for q, _case in flatten_mcqs(bank):
        got = answers.get(q["id"], {})
        fresh = got.get("answer")
        if not fresh:
            unanswered.append(q["id"])
        elif fresh != q.get("correct"):
            mismatches.append((q, fresh, got))
        else:
            agreed += 1

    print(f"{slug}: {agreed} agreed, {len(mismatches)} mismatch(es), {len(unanswered)} unanswered.")

    if mismatches and args.queue:
        lines = [f"\n## {slug} — consistency check {date.today().isoformat()}\n"]
        for q, fresh, got in mismatches:
            stem = textwrap.shorten(q["stem"], 160, placeholder="…")
            lines.append(f"- [ ] **{q['id']}** — key: **{q.get('correct')}**, fresh pass: **{fresh}**"
                         + (f" (confidence: {got.get('confidence')})" if got.get("confidence") else ""))
            lines.append(f"  - Stem: {stem}")
            if got.get("note"):
                lines.append(f"  - Fresh-pass note: {got['note']}")
            lines.append("  - Resolution: fix the key, fix the stem, or delete — then rerun both passes.")
        with args.queue.open("a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"Mismatches quarantined in {args.queue} — do NOT merge them into the live bank.")

    for qid in unanswered:
        print(f"  unanswered: {qid}")
    for q, fresh, _ in mismatches:
        print(f"  MISMATCH {q['id']}: key={q.get('correct')} fresh={fresh}")

    if unanswered and not args.allow_missing:
        return 2
    return 1 if mismatches else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Independent-pass consistency check for MCQ banks")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("strip", help="emit an answer-free copy of a bank for a fresh reasoning pass")
    s.add_argument("bank", type=Path)
    s.add_argument("-o", "--output", type=Path)
    s.set_defaults(fn=cmd_strip)

    d = sub.add_parser("diff", help="compare fresh answers to the key; quarantine mismatches")
    d.add_argument("bank", type=Path)
    d.add_argument("answered", type=Path)
    d.add_argument("--queue", type=Path, default=Path("review_queue.md"))
    d.add_argument("--allow-missing", action="store_true", help="don't fail on unanswered questions")
    d.set_defaults(fn=cmd_diff)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

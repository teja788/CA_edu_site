# consistency_check

Independent-pass verification for MCQs that a program can't compute (law,
theory, classification). The author of a question always "knows" its intended
answer; a fresh pass answering the same stem blind — no key, no explanations —
catches wrong keys and ambiguous stems.

## Protocol (run inside every chapter session)

```sh
# 1. Strip the bank to a blind file
python3 scripts/consistency_check/consistency_check.py strip \
    src/data/questions/foundation/business-laws/indian-contract-act.json -o blind.json

# 2. Fresh pass: hand blind.json to a SEPARATE session/subagent that has never
#    seen the bank. It fills "answer" (+ optional "confidence"/"note") per
#    question, or returns {"answers": {"q-id": "B", ...}}. Marking a stem
#    "AMBIGUOUS" is a valid — and valuable — answer.

# 3. Diff against the key; mismatches are quarantined, not merged
python3 scripts/consistency_check/consistency_check.py diff \
    src/data/questions/foundation/business-laws/indian-contract-act.json \
    answered.json --queue review_queue.md
```

Exit codes: `0` all agree · `1` mismatches (written to `review_queue.md` with
both answers) · `2` unanswered questions. The fresh pass disagreeing does not
mean the fresh pass is right — it means a human decides, from the primary
source, in `review_queue.md`.

`selftest.py` (run in CI) proves: strip leaks nothing, mismatches are
quarantined, exit codes hold.

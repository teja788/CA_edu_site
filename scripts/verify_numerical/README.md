# verify_numerical

Programmatic answer verification for every numerical question. The founding
rule: **the verify script outranks the prose.** A fluent explanation defending
a wrong key is exactly the failure mode this exists to catch — the self-test
fixture (`fixtures/depreciation-demo.json`) contains the plan's planted-error
exemplar, and CI proves the runner catches it on every PR.

## Convention

- Chapter bank: `src/data/questions/<level>/<paper-slug>/<chapter-slug>.json`
  with `"numerical": true` on every machine-computable question.
- Verify module: `scripts/verify_numerical/verify_<chapter-slug>.py`, one
  function per numerical question id (`q-tvm-001` → `def q_tvm_001():`).
- Each function recomputes the answer **from the stem's parameters** (never
  hard-codes the key), maps the computed value to an option, and returns
  `{"answer": "B", "computed": 90000}` (the runner prints computed values for
  reviewers) or just `"B"`.

## Running

```sh
python3 scripts/verify_numerical/run.py                 # whole tree
python3 scripts/verify_numerical/run.py --bank <file>   # one chapter
python3 scripts/verify_numerical/selftest.py            # toolkit self-test
```

Exit is non-zero on any key mismatch, missing module/function, or verifier
exception. `.github/workflows/verify-content.yml` runs both on every PR —
with branch protection, an unverified numerical question cannot merge.

When the runner fails: recompute by hand, then fix the question or the
verifier. Never edit the key to match the explanation's prose.

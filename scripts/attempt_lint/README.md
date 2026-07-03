# attempt_lint

CI gate for the plan's day-one rule (§6.2): **tax/law content without
attempt-tagging is a liability and must not merge.**

Scope — the volatile Intermediate papers:

| Paper | Slug | Why volatile |
|---|---|---|
| P2 Corporate & Other Laws | `corporate-and-other-laws` | Companies Act amendments per attempt |
| P3 Taxation | `taxation` | Finance Act churn every attempt; Income-tax Act 2025 from May 2027 exams |
| P5 Auditing & Ethics | `auditing-and-ethics` | SA revisions, Companies Act audit chapters |

What must be tagged:

- **Question banks** (`src/data/questions/intermediate/<paper>/*.json`):
  every entry needs a non-empty `applicableAttempts` list and a `lawAsOnDate`.
  `case_mcq_set` entries carry the tags on the set (sub-questions inherit).
- **Notes** (`src/pages/intermediate/<paper>/**/*.mdx`): frontmatter needs
  `applicable_attempts` and `law_as_on_date`. Notes for volatile papers must
  be MDX — a `.astro` note page is itself a violation because its frontmatter
  can't be linted (`index`/`amendments`/`weightage` pages are exempt).

Attempt records (which Finance Act, cut-off dates, what still needs human
verification) live in `src/data/intermediate.js` → `attempts`.

Run locally:

```
python3 scripts/attempt_lint/attempt_lint.py   # lints the repo
python3 scripts/attempt_lint/selftest.py       # proves the lint catches planted violations
```

Both run in CI (`.github/workflows/verify-content.yml`); the selftest runs
first so a broken lint can never green-light untagged content.

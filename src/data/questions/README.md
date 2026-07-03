# Question banks

One JSON file per chapter: `src/data/questions/<level>/<paper-slug>/<chapter-slug>.json`.

(The 12 launch MCQs in `src/data/site.js` predate this convention and stay there
until the Advanced Accounting bank is regenerated through the chapter loop; all
new banks land here.)

## Bank file shape

```json
{
  "level": "foundation",
  "paper": "Paper 3 — Quantitative Aptitude",
  "chapterSlug": "time-value-of-money",
  "chapter": "Ch 4 — Time Value of Money",
  "questions": [ ... ]
}
```

`chapterSlug` must match the filename (minus `.json`) — the verification runner
uses it to find `scripts/verify_numerical/verify_<chapterSlug>.py`.

## Question shape

Same schema as the engine already consumes (see `src/data/site.js`), plus the
`numerical` flag:

```json
{
  "id": "q-tvm-001",
  "topic": "Ch 4 · Time Value of Money · Compound interest",
  "type": "mcq",
  "numerical": true,
  "stem": "…",
  "options": [
    { "key": "A", "text": "…", "explanation": "why this wrong option is tempting — name the exact slip" },
    { "key": "B", "text": "…", "explanation": "why correct, with the working" }
  ],
  "correct": "B",
  "readLink": { "label": "Read: … →", "href": "/…/#s2" },
  "difficulty": "easy | medium | hard",
  "source": "original",
  "sourceRef": "Act section / AS para / formula name",
  "applicableAttempts": ["Jan 2027"],
  "lawAsOnDate": "2026-04-01",
  "lastVerified": "2026-07-03"
}
```

Rules enforced by tooling and review:

- **`numerical: true`** on every question whose answer a program can compute
  (arithmetic, accounting, statistics, FM, tax computation). CI fails if a bank
  contains a numerical question with no matching verifier function — see
  `scripts/verify_numerical/README.md`.
- **Every option carries an explanation.** Wrong options name the exact
  misconception or calculation slip they represent.
- **`sourceRef`** is mandatory: the Act section, AS/SA paragraph, or formula the
  answer is checkable against. Law questions must be checkable against the bare
  Act; quote the section number in the explanation.
- **`applicableAttempts`** always; **`lawAsOnDate`** additionally for tax/law.
- Never reproduce ICAI question wording — fresh scenarios only.

## Descriptive questions

Descriptive items use `"type": "descriptive"` with a `skeleton` array instead of
`options`/`correct`: each entry is `{ "point": "…", "marks": 1, "citation": "…" }`.
They are ignored by the numerical runner and the consistency check.

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
  "paperSlug": "quantitative-aptitude",
  "chapterSlug": "time-value-of-money",
  "chapter": "Ch 4 — Time Value of Money",
  "questions": [ ... ]
}
```

`chapterSlug` must match the filename (minus `.json`) — the verification runner
uses it to find `scripts/verify_numerical/verify_<chapterSlug>.py`.

`paperSlug` is the canonical route slug for the paper (the `<paper-slug>`
directory this file lives in, e.g. `advanced-accounting`). Practice pages build
links from it directly — never by slugifying the display `paper` string, which
mangles names like "Corporate & Other Laws".

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

Optional fields consumed by `/practice/descriptive/` and the mock composer:
`"marks"` (total; defaults to the skeleton sum) and `"workingNotes": true` when
the rubric expects working notes. `citation` strings are shown in the
self-grading rubric — cite the Act section / AS/SA paragraph the point rests on.

## Case-scenario MCQ sets (Intermediate pattern)

The Inter 30% MCQ section is case-based: a 150–250 word case paragraph with 4–5
linked MCQs, rendered and scored as a unit. Bank shape:

```json
{
  "id": "cs-p2c4-001",
  "type": "case_mcq_set",
  "topic": "Ch 4 · Share Capital · Rights issue case",
  "case": "150–250 word scenario…",
  "applicableAttempts": ["Sept 2026"],
  "lawAsOnDate": "2026-02-28",
  "questions": [
    { "id": "cs-p2c4-001-a", "stem": "…", "options": [ … ], "correct": "B", "numerical": false, "sourceRef": "s.62(1)(a)" }
  ]
}
```

Sub-questions use the normal MCQ shape (every option explained, `sourceRef`
mandatory); `applicableAttempts`/`lawAsOnDate` sit on the SET and are inherited.
The quiz engine keeps the set together (mixed mode shuffles whole sets), shows
the case above each linked question, and reports the set's score as a unit.
`verify_numerical` verifiers treat each sub-question ID like any other MCQ.

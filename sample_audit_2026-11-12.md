# Sample audit — 12 Nov 2026

Independent re-solve of 48 randomly sampled Foundation MCQs (12 per paper,
seed 42) by two Claude Opus agents. Each agent solved every question from
scratch before looking at the marked key; law questions were checked against
statute text where sections/thresholds were cited.

## Result

| Verdict | Count |
|---|---|
| OK | 43 |
| WRONG_KEY | **0** |
| AMBIGUOUS / OUTDATED / UNSURE | 0 |
| EXPLANATION_ERROR (key right, option explanation wrong) | 5 |

**48/48 answer keys correct.** Point estimate for wrong keys in the full bank:
0% (n=48; a true error rate up to ~6% can't be ruled out at 95% confidence).

## Items to fix (explanation text only) — all fixed 12 Nov 2026

- [x] `q-f3c10-039` (QA Ch 10, directions) — option B's explanation said an
  afternoon shadow points West; it points East. Rewritten.
- [x] `q-f3c14-046` (QA Ch 14, CV) — options A and C explanations were
  garbled/muddled. Rewritten (A = variance÷mean read as %, C = SD read as %).
- [x] `q-f3c1-015` (QA Ch 1, proportion) — option B's explanation called 5 and
  15 "the extremes"; in 5:10::15:d the extremes are 5 and d. Rewritten.
- [x] `q-f4c3-041` (Econ Ch 3) — options A and C assumed TFC = ₹100, which the
  stem never gave. TFC = ₹100 added to the stem.
- [x] `q-f4c5-050` (Econ Ch 5) — exam-strategy item misfiled under Business
  Cycles with a wrong expected-value claim (blind 4-option guess at +1/−0.25
  already averages +0.0625). **Deleted** (bank now 49 questions).
- [x] `q-f4c5-048` (Econ Ch 5) — absurd distractors (logo, wall colour)
  replaced with plausible ones (only-long-term, only-financing).
- [x] Bonus: business-cycles notes §10 said eliminating one option makes a
  guess worth "about 0.5 marks per four attempts"; true value is 0.67. Fixed.

Full per-question working: agents' reports in session scratchpad
(`audit_comp_report.md`, `audit_conc_report.md`); regenerate the sample with
seed 42 if needed.

# Momentum improvement research — literature + practice survey (Jul 2026)

Compiled from a three-agent web survey (academic literature; India/NSE practice;
practitioner portfolio construction), for improving `m2` = 12-1 momentum
top-25, monthly, dynamic top-1000 NSE universe (net +296%, Sharpe 1.22,
DD −33% over Jul 2021–Jul 2026). Full agent reports summarized; citations
inline. Own-data priors this must reconcile with: per-position ATR stops
failed 4/4 times; per-stock SMA gate redundant 5/5 times; market-level regime
gate (v7) was the one overlay that helped; dynamic universe's failure mode is
buying freshly-hyped names near peaks.

## Convergent findings (multiple independent sources agree)

1. **Vol-adjusted momentum score, 6m+12m blend** — NSE's own momentum indices
   (Nifty200 Momentum 30 / Midcap150 Momentum 50 / Nifty500 Momentum 50) all
   rank by `return / σ(daily log returns, 1y)`, z-scored, 50/50 blend of 6m and
   12m, normalized `1+Z` (or `1/(1−Z)` if Z<0). Verified from the NSE
   methodology PDF (nsearchives.nseindia.com Method_NIFTY_Equity_Indices.pdf,
   Jun 2026). MSCI Momentum does the same. Academic support: Liu (JEDC 2022)
   GRJMOM; caveat from Newfound (2019): mom/vol is ~0.93-correlated with plain
   momentum — expect de-ranking of parabolic junk, not a new factor.
2. **Portfolio-level vol targeting (gradual de-risking)** — Barroso &
   Santa-Clara (JFE 2015): scale exposure by `σ_target/σ̂`, σ̂ = realized vol of
   the *strategy's own* daily returns over 126 trading days, σ_target ≈ 12%
   annualized; US long-short Sharpe 0.53→0.97, maxDD −97%→−45%, turnover
   unchanged. Harvey et al. (JPM 2018): tail benefits confirmed across 60
   assets; works long-only via cash overlay (de-lever only, cap weight at 1).
   **India-validated**: Singh et al., FIIB Business Review 2022 (450 BSE
   stocks) — "doubles adjusted Sharpe". Daniel & Moskowitz (JFE 2016) add the
   panic-state throttle: crashes cluster when (24m market return < 0) AND
   market vol high.
3. **Turnover: buy/hold hysteresis + tranching** — Novy-Marx & Velikov (RFS
   2016): buy into top-S%, hold until it leaves a wider band — their single
   most effective cost mitigation (~turnover/3 at minimal alpha cost). NSE
   uses 1.5x rank buffers in production (30-name index holds until rank 45).
   Hoffstein/Faber/Braun (SSRN 3673910): rebalance-timing luck >100bp/yr for
   high-turnover factor portfolios; fix = split the book into 2-4 staggered
   weekly tranches (RTL falls ~1/N). Our 25-in/35-out buffer is at the narrow
   end; test 25/50-60.
4. **Regime gate: gradual + asymmetric beats binary** — Newfound "What the
   Trend": one binary 200SMA gate carries huge specification/timing luck (600bp
   from a one-day shift in 2020); use 3-5 signals (100/150/200d SMA, 6m/12m
   TSMOM) and set exposure = fraction on. Clenow: gate blocks NEW buys but
   doesn't force-liquidate — kills whipsaw round-trips. Consistent with our
   v7 result (binary gate helped DD/Sharpe, cost return in V-recoveries).
5. **Everyone credible in India adds risk controls** — no practitioner runs
   naked top-N momentum: NSE adds vol-adjustment + buffers + circuit screens;
   Capitalmind adds min-1-month hold + cash raising (still discontinued its
   momentum smallcase after 2024-25); Samco hedges with derivatives (still ~9%
   CAGR over 3y); Wright offers a hedged variant. The 2024-25 factor drawdown
   was −31.8% on the N200M30 index itself (Wright Research) — our backtest's
   2025 bleed is the factor, not a bug. Historical N200M30 drawdown norm:
   −23 to −34% with recovery ≈ 2.3× fall duration.

## Signal upgrades with strong evidence

- **Residual momentum** (Blitz-Huij-Martens 2011; Blitz-Hanauer-Vidojevic
  2020; Hanauer & Windmüller JBF 2023): momentum on market-model residuals
  over t−12..t−2, standardized by residual σ. In the 48-country sample it
  beats vol-scaling approaches (Sharpe uplift >2x) with the largest DD
  reduction, **validated in emerging markets** — strongest India-relevant
  signal upgrade. Stacks with portfolio vol targeting (residualize the signal,
  vol-manage the book).
- **Frog-in-the-pan / information discreteness** (Da-Gurun-Warachka RFS 2014):
  ID = sgn(PRET) × (%neg − %pos daily returns over the formation window); buy
  smooth (low-ID) winners. US: momentum profit −2.07% (discrete) → +5.94%
  (continuous) over 6m holds. Price-only; ideal secondary screen: rank top-75
  by momentum, keep the 25 smoothest. US-large-cap evidence; validate locally.
- **Moving Average Distance** (Avramov et al., SSRN 3111334): MAD = MA(21)/
  MA(200), ~9%/yr value-weighted alpha, survives costs, strongest long-side;
  international confirmation. Candidate auxiliary rank, price-only.
- **52-week-high proximity** (George & Hanna 2004): independent of 12-1;
  useful second signal, but costs eat much of it in many markets.

## India-specific screens (pure price/volume, copy from NSE practice)

- **Circuit-hit screen**: exclude names hitting upper/lower circuit ≥20% of
  days in trailing 6m (NSE uses this in the midcap/smallcap/500 momentum
  indices — locked lower circuit = can't exit a loser).
- **ASM/GSM/T2T risk**: high-momentum smallcaps enter surveillance lists,
  margins/bands tighten, intraday exit impossible in T2T. Another reason
  per-position stops fail here.
- **Speculative-churn filter** (BacktestIndia, blog-grade): monthly share
  turnover (value/mcap) 5-10% preferred, exclude 30-60% churners: +4pp CAGR,
  −9pp maxDD over 18.5y survivorship-corrected. Needs mcap (shares
  outstanding) — partial: can proxy with raw traded-value vs price level? Park
  unless shares-outstanding data added.
- **Cost stack**: ~25-30bp round trip ex-brokerage (STT 0.1% both sides
  dominates); DP charge fixed per scrip-day. Monthly one-shot rebalance has no
  T+1 settlement drag.

## What NOT to do (evidence + our own four stop failures)

- Per-position trailing stops (Daniel-Moskowitz: crashes are portfolio-level
  beta events; stock-level daily mean reversion fights stops; ASM/T2T frictions
  compound it). Confirmed 4/4 in our data.
- 12-7 "echo" window (Goyal & Wahal 2015: not robust in 36/37 non-US markets).
  Keep 12-1/12-2.
- Weekly rebalance (smallcase India backtest: 16.6% CAGR weekly vs 23.0%
  monthly, costs+whipsaw). Monthly is the India sweet spot; NSE's semi-annual
  is a capacity choice, not signal-optimal.
- Rank-weighting inside the selected top-N (ReSolve: no value post-selection).
- Portfolio-DD-triggered de-risking (slow proxy for vol/trend; sells bottoms).

## Long-run India context

IIM-A factor library (Agarwalla-Jacob-Varma): WML premium 21.9%/yr (1994-2014,
survivorship-corrected) — largest factor premium in India. Official index
spreads: N200M30 +4-6pp/yr over parent since 2005; Midcap150 Momentum 50
+5.6pp/yr — midcap momentum premium is the fattest. Both indices LAGGED their
parents over the year to Jun-2026; QTD 2026 momentum re-asserting.

## Proposed test waves (for discussion)

Wave 1 — config-only or near-config changes on dyn-1000 m2:
  a. NSE-style score: two signals (6m, 12m vol-adjusted momentum), 50/50
     weighted z (needs one custom signal: return_over_window / realized vol).
  b. Exit-buffer widening: exit_rank 50 and 60 (vs 35).
  c. v7-style regime gate on dyn-1000 (binary first; it's one config line).
  d. Circuit-proxy screen: drop names with ≥20% of days at ±band moves
     (approximate bands from daily |return| clusters since band data isn't in
     Kite; or skip if too approximate).
Wave 2 — engine additions:
  e. Vol-target overlay: exposure = min(1, 12%/σ̂_126d strategy vol), monthly.
  f. Fractional multi-signal regime exposure (3 index signals → 0/⅓/⅔/1).
  g. Asymmetric gate (block buys, don't force sells).
Wave 3 — new signals:
  h. FIP ID screen (top-75 mom → 25 smoothest).
  i. Residual momentum (market-model residuals, needs rolling regression
     signal).
  j. MAD auxiliary rank.

---

# Addendum (2026-07-12): gap-fill survey + own-data synthesis

Second two-agent pass covering gaps the first survey left open (seasonality,
concentration, weighting, dual momentum, crash prediction, 2024-26
literature; India post-crash practitioner changes, sector caps, quality
blends, rebalance staggering, universe construction, mid-2026 state of play).
Grounding facts from our own runs: m2 dyn-1000 yearly net = 2021 +47.3%,
2022 −8.6%, 2023 +72.0%, 2024 +56.7%, 2025 −10.0%, 2026 +14.4%; maxDD −32.9%
troughed Feb-2023 (the 2022-23 grind, NOT the 2024-25 factor crash); win rate
64%; top-25 trades = 51% of P&L; charges 10.0% of gross. v7 binary regime
gate remains the only overlay to raise Sharpe (1.57→1.67); v8 inverse-vol
diluted (346% vs 390%), consistent with MSCI's finding that inv-vol inside a
momentum book is a low-vol tilt fighting the signal.

## Strongest new findings

1. **Turnover-chasing is directly, hugely costly in India** (BacktestIndia,
   Mar 2026; NSE top-200, 2006-2025): top-30 momentum split by scaled
   turnover (traded value / mcap) — LOW-churn winners 19.4% net CAGR vs
   HIGH-churn 8.5% (below Nifty), base 14.6%. Largest single effect found
   anywhere in this research, and our dynamic top-1000-by-traded-value
   construction tilts toward the losing bucket (liquidity ranking = hype
   ranking). Practitioner fix (Capitalmind): universe = mcap rank with a
   traded-value FLOOR, never traded-value ranking. NSE indices additionally
   impose ~12m listing age (12m signal + parent-index membership) and F&O
   eligibility.
2. **Graded trend states beat the binary gate** (Goulding-Harvey-Mazzoleni,
   JFE 2023 + FAJ 2024 "Breaking Bad Trends"): classify market by agreement
   of slow (12m) and fast (1m) trend → Bull/Correction/Rebound/Bear; scale
   exposure by state instead of on/off. Higher Sharpe, shallower DD, positive
   skew vs static trend. This is the published upgrade of our v7 result
   (binary gate helped DD, cost return in V-recoveries). Also: cross-
   sectional momentum + time-varying market beta replicates TSM — the
   theoretically right overlay for our book is a scaled beta dial.
3. **Persistence-aware selection cuts turnover and adds net return**
   (Calluzzo-Moneta-Topaloglu, SSRN 5199701, 2025): the skip-month contains
   information about which stocks will REMAIN momentum stocks; filtered
   (drop predicted exits) and blended (current + anticipated score) variants
   add up to +5pp net p.a. in US long-only at matched horizons. Price-only;
   a smarter version of the Novy-Marx hysteresis band. Our charges are 10%
   of gross — turnover reduction is worth real bp here.
4. **Ex-ante crash dials that beat Daniel-Moskowitz**: momentum gap (Huang,
   RFS 2022 — formation-period winner-loser spread negatively predicts
   momentum profits, 20/21 non-US markets); cross-sectional return IQR (Liu
   et al. 2025 — forecasts crashes OOS across 52 markets, dispersion-guided
   rotation ~doubles Sharpe); beta+momentum-vol regime split (Dierkes-
   Krupski, JEF 2022 — Sharpe 1.12 vs 0.94 Barroso-SC). Both gap and IQR are
   one-liners on ranking data we already compute.
5. **Rebalance timing matters, monthly cadence is settled**: Raju "Timing
   the Tide" (India grid: universe × N × weighting × 1/2/3/6m) — shortest
   rebalance captures the premium best, weighting second-order; Wright:
   monthly 23.0% vs weekly 16.6% CAGR, AND mid-month rebalance (day 6-20)
   Sharpe >0.9 vs 0.84 on the 1st (month-turn crowding); Quantpedia: ~350bp
   CAGR dispersion across monthly rebalance dates. India month-of-year:
   April is the momentum-hostile month (fiscal-year-end loser rebound,
   strongest in mid/small caps — our universe).
6. **Concentration and N: we're already at the optimum.** Raju (SSRN
   4453680): concentration buys factor exposure but not risk-adjusted
   return; larger universes win. Capitalmind: 20-30 names best on return
   AND drawdown. Leave N=25; a 15/50 sweep is only a robustness checkbox.
7. **India post-crash practice** (who changed what after N200M30's −31.8%):
   nobody touched the 6m/12m signal. Changes: Capitalmind folded momentum
   into a regime-rotating flexi-cap (momentum primary, quality/low-vol/value
   alternates) and LOOSENED stock-level exits (tight exits whipsawed
   2023-25); Wright added a hedged variant (trails unhedged since inception
   — permanent put hedging did NOT pay) + hard 10%-portfolio-DD gradual
   cash rule; Weekend Investing added crisis-only cash mode to rotational
   strategies (best live Q1-2026 results: −2 to −8% vs Nifty −14.5%); Axis/
   index funds changed nothing. Sector caps: NSE indices have NONE
   (financials hit 49% of N200M30, May 2026); Capitalmind/Axis cap sectors
   as cheap insurance; no Indian evidence caps cost return.
8. **Permanent quality/low-vol blending dilutes** (Abacus 2024: a 50:50 mix
   of two pure momentum indices matches the MQ blends with lower vol —
   quality sleeve adds little). Regime-conditional rotation is the
   defensible variant, permanent blend is not.
9. **2021-26 window is now a 3-stress torture set**: slow grind (Sep-24→
   Apr-25, −31.8%), crowding unwind (Oct-25), geopolitical gap (Q1-26 "US-
   Iran", Nifty −14.5%). Plus OUR worst DD was the 2022-23 grind. Any
   overlay must be judged per-episode, not on full-period Sharpe alone.

## Revised test plan (supersedes "Proposed test waves" above)

Wave 1 — config-only, existing signals (`risk_adjusted_momentum`,
`return_smoothness`, `distance_from_52w_high` already registered):
  W1a. Exit-buffer widening: exit_rank 50, 60 (vs 35). [turnover ↓]
  W1b. Rebalance-day sweep: trading_day 1 vs 8 vs 15. [~free Sharpe]
  W1c. NSE-style score: 50/50 z-blend of 6m+12m risk-adjusted momentum.
  W1d. 12m listing age in dynamic universe (seasoning 126→252 bars).
  W1e. FIP smoothness as score component (mom z + smoothness z) — engine
       has no two-stage select; blend approximates the top-75→smoothest-25
       screen.
  W1f. (robustness checkbox) N=15 / N=50 arms.
Wave 2 — small engine additions:
  W2a. GHM 3-state graded exposure: Nifty 12m & 1m trend agreement →
       1 / 0.5 / 0 gross exposure; asymmetric (blocks buys, doesn't force
       sells). Replaces binary v7 gate. [highest-priority overlay]
  W2b. Portfolio-level vol target: exposure = min(1, 12% / σ̂_126d of own
       net returns), monthly step. (Existing `volatility_target` sizing is
       per-position — this is a new portfolio-level scaler hook.)
  W2c. Crash dials on the same scaler hook: momentum gap quintile + cross-
       sectional IQR quintile → trim exposure when extreme.
  W2d. Hype screen (price/volume-only scaled-turnover proxy until mcap data
       exists): exclude names whose trailing 21d traded value > k× their own
       trailing 252d median (k≈3-4 sweep) — targets the freshly-hyped-
       near-peak failure mode directly.
  W2e. Persistence blend (Calluzzo): score = w·mom(12-1) + (1−w)·anticipated
       next-month mom (computable today from 11-1); w sweep {1.0, 0.7, 0.5}.
       Expect similar gross, lower turnover, higher net.
  W2f. Staggered half-tranches: two half-books rebalancing day 1 / day 11
       (kills rebalance-timing luck; untested in India).
Wave 3 — need new data first:
  W3a. Shares outstanding / mcap (NSE securities master or bhavcopy) →
       proper scaled-turnover screen + mcap-ranked universe with traded-
       value floor. [biggest documented effect; data work first]
  W3b. Sector table (NSE industry classification) → 25-30% sector cap
       (schema's max_sector_pct exists, currently a warning no-op).
  W3c. Residual momentum (rolling market-model regression signal) —
       strongest EM-validated signal upgrade from first survey.
  W3d. April-effect audit of our own monthly returns (analysis, not a run).

## Skip list (evidence says don't)

Permanent put hedging (Wright hedged trails unhedged live); permanent
quality blend (Abacus); weekly/fortnightly rebalance (costs); tighter
concentration than ~20 (worst DD, no risk-adjusted gain); inverse-vol
weighting (our v8 + MSCI: low-vol tilt fights the signal); per-position
stops of any flavor (our 4/4 + ASM/T2T frictions); 12-7 echo window
(Goyal-Wahal); portfolio-DD-triggered de-risking as PRIMARY rule (slow
proxy — but note Wright uses 10% DD as a live backstop; test only as
backstop, judged per-episode); learning-to-rank ML (5y sample too short).

Full agent reports with all citations: see session artifacts 2026-07-12;
key sources inline above.

---

# Agreed test plan (2026-07-12, owner-approved) — "the batches"

Baseline: m2 (12-1 momentum, top-25 equal-weight, monthly, dyn-1000)
= net +296% / Sharpe 1.22 / DD −32.9%, Jul 2021–Jul 2026.

Batch 1 — config-only, existing data (runner: scripts/adhoc/batch1_m2_improvements.py):
  1. exit_rank 50 (vs 35)
  2. exit_rank 60
  3. NSE-style score: 50/50 z-blend of 6m + 12m risk_adjusted_momentum
  4. #3 + exit_rank 50 combined
  5. binary index_above_ma regime gate (NIFTYBEES proxy) on dyn-1000
  6. 12m listing seasoning (universe eligibility 126 → 252 bars)
  7. FIP smoothness in score (mom z + return_smoothness z), config-only

Batch 2 — engine additions, tested on Batch-1 winner:
  8. graded asymmetric regime gate: 3 index signals (100d SMA, 200d SMA,
     12m return) → target exposure 0/⅓/⅔/1; blocks new buys, never
     force-sells
  9. portfolio-level vol target: exposure = min(1, 12% / σ̂_126d of own net
     daily returns), stepped at rebalance
  10. #8 + #9 stacked

Batch 3 — new signal:
  11. residual momentum: 12-1 momentum on rolling market-model residuals
      (vs NIFTYBEES), standardized by residual σ

Deliberately excluded: per-position stops (0/4), per-stock SMA gates (5/5
redundant), weekly rebalance, 12-7 window, rank/inverse-vol weighting.

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

# b2d-ST — the four-signal-gate momentum strategy (campaign champion)

Written 2026-07-12 for future reference. This documents the best
growth-profile strategy from the July 2026 momentum campaign in full
detail: what it does, why every component is there, what it earned, and
how to reproduce it exactly.

**Identity:** experiments DB run **1346**, family `adhoc_st_gate_stmad_b2d`,
config_hash `698951d560855d83`, code commit `b80bb38`. Lineage:
m2 → b1d (score + buffer) → b2d (graded gate) → **b2d-ST** (supertrend
added to the gate).

**Headline (net of all charges, ₹4cr, 2021-07-13 → 2026-07-10):**
+291.8% total, **32.1% CAGR**, Sharpe **1.35**, max drawdown **−24.3%**
(trough 2025-03-03), annualized vol 22.5%, 994 trades, charges ₹39.7L.
Yearly net: 2021 +29.7%, 2022 +6.8%, 2023 +72.5%, 2024 +55.0%,
2025 −3.3%, 2026(H1) +3.7%. Note what the overlays bought vs raw m2
(+296.3%/−32.9%/1.22): the same return with a third less drawdown, and
the two loss years nearly flattened (2022: −8.6%→+6.8%; 2025:
−10.0%→−3.3%).

---

## The strategy in one paragraph

Once a month, rank every reasonably liquid NSE stock (a dynamic
~1,000-name universe) by *volatility-adjusted* momentum — how much it
returned over the past 6 and 12 months per unit of its own daily
volatility, skipping the most recent month. Buy the top 25, equal-weight.
Hold each name until it decays below rank 50 (not 25 — a wide exit
buffer). Before buying anything *new*, check four health signals on the
market itself; scale new buying by the fraction that pass, down to zero
in confirmed downtrends — but never force-sell holdings the rank still
justifies. Everything compounds; nothing is withdrawn.

## Full specification

### Universe (dynamic top-1000, PIT-honest)
- Candidate pool: all NSE mainboard plain-equity series (~2,080 names,
  `scripts/adhoc/nse2000.csv`; ex ETF/iNAV/SGB).
- At each rebalance: keep the top **1,000** by trailing **126-day median
  rupee traded value** (close × volume), computed from bars ≤ the
  decision date only. New listings become eligible after 126 trading
  days. Names that decay out drop at the next rebalance.
- Liquidity floor downstream: median traded value ≥ **₹5cr**.
- First-class config since commit `aa6aa6e`:
  `universe: {symbols: <pool>, point_in_time: false, dynamic_top_n: 1000,
  min_median_traded_value: 50000000}`.
- Known residual bias: delisted names are absent from Kite data entirely.

### Signal & score (vol-adjusted momentum, NSE-index style)
- `ram6`  = return over 126 bars, skipping the last 21, ÷ realized vol
  (252-day, annualized, daily simple returns).
- `ram12` = same with a 252-bar return window.
- Score = cross-sectional z-score of each, weighted **50/50**.
- Why: de-ranks parabolic junk (same return earned with 4× the wiggle
  scores ¼ as well). Cut DD by ~5pp vs raw 12-1 in testing. Skip-month
  avoids short-term reversal. (Raw 12-1 = the m2 baseline.)

### Selection (top-25 with a wide exit buffer)
- Buy into the top **25** by score; **hold until rank > 50** (`exit_rank`).
- Why 25: Indian evidence (Raju, Capitalmind) puts the optimum at 20-30.
- Why the 35→50 buffer widening: cuts turnover (charges are ~10% of
  gross P&L); tested positive ONLY in combination with the vol-adjusted
  score (steady names that slip ranks tend to recover; raw-momentum
  slippers were burst bubbles — buffer alone HURT, see runbook batch 1).

### Sizing
- Equal weight across selected names, **max 5% of equity per position**.
- Weights recomputed from CURRENT total equity every rebalance — full
  compounding, no withdrawals.
- Rejected alternatives (all tested, all diluted): inverse-vol weights,
  rank/score weighting, MAD/FIP score tilts.

### The graded asymmetric regime gate (the strategy's signature)
Four boolean signals evaluated on **NIFTYBEES** (Nifty-50 ETF proxy),
bars ≤ decision date only:
1. close > 100-day SMA
2. close > 200-day SMA
3. trailing 252-bar return > 0
4. **Supertrend(period=10, multiplier=3.0) in up-state** — ATR-adaptive
   bands (Wilder smoothing, standard ratchet); flips faster than any
   fixed SMA in volatility-spike breaks (the 2026 gap-down type), quiet
   in slow grinds.

Let f = (signals passing)/4 ∈ {0, ¼, ½, ¾, 1}.
- **New entries** get weight × f. At f = 0, no new buys at all; freed
  capital waits in cash.
- **Existing holdings are NEVER force-sold by the gate** — they exit
  only via exit_rank. This asymmetry is why the graded gate kept +30pp
  more return than the binary v7-style gate: in V-recoveries it was
  still holding winners while the binary version had sold the bottom.
- Engine: `regime:` section of StrategyConfig (commit `e36e320`;
  supertrend kind added in `b80bb38`).

### Rebalance & execution
- Monthly, first trading day. Signals at close of T → orders at T+1
  open ("next_open"), max participation 5% of bar volume.
- Monthly is settled Indian evidence (weekly loses net to costs;
  mid-month timing bump remains an untested refinement).

### Costs
- Zerodha CNC schedule `zerodha_2026` (STT 0.1% both sides dominates;
  DP charge per scrip-day on sells; brokerage ₹0 delivery). ~25-30bp
  round trip. Applied to ALL years (pre-2026 approximate).
- NOT modeled: capital-gains tax (STCG ≈ ₹4.2L over the 5y at ₹10L
  scale — see results_summary), dividends (would ADD ~0.9-1.7L per ₹10L).

## What was tried and rejected (don't relitigate without new data)
Per-position stops of every flavor incl. supertrend-style ATR trails
(0 for 4, worsens DD — stock-level exits fight daily mean reversion and
ASM/T2T frictions); per-stock SMA gates (redundant 5/5); weekly
rebalance; 12-7 echo window; inverse-vol weighting; FIP smoothness, MAD,
residual momentum in the score; mcap-ranked universe and scaled-turnover
churn veto (negative ON TOP of this design — the score+gate already
occupy that niche); permanent quality blends; permanent put hedging
(live Indian evidence negative). Walk-forward validation: owner declined.

## Scaling (tested)
₹10k/slot (₹2.5L): b2d variant +266% — viable, integer-share slot misses
are the only real drag. ₹40k/slot (₹10L): +276.7% → ₹37.7L, charges
~4% of gross. ₹4cr: headline above. Vol-target overlay (b2e-ST profile:
add `vol_target: {target_annual_vol: 0.12, lookback_bars: 126}`) is the
defensive sibling: +203.7%/−18.8%/Sharpe 1.41.

## Reproduction
```
uv run python scripts/adhoc/stmad_b2d.py          # runs st_gate variant
# or via the harness on any base YAML with:
#   regime.signals: [{kind: above_ma, params: {window: 100}},
#                    {kind: above_ma, params: {window: 200}},
#                    {kind: positive_return, params: {window: 252}},
#                    {kind: supertrend, params: {period: 10, multiplier: 3.0}}]
```
Artifacts: `artifacts/adhoc/adhoc_st_gate_stmad_b2d/2026-07-12_094556/`
(equity curve, trades, per-stock P&L). Full config JSON: experiments DB
run 1346 `config_json`.

## Honest caveats (read before trusting)
1. One 5-year path (Jul 2021–Jul 2026), and this design is roughly the
   45th test against it. The supertrend gate's edge (+8pp, +0.03 Sharpe
   vs b2d) is directionally consistent across three configurations but
   individually within noise. **Paper trading is the real validation.**
2. Delisted names absent (survivorship residue); price returns only;
   2026 charge schedule throughout; mcap-era tests used non-PIT shares.
3. The window contains three stress types (2022-23 grind, 2024-25 factor
   crash, Q1-26 gap) but NO 2008/2020-scale crash. The gate has never
   been tested against a −50% market.
4. Capacity: fine at personal scale; the dynamic universe's tail names
   would not absorb institutional size at 5% participation.

## Path to live
YAML-ify via the dynamic universe spec → `platform backtest run` parity
check → 4+ weeks paper (`platform paper`) with divergence review per
docs/runbook.md → owner promotion gate. Daily ops need the TOTP login
(owner-only) and the kill switch is `platform live killswitch`.

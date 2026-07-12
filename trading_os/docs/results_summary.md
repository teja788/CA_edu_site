# Momentum campaign — consolidated results (updated 2026-07-12)

All returns NET of brokerage + charges, ₹4cr portfolio, Jul 2021 – Jul 2026.
Caveats on every row: delisted names absent from Kite data, price returns
(no dividends), zerodha_2026 charge schedule applied to all years.
Full detail: docs/backtesting_runbook.md (log), docs/momentum_research_notes.md
(research + test plan), experiments DB families named in the runbook.

m2 = 12-1 momentum, top-25 equal-weight, monthly rebalance.

| # | Phase | Variant | Universe | Net | MaxDD | Sharpe | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | 1 SMA-family | v1 weekly SMA cross (per-stock) | N200 current | +119.8% | −14.2% | — | dropped |
| 2 | 1 | v2 golden cross | N200 current | +135.5% | −13.1% | — | dropped |
| 3 | 1 | v3 SMA band | N200 current | +120.9% | −14.6% | — | dropped |
| 4 | 1 | v4 SMA + confirm | N200 current | +126.8% | −13.4% | — | dropped |
| 5 | 1 | v5 wide ATR stop | N200 current | +96.6% | −15.4% | — | dropped |
| 6 | 1 momentum | v6 momentum top-25 | N200 current | +389.6% | −26.0% | 1.57 | survivorship-inflated |
| 7 | 1 | v7 = v6 + binary regime gate | N200 current | +320.5% | −20.1% | 1.67 | gate validated |
| 8 | 1 | v8 = v6 + inverse-vol weights | N200 current | +345.6% | −25.3% | 1.55 | inv-vol dropped |
| 9 | 2 universe | m2 | static-2020 top-200 | +183.2% | −26.8% | 1.04 | |
| 10 | 2 | m2 | static-2020 top-500 | +133.6% | −34.5% | 0.81 | |
| 11 | 2 | m2 | static-2020 top-1000 | +267.1% | −33.2% | 1.15 | |
| 12 | 2 | m2 | static-2020 top-1224 | +242.6% | −33.2% | 1.09 | |
| 13 | 2 | m2 | dynamic top-200 | +141.5% | −33.4% | 0.82 | dyn-200 = peak-chasing outlier |
| 14 | 2 | m2 | dynamic top-500 | +245.7% | −37.6% | 1.08 | |
| 15 | 2 | **m2 (BASELINE)** | **dynamic top-1000** | **+296.3%** | **−32.9%** | **1.22** | 1000 = sweet spot |
| 16 | 2 | m2 | dynamic all (~1930) | +259.7% | −32.9% | 1.15 | dilutes past 1000 |
| 17 | 3 batch 1 | b1a exit_rank 50 | dyn-1000 | +287.4% | −34.6% | 1.20 | buffer alone hurts |
| 18 | 3 | b1b exit_rank 60 | dyn-1000 | +268.1% | −35.0% | 1.16 | dropped |
| 19 | 3 | b1c NSE vol-adjusted score | dyn-1000 | +248.6% | −28.0% | 1.15 | DD tool |
| 20 | 3 | b1d = b1c + exit 50 | dyn-1000 | +280.7% | −28.3% | 1.23 | balanced base |
| 21 | 3 | b1e binary regime gate | dyn-1000 | +257.7% | −33.6% | 1.38 | v7 transfers |
| 22 | 3 | b1f 12m listing seasoning | dyn-1000 | +285.5% | −32.9% | 1.20 | neutral, dropped |
| 23 | 3 | b1g FIP smoothness blend | dyn-1000 | +245.2% | −39.1% | 1.12 | fails, dropped |
| 24 | 4 batch 2 | b2a = m2 + graded gate | dyn-1000 | +287.6% | −33.6% | 1.27 | +30pp vs binary gate |
| 25 | 4 | b2b = m2 + vol target 12% | dyn-1000 | +205.0% | −23.5% | 1.33 | DD tool, return cost |
| 26 | 4 | b2c = m2 + both | dyn-1000 | +207.6% | −23.8% | 1.38 | |
| 27 | 4 | **b2d = b1d + graded gate (CHAMPION)** | dyn-1000 | **+283.4%** | **−24.8%** | **1.32** | ~+30.7%/yr net |
| 28 | 4 | b2e = b1d + both (DEFENSIVE) | dyn-1000 | +196.5% | −19.0% | 1.38 | ~+24%/yr net |
| 29 | 5 batch 3 | b3a residual momentum (vs NIFTYBEES) | dyn-1000 | +123.6% | −32.6% | 0.88 | signal fails here |
| 30 | 5 | b3b = b3a + graded gate | dyn-1000 | +110.1% | −25.3% | 0.91 | dropped |
| 31 | 5 | b3c = residual mom in champion structure | dyn-1000 | +147.8% | −22.3% | 1.07 | dropped |
| 32 | 6 sizing | b1d @ Rs 10k/position (capital Rs 2.5L) | dyn-1000 | +254.0% | −28.2% | 1.19 | viable at retail size |
| 33 | 6 | b2d @ Rs 10k/position (capital Rs 2.5L) | dyn-1000 | +266.2% | −24.6% | 1.30 | viable at retail size |
| 34 | 6 | b1d @ Rs 40k/position (capital Rs 10L) | dyn-1000 | +268.5% | −28.4% | 1.21 | Rs 10L → Rs 36.8L |
| 35 | 6 | b2d @ Rs 40k/position (capital Rs 10L) | dyn-1000 | +276.7% | −24.8% | 1.31 | Rs 10L → Rs 37.7L |
| 36 | 6 | b2e @ Rs 40k/position (capital Rs 10L) | dyn-1000 | +194.5% | −18.9% | 1.37 | Rs 10L → Rs 29.5L |
| 37 | 7 tier-2 | b2d on mcap-ranked universe | mcap-1000 | +247.4% | −24.3% | 1.23 | worse; dropped |
| 38 | 7 | b2d + churn-quintile veto | dyn-1000 | +207.1% | −24.8% | 1.17 | worse; dropped |
| 39 | 7 | b2d + both | mcap-1000 | +183.4% | −25.1% | 1.12 | worst; dropped |

## MARKED FOR FUTURE (owner, 2026-07-12)

Two strategies of record going forward — candidates for paper trading and
any further overlay work. Exact reproduction records (experiments DB):

| Strategy | Spec | Run id | config_hash | code commit | Rerun |
|---|---|---|---|---|---|
| **b1d** (no-overlay base) | vol-adj score (6m+12m, vol_window 252) + exit_rank 50, top-25 monthly, dyn-1000 | 1326 | `b024895df6bc440c` | 8956038 | `uv run python scripts/adhoc/batch1_m2_improvements.py b1d_score_exit50` |
| **b2d** (champion) | b1d + graded asymmetric regime gate (NIFTYBEES 100SMA/200SMA/12m-ret) | 1333 | `9524dc5441b10f8d` | e36e320 | `uv run python scripts/adhoc/batch2_m2_overlays.py b2d_graded_score` |

Full config JSON for both is in the experiments DB (`config_json` on the
run ids above). Note: the dynamic top-1000 universe lives in the runners'
`DynamicTopNResolver`/`SeasonedTopNResolver`, not in the YAML universe spec
— promoting these to `strategies/examples/` YAMLs needs the dynamic
traded-value universe as a first-class UniverseSpec option first (open
engine item).

Settled negatives (multiple tests each): per-position ATR/chandelier stops
(0/4), per-stock SMA gates (0/5 vs m2), inverse-vol weighting, FIP blend,
exit-buffer widening without vol-adjusted scoring, weekly rebalance.

Batch 3 verdict: residual momentum (Blitz et al., EM-validated in the
literature) does NOT transfer to this universe/window — pure residual
ranking earns less than half the plain-momentum return at lower Sharpe even
inside the champion structure. Dropped; plain + vol-adjusted price momentum
stays the signal.

Tier-2 verdict (rows 37-39, runner `scripts/adhoc/tier2_mcap_churn_b2d.py`):
the mcap-ranked universe and the scaled-turnover (churn) veto — the
literature's biggest documented effects — are NEGATIVE on top of b2d. Every
variant lost 36-100pp of return for zero drawdown improvement. Best
explanation: b2d's vol-adjusted score + graded gate already neutralize the
hyped-junk channel these screens target, so the screens only remove the
high-churn WINNERS (the MAZDOCK/BSE-type multibaggers that drove 2021-26);
the published 19.4%-vs-8.5% split was measured on raw momentum without
those defenses, on 2006-2025. Also mcap here is a non-PIT snapshot
reconstruction. Champion remains b2d unchanged.

Rs 10k/position sizing check (rows 32-33): both marked strategies survive
retail sizing — b2d turns Rs 2.5L into Rs 9.16L (5y) vs the pro-rata Rs
9.6L at Rs 2L/position sizing. Costs stay ~5% of gross P&L; the drag is
mostly integer-share slot misses (770 vs 1010 trades — high-priced stocks
exceed a Rs 10k slot). Campaign COMPLETE: all planned batches run.

## Tax & dividend estimates — ₹40k/position runs (rows 34–36)

STCG computed from actual trade ledgers (FY netting, loss carry-forward,
15% before 2024-07-23 / 20% after, on net realized P&L; all FYs were net
positive so no carry-forward triggered). Dividends estimated at 0.8–1.5%
yield on average invested equity (dividend table is empty — no per-stock
data; price-return backtests exclude dividends, so these would ADD):

| Strategy | STCG owed (5y) | Dividends est (5y) | Final equity net of tax (approx) |
|---|---|---|---|
| b1d | ₹3.81L | +₹0.91–1.71L | ~₹33.9L |
| b2d | ₹4.22L | +₹0.91–1.70L | ~₹34.8L |
| b2e | ₹2.89L | +₹0.66–1.25L | ~₹27.6L |

Peak STCG year is FY2024 (the +72% 2023 run): ₹1.3–1.7L owed in one year —
advance-tax planning needed. Estimates ignore compounding drag from paying
tax out of the pot (real net-of-tax equity would be a few % lower still)
and assume no other income offsets.

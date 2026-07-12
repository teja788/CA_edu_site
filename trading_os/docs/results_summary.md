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
| 40 | 8 indicators | b2d + supertrend(10,3) 4th gate signal | dyn-1000 | **+291.8%** | **−24.3%** | **1.35** | beats b2d on all three |
| 41 | 8 | b2d + MAD 0.25 score weight | dyn-1000 | +257.4% | −25.4% | 1.23 | dilutes; dropped |
| 42 | 8 | b2d + both | dyn-1000 | +261.2% | −25.0% | 1.25 | MAD drag dominates; dropped |
| 43 | 8 | b1d + supertrend-ONLY gate (binary) | dyn-1000 | +265.8% | −22.6% | 1.36 | vs b1d: DD −5.7pp, Sharpe 1.23→1.36 |
| 44 | 8 | b2e + supertrend 4th gate signal | dyn-1000 | +203.7% | **−18.8%** | **1.41** | beats b2e on all three |
| 45 | 9 out-of-window | **b2d-ST on 2019-2020 (COVID exam)** | dyn-1000 | +62.6% (2y) | −29.8% | **1.35** | survivors-only upper bound; see note |
| 46 | 10 window sweep | b2d-ST, skip 21→0 | dyn-1000 | +191.2% | −27.6% | 1.05 | skip-month EARNS its keep in India too |
| 47 | 10 | b2d-ST, skip 21→10 | dyn-1000 | +221.3% | −26.2% | 1.16 | dropped |
| 48 | 10 | b2d-ST, 6m-heavy 70/30 | dyn-1000 | +238.2% | −23.8% | 1.22 | dropped |
| 49 | 10 | **b2d-ST, 12m-heavy 30/70** | dyn-1000 | **+308.9%** | −24.8% | **1.37** | challenger; OOW validation pending |
| 50 | 10 | b2d-ST + 3m component | dyn-1000 | +265.4% | −24.4% | 1.30 | dropped |
| 51 | 10 | b2d-ST + 9m component | dyn-1000 | +286.6% | −23.9% | 1.33 | dropped |
| 52 | 10 | b2d-ST, 9m replaces 6m | dyn-1000 | +267.9% | −25.9% | 1.29 | dropped |
| 53 | 10 | pure 1m momentum | dyn-1000 | +65.8% | −19.9% | 0.61 | reject confirmed, 1463 trades |
| 54 | 10 | 12m-heavy challenger on 2019-2020 | dyn-1000 | +55.6% (2y) | −33.0% | 1.20 | FAILS OOW exam; rejected |
| 55 | 11 US port | **b2d-ST on US (S&P1500 pool, SPY gate)** | US dyn-1000 | +176.5% | −31.0% | 0.88 | survives the hardest market; ~2x SPY CAGR |
| 56 | 12 adaptive | GHM adaptive weights, 2021-26 | dyn-1000 | +274.8% | −26.6% | 1.32 | worse than champion; rejected |
| 57 | 12 | GHM adaptive weights, 2019-20 | dyn-1000 | +58.7% (2y) | −31.1% | 1.29 | worse on both windows; rejected |
| 58 | 13 survivorship | **b2d-ST 2019-20, delisted names restored** | dyn-1000+133 | +61.1% (2y) | −29.9% | 1.33 | bias measured: −1.5pp/2y — small |

## MARKED FOR FUTURE (owner, re-marked 2026-07-12 after supertrend sweep)

Strategies of record (also flagged `is_marked` in the experiments DB via
`platform experiments mark` — `compare` uses the latest as its default
baseline). Full champion write-up: docs/champion_strategy_b2dst.md.

| Strategy | Spec | Run id | config_hash | code commit | Rerun |
|---|---|---|---|---|---|
| **b2d-ST (CHAMPION, growth)** | vol-adj 6m+12m score + exit 50 + 4-signal graded gate (100/200SMA, 12m ret, supertrend 10/3) | 1346 | `698951d560855d83` | b80bb38 | `uv run python scripts/adhoc/stmad_b2d.py` (st_gate) |
| **b2e-ST (defensive)** | b2d-ST + vol target 12%/126d | 1350 | see DB | b80bb38 | `uv run python scripts/adhoc/st_all_marked.py` (st4_b2e) |
| **b1d** (no-overlay base) | vol-adj score + exit_rank 50, top-25 monthly, dyn-1000 | 1326 | `b024895df6bc440c` | 8956038 | `uv run python scripts/adhoc/batch1_m2_improvements.py b1d_score_exit50` |

Superseded marks: b2d (run 1333) — replaced by b2d-ST.

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

Supertrend sweep across all marked strategies (rows 40, 43, 44): the
supertrend gate improves EVERY strategy it touches — b2d+ST dominates b2d
(+291.8/−24.3/1.35), b2e+ST dominates b2e (+203.7/−18.8/1.41, the best
Sharpe of the whole campaign), and even as b1d's ONLY gate signal it
trades 15pp of return for −5.7pp DD and Sharpe 1.23→1.36. Coherent
mechanism (fast ATR-adaptive throttle + asymmetric non-forced-selling),
consistent direction across three configurations — this is the real
deal as far as one price path can show. Pending owner: re-mark champions
as b2d+ST (growth) and b2e+ST (defensive).

Adaptive signal-speed weights REJECTED (rows 56-57): the theoretically
best-motivated upgrade (12m-heavy when gate fully on, faster blend in
transitions — GHM) loses to the champion's static 50/50 on BOTH windows.
Sixth consecutive score-modification failure; the score is closed.

Survivorship bias, MEASURED (row 58, expanded pool with 133 bhavcopy-
recovered delisted names): the 2019-20 exam moves from +62.6%/−29.8%/1.35
to +61.1%/−29.9%/1.33 — a 1.5pp haircut over two years. Why so small:
momentum-with-vol-adjustment rarely ranks dying names into the top 25
(they fade before they die), and the worst blowups (DHFL, JETAIRWAYS +17
others) were CA-excluded from ingestion, so the true bias is somewhat
larger than measured but same order. The COVID-exam conclusion stands.

US port (row 55, runner `scripts/adhoc/us_b2dst.py`, isolated us_data/
store, cost schedule `us_2026` = SEC+TAF only): the untouched champion
design on the S&P 1500 pool with SPY as the gate benchmark earns +176.5%
net / CAGR 22.7% / Sharpe 0.88 / DD −31.0% (trough Jul-2022) over the
same Jul-2021..Jul-2026 window — roughly double SPY's ~11.5% CAGR, net,
in the most efficient market on earth. Yearly: 2021 +1.9, 2022 −12.6,
2023 +21.2, 2024 +34.7, 2025 +18.7, 2026H1 +60.2. Weaker than India
(1.35 → 0.88 Sharpe) exactly as the EM-premium literature predicts.
Caveats: current-constituent pool (survivorship), yfinance auto-adjust =
total-return momentum (mildly flattering), charges $1,759 total (US costs
are a rounding error — the strategy's cost sensitivity is India-specific).

Window-geometry sweep (rows 46-53, runner
`scripts/adhoc/window_sweep_b2dst.py`): a strikingly MONOTONE pattern —
every change that speeds the signal up (drop/halve the skip, 6m-heavy,
+3m, pure 1m) hurts, every slowdown helps; 12m-heavy 30/70 weighting is
the sweep winner (+308.9%/−24.8%/1.37, +17pp return and +0.02 Sharpe over
the champion at −0.5pp DD). The skip-month question is settled AGAINST
the NSE-index convention: skip 0 loses 100pp — India's 1-month reversal
is alive in this universe. 12m-heavy CHALLENGER REJECTED (row 54): on
2019-2020 it loses to the 50/50 champion on all three metrics (+55.6% vs
+62.6%, DD −33.0% vs −29.8%, Sharpe 1.20 vs 1.35). The 30/70 edge was
specific to 2021-26's long-duration trends; 50/50 is the robust setting
across both regimes. Champion stays b2d-ST unchanged — and this is the
multiple-testing discipline doing exactly what it exists to do: the
sweep's best in-sample cell did not generalize.

Out-of-window COVID exam (row 45, runner `scripts/adhoc/b2dst_2019_2020.py`
after a 2017-07 Kite backfill of 722k rows): the champion earned +9.0% in
2019 (mid/small bear — correctly quiet) and +48.5% in 2020, with the COVID
drawdown bottoming at −29.8% on 2020-03-23 (the market's exact low) vs
Nifty ~−38% peak-to-trough and momentum indices worse — the 4-signal gate
cut the crash AND the asymmetric design caught the V-recovery. Sharpe 1.35,
numerically identical to the 2021-26 window — strategy behavior is stable
across two very different regimes. Caveat: survivors-only pool (delisted
2019-20 names invisible) — an upper bound; bhavcopy-restored rerun pending.

Indicator wave verdict (rows 40-42, runner `scripts/adhoc/stmad_b2d.py`,
first run through the run-variants harness): adding supertrend(10,3) on
NIFTYBEES as a FOURTH graded-gate signal (f now grades in quarters) beats
b2d on return (+8.4pp), drawdown (−24.3 vs −24.8) and Sharpe (1.35 vs
1.32) — the ATR-adaptive fast component reacts to vol-spike breaks
(Q1-2026 type) faster than the fixed SMAs, exactly the GHM fast/slow
blend prediction. Candidate to supersede b2d pending owner mark; caveat:
~40th test on one 5y path, improvement is real but modest — treat as
gate refinement, not new alpha. MAD in the score dilutes like every rank
auxiliary tried (FIP, inv-vol, residual momentum) — the vol-adjusted
momentum blend keeps winning as-is.

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

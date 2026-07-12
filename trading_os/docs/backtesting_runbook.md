# Backtesting runbook — running real-data strategy studies

Operational guide distilled from the first real-data backtest sessions
(2026-07-11: NIFTY 50/200 trend systems, 8-variant comparison). Complements
`docs/runbook.md` (go-live) — this one is about research runs.

## Daily auth flow

1. Credentials in `.env` (git-ignored): `TOS_KITE_API_KEY`,
   `TOS_KITE_API_SECRET`, optionally `TOS_KITE_USER_ID` /
   `TOS_KITE_PASSWORD` / `TOS_KITE_TOTP_SECRET` for headless login.
2. Access tokens expire daily. With the TOTP secret in `.env`:
   `uv run platform data login --totp`. Without it, use the interactive
   flow (`data login --no-browser`) or `scripts/adhoc/manual_totp_login.py
   <6-digit-code>` — TOTP codes expire in ~30 s and Kite locks the account
   after 5 bad attempts, so run it immediately after generating the code.
3. Static IP registration is required only for API **order placement**
   (SEBI algo framework) — historical data and quotes work from any IP.

## Data

- One-time: `uv run platform data instruments`.
- Sync: `uv run platform data sync SYM1 SYM2 ... --timeframe day --start
  2020-01-01`. Quote symbols with shell metacharacters (`"M&M"`,
  `"BAJAJ-AUTO"`). ~200 symbols × 6.5y daily ≈ 2–3 minutes.
- Start the sync ~18 months before the backtest window so 200-day
  indicators are warm on day one (frames load full-history; the engine
  clips the trading calendar, not the data).
- Constituent lists: `https://archives.nseindia.com/content/indices/
  ind_nifty200list.csv` (same pattern for nifty50list, nifty500list...).
  A copy of the Jul-2026 NIFTY 200 list lives in `scripts/adhoc/`.
- The NIFTY 50 **index** series is not in the cash-equity instrument
  master; use `NIFTYBEES` as a regime-filter proxy.
- A fresh sync stores Kite's adjusted-as-of-fetch prices — consistent for
  a one-shot study. The raw store is append-only, so a later corporate
  action leaves it mixed-scale until `data adjust` runs; re-run
  `data doctor` before reusing a weeks-old store. "no adjusted day data
  ... falling back to raw" warnings are expected while no corporate
  actions are recorded.
- Dividends are not imported yet → all results are **price returns**.
  `data import-dividends` + the total_return_close load-time column
  (already plumbed) fixes that when dividend data is available.

## Running studies

Reusable runners live in `scripts/adhoc/` — run them **from the
`trading_os/` directory** (`uv run python scripts/adhoc/<script>.py`);
`uv run` and `.env` discovery are cwd-sensitive.

- `nifty50_sma200_atr.py` — per-stock SMA-200 system with 3×ATR chandelier
  stop (50 independent runs + combined view).
- `nifty200_sma_cross.py` — per-stock SMA-200 cross system, no stop
  (200 runs + combined view, net-of-charges reporting).
- `nifty200_variants.py` — 8-variant comparison: weekly decisions, golden
  cross, ±2% band hysteresis, 3-day confirmation, wide 5×ATR stop
  (per-stock ×200 each), and momentum top-25 / +regime gate / +inverse-vol
  (portfolio runs).

The pattern all of them follow:

1. Per-stock systems: one single-symbol `StrategyConfig` per name —
   `top_n=1`, the entry rule expressed as an eligibility **filter**
   (`index_above_ma`, `above_ma_band`, `above_ma_confirm`,
   `fast_ma_above_slow_ma`), `rebalance: daily`, exits via filter turning
   false and/or a `trailing_stop_*` overlay. Portfolio systems: one config
   over the whole universe with signals + top-N selection.
2. **Persist every run**: an `ExperimentRun` row per run (family = stable
   slug like `adhoc_sma200_cross_nifty200`, variant = symbol) into
   `artifacts/experiments.sqlite`, plus a timestamped
   `artifacts/adhoc/<family>/<ts>/` dir with `results.json`, per-stock CSV
   and equity curves. `res.equity` is net of charges, `res.gross_equity`
   gross — reporting leads with **net**.
3. Always compute an equal-weight buy-and-hold baseline from the same
   store data for the same window — it reframes every result.

Timing on a 2-vCPU codespace: ~50 per-stock 5-year runs ≈ 3–4 min,
200 ≈ 12–15 min, the 8-variant sweep ≈ 1 h.

## Sanity checks before trusting results

Each of these caught a real problem in the first session:

- **Stop/overlay fire count**: zero `trailing_stop` exits across hundreds
  of stock-years means the overlay never acted (this exposed the
  rebalance-cancels-stop engine bug — fixed; risk-exit sells now survive
  the same-bar rebalance). Check the `exit_reason` distribution of trades.
- **Trade counts**: ~80 trades on a name in a trend system = whipsaw churn
  worth investigating; low single digits on a choppy name = the entry rule
  may not be applied.
- **Provenance**: commit engine/platform changes before big run batches —
  `ExperimentRun.code_git_hash` records HEAD and lies about uncommitted
  fixes. If a batch is discovered invalid (e.g. produced by a buggy
  engine), delete those rows from the experiments DB (by family +
  `started_at` window) so the dashboard never mixes them with real runs.

## Standing result caveats (repeat with every report)

1. **Survivorship bias** — current index constituents applied backwards.
   Top performers are in the list *because* they rose. Fix: import
   historical membership (`data import-universe`, NSE monthly archives)
   and set `point_in_time: true`.
2. **Price returns** — no dividends (understates buy & hold and
   high-yield names most).
3. **Level rule** — re-entry happens the next day the stock is above the
   SMA, not on a strict re-cross.

## Results log (headline numbers, net of charges)

Window Jul 2021 – Jul 2026, ₹2L per stock, current constituents:

| Study | Result | Baseline B&H |
|---|---|---|
| NIFTY 50, SMA-200 + 3×ATR(14) stop | +19.9%, DD −20.7% | +113.6% mean |
| NIFTY 50, SMA-200 only (no stop) | +40.0%, DD −17.3% | +113.6% mean |
| NIFTY 200, SMA-200 cross, no stop | **+108.9%, DD −14.4%**, 135/200 profitable, ₹23.3L charges | +211.4% mean |
| NIFTY 200, 8-variant sweep | families `adhoc_v1..v8_*_nifty200`, comparison JSON in `artifacts/adhoc/variants_comparison_*.json` | — |
| NSE 2000 momentum top-25 (`nse2000_momentum.py`, ₹5cr liquidity screen): m1 = v6-style SMA gate | +251.3%, DD −33.8%, Sharpe 1.13 | see NIFTY 200 studies |
| — m2 returns-only (no SMA gate) | **+261.1%, DD −32.9%, Sharpe 1.15** | — |
| — m3 = m1 + 3×ATR stop | +110.2%, DD −33.5%, Sharpe 0.85 | — |
| — m4 = m2 + 3×ATR stop | +90.6%, DD −40.1%, Sharpe 0.75 | — |
| 2020-vintage top-200 (traded-value proxy, `nse200_2020.csv`): m1 SMA gate | +155.0%, DD −26.8%, Sharpe 0.97 | vs +389.6% on current constituents |
| — m2 returns-only | **+183.2%, DD −26.8%, Sharpe 1.04** | — |
| — m3 / m4 (+3×ATR stop) | +50.8% / +51.2%, Sharpe ~0.55 | — |
| m2 universe-size scaling, 2020-vintage top-N by traded value: N=200 | +183.2%, DD −26.8%, Sharpe 1.04 | families `adhoc_m2_returns_only_nse{N}v2020` |
| — N=500 | +133.6%, DD −34.5%, Sharpe 0.81 | — |
| — N=1000 | +267.1%, DD −33.2%, Sharpe 1.15 | — |
| — N=1224 (all Kite names with full 2020 history; "2000/4000" not constructible) | +242.6%, DD −33.2%, Sharpe 1.09 | — |
| DYNAMIC top-200 (recomputed monthly, trailing 126d traded value, new listings after seasoning; `nse200_dynamic.py`): m1 | +140.5%, DD −34.2%, Sharpe 0.83 | families `adhoc_m*_nse200dyn` |
| — m2 returns-only | +141.5%, DD −33.4%, Sharpe 0.82 | — |
| — m3 / m4 (+3×ATR stop) | +24.4% / +20.5%, Sharpe ~0.3 | — |
| m2 on DYNAMIC top-N: N=500 | +245.7%, DD −37.6%, Sharpe 1.08 | static-2020 counterpart +133.6% |
| — N=1000 | **+296.3%, DD −32.9%, Sharpe 1.22** | static +267.1% |
| — N=all seasoned (~1,930 ever) | +259.7%, DD −32.9%, Sharpe 1.15 | static 1224 +242.6% |

Takeaways so far: the 3×ATR stop halved returns without reducing drawdown
(shaken out on V-recoveries); the SMA filter's value is drawdown control
(−14% vs riding full corrections), paid for with roughly half the upside;
the midcap tail (NIFTY 200) is where trend following earned its keep —
all pre-survivorship-correction numbers.

NSE-2000 additions (Jul 12 session): expanding momentum top-25 from NIFTY 200
to the full mainboard *lowered* return (+251% vs +390%) and deepened drawdown
(−34% vs −26%) — the smallcap tail crashes harder in 2022/2025 than its rallies
repay, at least under a ₹5cr liquidity screen. The per-stock 200-SMA gate is
redundant on top of 12-1 momentum ranking (m1 ≈ m2; top-25 momentum names are
above their SMA anyway). Chandelier stops failed a third time, on both gated
and ungated variants — m3/m4 stops fired 733/724 times, halved returns, and
m4's DD got *worse* (−40%): stopped out at local lows, monthly rebalance
re-entered higher. Universe CSV: `scripts/adhoc/nse2000.csv` (2,080 plain-series
names, ex ETF/iNAV/SGB); sync runner: `scripts/adhoc/sync_nse2000.py`.

Survivorship, quantified: rebuilding the top-200 from *2020-known* information
(median 2020 traded value, `build_nse200_2020.py` — Kite has no historical
membership, so traded value proxies market cap; ~68% overlap with real lists)
cut the same strategy from +389.6% to +155–183% and Sharpe from 1.57 to ~1.0.
Roughly half the headline momentum return was universe vintage, not strategy.
Delisted names are still absent from Kite data, so even these numbers are
optimistic. The 12-1 momentum edge survives (still ~+20%/yr net with 2023-24
concentration) but the case for `data import-universe` + PIT membership is now
empirical, not theoretical.

The DYNAMIC monthly top-200 (the most honest configuration constructible from
Kite data — no hindsight anywhere in universe construction) landed BELOW the
frozen 2020 universe: +141.5% vs +183.2% (m2). Universe churn averaged 7
adds/drops a month (371 names ever member over 60 months); names that migrated
in mid-run earned 2/3 of closed-trade P&L (MAZDOCK, BSE, RVNL...) but the
rotation also kept buying freshly-hot liquidity near peaks (traded-value
ranking is itself a momentum screen — stacking it on 12-1 momentum doubles the
peak-chasing) and gave the deepest 2025 bleed. Realistic expectation for the
implementable strategy: ~+19%/yr net, Sharpe ~0.8, DD ~-33%. Chandelier stops
were worst-ever here (+20-24%, Sharpe 0.3) — fourth consecutive negative
result, now on the most realistic universe.

Dynamic-universe scaling resolved the earlier ambiguity: the top-200 rung is
the outlier (dynamic mega-liquid ranking = peak-chasing), and ~1000 names is
the sweet spot on BOTH universe constructions (static +267%/1.22... dynamic
+296%/Sharpe 1.22 — the two 1000-rungs nearly coincide, which is the
robustness signal). Beyond 1000, more names dilute slightly. Implementable
base case upgrades to ~+31%/yr net, Sharpe ~1.2, DD ~-33% (momentum top-25
over a dynamic ~1000-name liquid universe) — still price returns, still no
delisted names, still one 5y path.

Batch 1 (Jul 12, momentum improvement plan — config-only variants on
dyn-1000 m2; runner `scripts/adhoc/batch1_m2_improvements.py`, families
`adhoc_b1*_nse1000dyn`, baseline +296.3% / Sharpe 1.22 / DD −32.9%):

| Variant | Net | DD | Sharpe | Note |
|---|---|---|---|---|
| b1a exit_rank 50 | +287.4% | −34.6% | 1.20 | charges ₹40L→₹33L but return fell more |
| b1b exit_rank 60 | +268.1% | −35.0% | 1.16 | wider is worse again |
| b1c NSE vol-adj score (6m+12m) | +248.6% | −28.0% | 1.15 | DD −5pp, return −48pp |
| b1d = b1c + exit 50 | +280.7% | −28.3% | **1.23** | best balanced: DD −4.6pp at ~baseline Sharpe |
| b1e binary regime gate (NIFTYBEES 200SMA) | +257.7% | −33.6% | **1.38** | v7 TRANSFERS: biggest Sharpe jump, usual return cost, DD barely moved |
| b1f 12m listing seasoning | +285.5% | −32.9% | 1.20 | ~neutral; hyped-IPO channel wasn't the edge OR the drag |
| b1g FIP smoothness blend | +245.2% | −39.1% | 1.12 | fails on this universe — smooth winners underperformed |

Takeaways: exit-buffer widening HURTS here (opposite of Novy-Marx/NSE
prediction — on a dynamic liquid universe, decaying names bleed faster than
turnover costs); the buffer only pays when paired with the vol-adjusted
score (b1d), which is also the only variant to cut drawdown materially. The
binary regime gate's Sharpe gain transfers from NIFTY200 to dyn-1000
(1.22→1.38) and remains the strongest single overlay — the graded/asymmetric
version (Batch 2) starts from a confirmed base. FIP and 12m seasoning:
dropped.

Batch 2 (Jul 12, exposure overlays via new engine sections `regime` /
`vol_target`, commit e36e320; runner `scripts/adhoc/batch2_m2_overlays.py`,
families `adhoc_b2*_nse1000dyn`; graded gate = NIFTYBEES 100SMA + 200SMA +
12m return -> f∈{0,⅓,⅔,1} on NEW buys only; vol target = 12%/126d de-lever
only):

| Variant | Net | DD | Sharpe | Note |
|---|---|---|---|---|
| b2a m2 + graded gate | +287.6% | −33.6% | 1.27 | vs binary gate +257.7%/1.38: asymmetry preserves return (+30pp), gives up Sharpe |
| b2b m2 + vol target | +205.0% | −23.5% | 1.33 | classic long-only vol targeting: −9.4pp DD for −91pp return |
| b2c m2 + both | +207.6% | −23.8% | **1.38** | matches binary gate's Sharpe at 10pp less DD |
| b2d b1d + graded gate | **+283.4%** | **−24.8%** | 1.32 | **best all-rounder**: near-baseline return, −8.1pp DD, Sharpe 1.22→1.32 |
| b2e b1d + both | +196.5% | **−19.0%** | 1.38 | max-defense profile: ~24%/yr net at DD −19% |

Takeaways: the graded asymmetric gate does exactly what GHM promise — b2a
keeps +30pp more return than the binary gate by never force-selling, at a
smaller Sharpe gain; vol targeting is the drawdown tool (every vol-target
variant lands DD −19 to −24%). The composition matters more than any single
overlay: vol-adjusted score + exit 50 + graded gate (b2d) is the new
implementable base case (~+30.7%/yr net, Sharpe 1.32, DD −24.8%), and
adding vol targeting (b2e) offers a defensive alternative at ~24%/yr net,
DD −19.0% for capital that can't stomach −25%. All standing caveats apply
(no delisted names, price returns, 2026 charge schedule throughout).

Batch 3 + sizing check (Jul 12, closes out the agreed test plan; runners
`scripts/adhoc/batch3_residual_momentum.py`,
`scripts/adhoc/smallcap_marked_strategies.py`; engine gained benchmark-aware
signals + residual_momentum factor in c339ae2):

| Variant | Net | DD | Sharpe | Note |
|---|---|---|---|---|
| b3a residual momentum | +123.6% | −32.6% | 0.88 | less than half of m2's return |
| b3b + graded gate | +110.1% | −25.3% | 0.91 | — |
| b3c in champion structure | +147.8% | −22.3% | 1.07 | best resid variant, still far below b2d's 1.32 |
| b1d @ ₹10k/slot (₹2.5L capital) | +254.0% | −28.2% | 1.19 | charges 5.6% of gross P&L |
| b2d @ ₹10k/slot (₹2.5L capital) | +266.2% | −24.6% | 1.30 | ₹2.5L → ₹9.16L in 5y |

Residual momentum is the campaign's clearest negative surprise: the most
EM-validated signal upgrade in the literature underperforms plain momentum
by >150pp here. Plausible mechanism: 2021-26 NSE returns were dominated by
high-beta broad rallies — stripping the market component removes most of
what our momentum was actually harvesting. Signal work is closed; b2d
stands as champion. Retail-size check passed: both marked strategies hold
their profile at ₹10k/position (integer-share slot misses cost ~15-25pp
over 5y, charges stay ~5% of gross).

# Accuracy-relevant assumptions

Every assumption that affects backtest/paper/live correctness is recorded
here, per CLAUDE.md rule 10. Each entry names the module that owns it.
When an assumption changes, update the owning code and this file together.

## Time and calendars

- **All timestamps are timezone-naive and interpreted as IST (Asia/Kolkata)**
  everywhere in the platform (`core/models.py`, `core/timeutils.py`). Kite
  returns IST; we strip the offset once at the ingestion boundary and never
  re-attach it.
- **Kite bar timestamps are bar-OPEN times.** A daily bar dated D is complete
  (fully knowable) at D 15:30 IST; a minute bar stamped T covers [T, T+1min)
  and is complete at T+1min (`engine/dataview.py::bar_completion_time`).
- **"52 weeks" / "one year" = 252 trading days**, and volatility is
  annualized with sqrt(252) (`strategies/signals/factors.py`). Trading-day
  approximations, not calendar conversions.

## Data adjustment and corporate actions

- **Kite historical candles are assumed split/bonus-adjusted at source.**
  `data/store.py::load_market_data(adjusted=True)` therefore falls back to
  raw bars (with a warning) when adjusted parquet is missing. This fallback
  would NOT be safe for an unadjusted vendor. The `data doctor` unadjusted-
  jump check (>40% overnight gap) exists because this assumption is
  validated, never trusted silently (`data/doctor.py`).
- **Raw market data is immutable.** Adjusted series are derived and stored
  separately; raw parquet is never rewritten (`data/store.py`).
- **Total-return series**: `total_return_close` chain-links cash dividends
  back into close (`data/actions.py`). Factor signals prefer this column
  when present and silently fall back to plain `close` when absent
  (`strategies/signals/factors.py::_price_series`) — momentum computed on
  frames without dividend data is price-return momentum, slightly
  understating total-return momentum for dividend payers.
- **Delisting exit**: a held symbol whose data ends mid-backtest is exited
  at its last traded close minus a configurable haircut, default 20%
  (`config/schemas.py::DelistingSpec`, event engine).

## Universe / survivorship bias

- Universes resolve from the point-in-time membership table. When PIT data
  is missing for the requested period, the run **must carry a loud
  survivorship-bias warning** in `BacktestResult.warnings`
  (`engine/base.py::StaticUniverseResolver`); results with that warning
  overstate performance and must not be trusted for go-live decisions.

## Costs (costs/model.py, costs/schedules/*.yaml)

- Charge schedules are **dated and immutable once committed**; charge
  changes create a new schedule file, never edit an old one.
- Component amounts use Decimal with **ROUND_HALF_UP to the paisa per
  component**, matching how Zerodha's brokerage calculator displays numbers.
  **Per-contract-note whole-rupee rounding of STT/stamp duty is NOT
  modeled** — real contract notes may differ by up to ~₹1 per note.
- **DP charge** (delivery sells) applies once per scrip per sell day
  (₹15.93 incl. GST in `zerodha_2026`); callers must pass
  `first_sell_of_scrip_today=False` for repeat same-day sells of a scrip.
- GST (18%) applies to brokerage + exchange transaction charges + SEBI
  charges only.
- **STCG tax line in reports is informational only** (default 20%,
  `config/schemas.py::CostSpec.stcg_tax_rate`) — no holding-period
  classification (STCG vs LTCG) is modeled.

## Signals and look-ahead prevention

- Row *t* of any registered signal/filter may use only rows ≤ *t* of its
  input frame. This is certified mechanically for **every** registered
  signal and filter by `tests/strategies/test_lookahead_detector.py`
  (truncation probes), not assumed from code review.
- Signals are precomputed over full history for speed and then sliced
  through `DataView`'s visibility cutoff; precomputation cannot leak the
  future *given* the per-signal causality certification above
  (`engine/dataview.py`).
- **Excluded as non-causal** (`strategies/signals/builtin.py`): ichimoku's
  chikou span (row t holds close[t+kijun]); DPO's default centered mode
  (the wrapper always forces `centered=False` and a YAML cannot re-enable
  it).
- **Multi-output pandas-ta indicators are unpacked by column POSITION**,
  not name (names embed parameter values, e.g. `MACD_12_26_9`). Stable
  across parameter overrides for `pandas_ta_classic` 0.6.x; re-verify
  column order on any library upgrade (`strategies/signals/builtin.py`).
- `bbands` registers with `length=20, std=2.0` (conventional Bollinger
  parameters), overriding the library's non-standard `length=5` default.
- `vwap` on daily bars degenerates to the day's typical price
  (high+low+close)/3 because anchoring is per calendar day; it is only
  informative on intraday bars.
- `realized_vol` is computed on plain `close` (price vol), not on
  total-return close — dividends are a level shift, not noise.
- `risk_adjusted_momentum` yields NaN (never ±inf) where the vol
  denominator is NaN or exactly 0 (flat price series).
- `return_smoothness` is **negative information discreteness**
  (Da–Gurun–Warachka): zero-return days count as neither up nor down; a
  smooth downtrend also scores high — trend *direction* is carried by the
  momentum term of a composite score, not by this factor.
- **Deferred:** `beta` and `residual_momentum` vs an index are not
  registered — a signal fn receives only its own symbol's frame today;
  benchmark-frame routing is an engine-level concern. A YAML referencing
  them fails loudly with `ConfigError: unknown signal`.

## Execution simulation (event engine)

- Default execution timing: signals computed on data through close(T)
  affect fills at **T+1 open** (`config/schemas.py::ExecutionSpec`,
  `same_close` available for EOD-execution simulation).
- Order quantities are computed from the **last visible close**, not the
  (unknowable) next open; the fill price is next open ± slippage.
- Default slippage when a strategy doesn't override: the cost schedule's
  conservative `other_bps` (25 bps) for all symbols — large-cap
  classification (10 bps tier) is deferred until an index/market-cap
  table exists at engine level.
- Partial fills: per bar, at most `max_participation` (default 5%) of bar
  volume fills; the remainder stays working and is retried on subsequent
  bars until filled or cancelled by the next rebalance (cancel-and-replace).
- `gross_equity` = net equity + cumulative costs paid so far — the standard
  add-back approximation (assumes identical fills with and without costs).
- Execution prices are rounded to the paisa; **NSE tick-size (₹0.05) rounding
  is not modelled**.
- **No intraday settlement or margin model**: within a bar, sells are
  processed before buys so rebalance proceeds fund the same bar's purchases;
  sizing caps total exposure at 100% (no CNC leverage), so cash cannot go
  meaningfully negative. `fixed_fractional` sizing is applied literally with
  no total-exposure cap — keeping `k × fraction ≤ 1` is the user's job.
- **Rebalance calendar**: weekly/monthly/quarterly fire on the Nth trading
  day of each calendar period on the engine's own trading calendar, clamped
  to the period's last day when the period is shorter than N (a partial
  first period still trades).
- **Overlay vs rebalance precedence**: on a rebalance day, stop exits queued
  at that close are cancel-and-replaced by the rebalance decision (the
  rebalance re-decides the whole book); the drawdown kill switch always wins
  and skips the rebalance. Between rebalances, stops execute at next open.
- **Delisting fills carry normal sell charges but no slippage** (the haircut
  already penalizes the exit).
- **Minute timeframe is stubbed** in the event engine
  (`NotImplementedError`); daily bars only for now.

## Vectorized (fast) engine (engine/vectorized/engine.py)

- The fast engine shares the event engine's calendar, rebalance schedule and
  decision pipeline; only execution differs. **Fills land at the SAME bar's
  close as the rebalance decision** (vs the event engine's default T+1 open);
  no order book, no partial fills, no participation cap, no overlays, no
  delisting model. Every run's warnings list declares this and mandates
  event-engine validation before paper/live.
- Charges are computed per simulated order through the same `CostModel` /
  `ChargeCalculator` seam (never re-implemented); net equity = cost-free
  gross simulation − cumulative charges. The cost drag on buying power is
  NOT compounded into sizing — the source of the small (≈0.2–0.7%) measured
  reconciliation gap vs the event engine.
- Integer shares via vectorbt `size_granularity=1`; sells fund same-bar buys
  (`cash_sharing` + `call_seq="auto"`), matching the event engine's
  sells-before-buys convention.
- Close panels are forward-filled across missing bars (a suspended symbol is
  marked and, at a rebalance, filled at its last stale close); leading NaNs
  before a symbol's first bar are back-filled but can only multiply zero
  positions — the decision pipeline never assigns weight to a symbol with no
  visible bars, so no future price reaches a valuation or an order.
- `result.trades` is empty for fast-engine runs; `total_costs` is
  authoritative at portfolio level only.
- Engine reconciliation is asserted by `tests/engine/test_reconciliation.py`
  (same strategy, both engines, same-close/zero-slippage/uncapped): final
  equity within 1%, costs within 5%, curve divergence within 2%.

## Analytics (analytics/metrics.py, dsr.py, montecarlo.py, tearsheet.py)

- Metrics use `equity.pct_change().dropna()` (T = len(equity) − 1 honest
  observations); `BacktestResult.returns` fills the first bar with 0 for
  plotting — the two differ by design.
- **Risk-free rate is 0 by design**; Sharpe/Sortino are excess-of-zero.
  Sortino's downside deviation is the RMS of below-target returns over the
  FULL sample (target 0), not the std over losing days only.
- `max_dd_duration_days` = longest peak-to-recovery underwater stretch in
  calendar days (trailing unrecovered stretch counts to the last bar);
  a monotonically rising curve reports 0.
- Turnover = annualized one-sided: (Σ entry notional + Σ exit notional)/2 /
  mean(equity) / (T/252). Exposure = mean over bars of open-trade ENTRY
  notional / equity (cost-basis approximation, not marked to market). Both
  assume positive round-trip quantities (long-only CNC); revisit for shorts.
- Alpha/beta: benchmark is a PRICE/LEVEL series (aligned to the equity
  index, then differenced); OLS beta = cov/var, alpha annualized ×252; NaN
  when overlap < 3 bars. Trade-derived metrics are NaN for fast-engine runs
  (empty trades).
- Metrics never return ±inf — undefined quantities are NaN; degenerate
  equity (0–1 bars) yields a full-NaN dict, never an exception.
- **DSR/PSR units** (dsr.py): all Sharpe quantities PER-PERIOD
  (non-annualized); kurtosis NON-EXCESS (normal = 3). SR0 uses the paper's
  closed-form expected-max estimator; anchor test verified by hand:
  DSR = 0.9004 for the Bailey–López de Prado worked example. A radicand
  ≤ 0 (extreme skew/kurtosis) yields NaN, flagged not faked.
- Monte Carlo drawdown bands: `p5` is the WORSE/deeper tail; per-call
  seeded `numpy.random.Generator`, never global seeding.
- Report layer: the STCG line is informational only —
  `stcg_tax_rate × max(final net equity − capital, 0)` over the whole
  window, no holding-period (STCG/LTCG) classification. The monthly-returns
  heatmap's first calendar month is a partial-period return measured from
  the curve's first observation.

## Rate limiting (data/ratelimit.py)

- Kite historical API: 3 requests/second token bucket. `acquire()` treats a
  token balance within 1e-9 of the requested amount as sufficient — exact
  refills of `wait * rate` tokens can land one float ULP short, which would
  otherwise busy-spin (equivalent tolerance: ~0.3 ns of accrual at 3 rps).

## Testing

- Tests never call live APIs. Market data in tests is deterministic
  synthetic OHLCV (geometric Brownian motion, seeded per symbol) from
  `tests/fixtures/synthetic.py`.
- Critical financial math (returns, costs, sizing) is verified by
  hand-computed known-answer tests, with the arithmetic written out in
  comments next to the expected literals.

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
- **`data sync` stores COMPLETED bars only** (`data/sync.py`). Kite serves
  the still-forming candle for the in-progress period, and the raw store is
  append-only and never re-fetched — a forming daily bar written intraday
  would stay permanently wrong, and a forming minute bar would brick the
  next sync with an immutability conflict. Daily fetches are therefore
  clamped to the previous day until 15:30 IST; minute bars whose completion
  time (ts + 1min) is still in the future at fetch time are dropped before
  the write.
- **Embedded NSE holiday table covers 2015–2026 only** (`data/calendar.py`);
  2024 includes the two election holidays and Muharram (05-20, 07-17,
  11-20). Outside covered years the calendar degrades to weekday-only logic
  and logs a loud once-per-year WARNING; `data doctor` demotes missing-day
  findings in uncovered years from error to warn (a "missing" weekday there
  may simply be an unknown holiday). Extend coverage with
  `<data_dir>/nse_holidays.csv`.
- **Minute-session completeness** (`data/doctor.py`): every stored minute
  session is expected to hold exactly 375 bars (09:15–15:29). The first
  stored session (listing-day partial) and today (an intraday sync
  legitimately holds a partial session) are exempt; other deviations warn.
- **"52 weeks" / "one year" = 252 trading days**, and volatility is
  annualized with sqrt(252) (`strategies/signals/factors.py`). Trading-day
  approximations, not calendar conversions.

## Data adjustment and corporate actions

- **Kite serves candles adjusted AS OF FETCH TIME — this does NOT make the
  stored raw series adjusted.** In an append-only store, rows fetched before
  a split/bonus keep the old price scale forever, while rows fetched after
  arrive on the new scale: after any price-affecting action the raw series
  is MIXED-SCALE until `data adjust` rebuilds the adjusted set from the
  recorded actions. (Corollary — double-adjust hazard: never re-import Kite
  history fetched post-action into a store whose corporate-actions table
  already covers that action; the source-adjusted rows would be
  back-adjusted a second time. `write_raw`'s immutability conflict is the
  guard that surfaces such a re-import.) Consequences in
  `data/store.py::load_market_data(adjusted=True)`:
  - raw fallback when no adjusted series exists is allowed (with a warning)
    ONLY when no price-affecting corporate action is recorded for the
    symbol — then raw == adjusted under recorded knowledge;
  - with recorded price actions but no adjusted series, the read RAISES
    `DataError` (serving mixed-scale bars would silently corrupt every
    backtest) and points at `platform data adjust`;
  - every adjusted series carries a sidecar record of the action-set
    signature it was built from (`build_adjusted` →
    `write_adjustment_meta`); serving an adjusted series whose signature no
    longer matches the corporate-actions table logs a loud STALE warning.
  The `data doctor` unadjusted-jump check (>40% overnight gap) still runs on
  raw data, and `data adjust` runs `validate_adjustments` over each freshly
  rebuilt adjusted series — a gap that survives adjustment means a
  missing/incorrect action and is printed as a `review:` line.
- **Raw market data is immutable.** Adjusted series are derived and stored
  separately; raw parquet is never rewritten (`data/store.py`).
- **Symbol reuse**: NSE reassigns tradingsymbols; `token_for` resolves a
  reused symbol deterministically to the ACTIVE / most-recent listing
  (greatest `last_seen`, then `first_seen`, then id —
  `data/instruments.py`).
- **Symbol renames**: `platform data migrate-symbol OLD NEW` relocates raw
  history (append-only merge when both names hold bars), re-keys corporate
  actions/dividends, rebuilds the adjusted series and records the rename in
  the SymbolChange table. Point-in-time universe MEMBERSHIP rows are NOT
  migrated — membership is recorded under the name the index used at the
  time; a renamed symbol appearing in a historical universe must be resolved
  through the SymbolChange table by the caller.
- **`snapshot_id` includes adjustment state** (`data/store.py`): the store
  fingerprint hashes raw extent AND the adjusted close-column content per
  symbol, so two stores with identical raw data but different adjustment
  passes never share a snapshot id (protects signal caches and experiment
  provenance from serving results computed on differently-adjusted data).
- **Total-return series**: `total_return_close` chain-links cash dividends
  back into close (`data/actions.py`). Factor signals prefer this column
  when present and silently fall back to plain `close` when absent
  (`strategies/signals/factors.py::_price_series`) — momentum computed on
  frames without dividend data is price-return momentum, slightly
  understating total-return momentum for dividend payers.
  `BarStore.load_market_data` derives the column at load time for daily
  frames of symbols with dividend records (never persisted — raw and
  adjusted parquet stay pure OHLCV, hard rule 8). Dividend amounts are
  applied at their recorded per-share rupee value against the loaded
  (usually split-adjusted) close: a dividend whose ex-date precedes a later
  split is NOT rescaled by that split's factor, slightly overstating the
  dividend yield of pre-split bars. Also note the chain-link anchors at the
  first loaded bar, so a `start`-clipped load reproduces total returns only
  from that bar onward (relative ranking, which is what factors consume, is
  unaffected).
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
- Filters follow the same pattern since Jul 2026: `FilterStore`
  (`engine/dataview.py`) computes each (filter, params, symbol) series once
  per run and `_apply_filters` reads the value at `now` through the same
  visibility cutoff — equivalent to recomputing on the truncated frame
  *given* filter causality (parity + call-count tests in
  `tests/engine/test_filter_store.py`).
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
- **Overlay vs rebalance precedence — risk exits win**: a rebalance's
  cancel-and-replace (`cancel_for_rebalance`) cancels working BUYs and
  rebalance-tagged sells but PRESERVES risk-exit sells (any SELL not tagged
  "rebalance": trailing stops etc.), and a symbol with a pending risk exit
  receives no rebalance order that bar — no competing sell (oversell), no
  same-bar re-buy fighting the stop. It is flat and re-selectable from the
  next rebalance onward. (The previous semantics — the rebalance
  cancel-and-replacing same-close stop exits — meant overlays could never
  act on daily-rebalance strategies; a 50-stock × 5-year daily-rebalance run
  produced exactly zero stop exits.) The drawdown kill switch always wins
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

## Walk-forward & robustness (analytics/walkforward.py, robustness.py)

- Walk-forward windows tile the calendar: train [k·test, k·test+train), test
  the next test_bars, step = test_bars. Selection uses ONLY the train window;
  the final partial test window is evaluated (real OOS data is never thrown
  away). Engines warm indicators up on pre-window (past) data — that is
  correct, not a leak.
- The stitched OOS curve chain-links each test segment's RETURNS from
  base.capital (levels are discarded); each seam is a genuine flat cash bar
  (every test run restarts from cash). OOS trade-derived metrics are NaN by
  construction. Windows where every variant scores NaN are skipped and leave
  an honest gap.
- Robustness is a ONE-AT-A-TIME ±step neighborhood (not a cartesian grid);
  int perturbations that collapse onto the base value are skipped; invalid
  or erroring perturbations are recorded as rows, never raised. The
  fragility flag (worst neighbor < 50% of base score) is only meaningful for
  a positive base score — otherwise False with an explanatory note.

## Experiments (experiments/, cli/experiments_cmds.py)

- **Train/holdout split**: train_end = (max bar ts − holdout_years × 365.25
  calendar days), tightened per variant to its own config.end if earlier.
  Train runs execute clamped to end=train_end; `config_json` stores the
  UNCLAMPED config and the `train_end` column records the clamp. The holdout
  window is [train_end + 1 day, config.end].
- **Holdout lockout**: `score_holdout` is the only door to the holdout
  window. The quota (default 3 accesses per family) is checked BEFORE any
  scoring — no partial scoring past it; every access writes a HoldoutAccess
  audit row and a WARNING log. A FAILED holdout run still consumes quota
  (the access happened). The check-then-insert is not atomic across
  concurrent processes, and max_evals is caller-supplied — the lockout is a
  discipline guard for a single user, not a security boundary.
- **DSR is computed at query time, per family, never stored** (it depends on
  the family's trial count N, which grows). n_trials counts non-holdout DONE
  runs; per-period Sharpe = sharpe/sqrt(252); sr variance across trials is
  ddof=1 over the finite per-period Sharpes (< 2 finite → DSR NaN);
  `ret_kurt` is stored non-excess (normal = 3).
- A failing grid variant is recorded as status="error" and never aborts the
  grid. Workers receive primitives only and reload data from the store (no
  frame pickling); all DB writes happen in the parent process.
- `code_git_hash` records HEAD of the enclosing repository — coarse
  provenance (the platform lives in a subfolder of a larger repo).
- Direct-script callers of `run_grid` with parallel > 1 must guard with
  `if __name__ == "__main__":` (spawn semantics).

## Paper trading (paper/, broker/risk.py, broker/killswitch.py)

- **Whole-order fills only.** A paper order either fills in full against a
  matching quote or stays working — no partial fills / volume participation
  (a single last-traded tick carries no reliable resting-depth signal; the
  backtest engine does model participation).
- **Fill prices**: market BUY at `round(ask·(1+slip), 2)`, market SELL at
  `round(bid·(1−slip), 2)`, falling back to last-traded when depth is absent.
  Slippage default = the cost schedule's non-large-cap bps unless overridden.
  LIMIT orders fill at the limit exactly (no extra slippage), touch mode by
  default (last ≤/≥ limit fills; "cross" requires strictly through). SL /
  SL-M are rejected at placement ("not supported in paper") — no intrabar
  path exists to trigger a stop off one tick.
- **No T+1 settlement**: a CNC buy can be sold the same day (Zerodha would
  block this). Long-only CNC — oversell is rejected pre-trade.
- **Immediate matching requires a same-day quote.** An order placed while
  the last known quote is stale (previous session) rests OPEN and matches on
  the day's first tick for its symbol — filling a market order at
  yesterday's close would be systematically wrong across overnight gaps; the
  first tick of the day is the paper analogue of "at the open" (mirrors the
  backtest's signals-at-close-of-T → fill-at-T+1-open). The stale quote is
  still used as the pre-trade risk/cash *estimate* (best reference
  available pre-open). The scheduler's session-open job therefore runs as an
  idempotent retry window (each minute 09:15–09:25) rather than a single
  09:15 shot that could beat the day's first ticks.
- **Working orders reserve what they commit** (mirrors Zerodha blocking
  funds/stock at placement): the BUY cash check runs against cash minus
  working-BUY commitments (limit value for LIMIT, latest-quote estimate for
  a resting MARKET, plus estimated charges); the oversell guard against
  holdings minus resting SELL quantity. Because a resting MARKET's
  reservation is only an estimate, a fill whose actual cost exceeds cash at
  match time is REJECTED then (like a real margin shortfall) — the ledger
  can never go negative.
- **Session close marks to the day's official closes** (last completed bar
  ≤ 15:30) before the 15:30 equity snapshot and target sizing, so a
  replayed broker that saw no ticks (report-only / `--once` runs) never
  values positions at stale fill prices.
- **`place_planned` is per-order fault tolerant**: a risk-rejected planned
  order is skipped (persisted REJECTED), one with no price reference stays
  PENDING for a later retry, and an engaged kill switch halts the batch
  (remainder stays PENDING).
- **Restart safety**: positions/cash are never stored — they are rebuilt by
  replaying the append-only fill log through the same `Ledger` used by the
  event engine (charges read off stored fills, never recomputed). A fill and
  its order's post-fill state are persisted in ONE SQLite transaction — a
  crash can never leave a replayable fill beside a still-OPEN order row
  (which would double-fill after restart). The ChargeCalculator's
  once-per-scrip-per-day DP bookkeeping is re-warmed from the last fill day.
- **Day-start equity** (the max_daily_loss basis) is snapshotted lazily at
  the day's first activity, stamped 09:15, exactly once — a mid-day restart
  never overwrites the day's baseline.
- **Risk checks** are inclusive-pass (only strictly-over violates), checked
  in order: restricted symbol → trading day/market hours → orders-per-day →
  order value → daily loss (BUYs only; SELLs always de-risk) → position %
  of equity post-order (BUYs only). Rejected orders are persisted REJECTED
  (they count toward the day's order tally) and the violation re-raised.
- **Modifications are re-validated like fresh placements** (Zerodha re-runs
  its checks on modify): the risk rules, the BUY cash check and the SELL
  oversell guard all run against the modified values, with the order's OWN
  current reservation excluded from working-order commitments (it is being
  replaced, not added). The orders-per-day rule is skipped — a modification
  is not a new placement. A violating modification raises and leaves the
  order working exactly as previously accepted.
- **PaperBroker is thread-safe via one reentrant lock** over every public
  entry point: in `--schedule` mode the websocket thread (`on_tick`) and the
  APScheduler job threads (`place_planned`, `mark_to_market`, `snapshot`)
  share the broker, and check-then-mutate sequences (cash check → fill) must
  not interleave. Consequence: a synchronous Telegram alert inside a fill
  holds the lock for up to its 5 s timeout, stalling other threads too.
- **A close-job re-run cancels its own stale queue entries**: planned
  (PENDING, tag="rebalance") orders for the next open that the freshly
  computed delta set no longer contains are CANCELLED (a symbol that dropped
  out — or flipped side — would otherwise still fire at the open alongside
  the new orders). Re-issued ids are upserted; orders queued by anything
  other than the runner are never touched.
- **Kill switch** is file-presence-based and shared across processes; a
  corrupt/unreadable file still counts as engaged (presence, not content,
  is the signal).
- **Ticks**: bid/ask come from the first market-depth level (None if absent
  or zero); tick ts from `exchange_timestamp`, falling back to
  `last_trade_time`, then wall clock, normalized to tz-naive IST. Ticks are
  persisted append-only as per-day Parquet parts. `on_tick` exceptions are
  logged, never kill the stream. 3000 instruments/connection (Kite cap)
  enforced.
- **Telegram alerts** never raise and are bounded by a 5 s HTTP timeout, but
  are sent synchronously inside the fill path — a Telegram outage can delay
  tick processing by up to that timeout per fill. Disabled unless both bot
  token and chat id are configured.
- **EOD divergence** joins paper and reference equity on common *dates*
  (inner join; last snapshot wins within a day); returns are `pct_change`
  of the joined series; `cum_diff_pct` normalizes both curves to their first
  common date. Paper gross equity = net equity + as-of-aligned cumulative
  fill charges (same identity as the event engine).
- **The paper equity curve is collapsed to one point per day** (each day's
  last snapshot, original timestamp kept) before it enters `BacktestResult`
  / `compute_metrics`: the store holds ~2 snapshots per trading day (09:15
  day-start risk baseline + 15:30 close) but all metric arithmetic assumes
  one equity point per trading day (252/yr annualization) — the raw
  snapshot pairs would double the period count and distort every annualized
  metric.

## Live broker (live/broker.py)

- **`dry_run` defaults to `True`.** Going live is always an explicit opt-in
  (`dry_run=False`). In dry-run, order-*mutating* Kite calls (place / modify /
  cancel) are NOT issued: the intent is journalled (order goes OPEN with a
  synthetic `broker_order_id="DRY-<n>"`) and the exact `kite.place_order`
  kwargs are appended to the public `intended_calls` list for the CLI to print.
  Read calls (ltp / quote / positions / holdings / margins / orders) DO still
  run in dry-run so the full pre-trade pipeline is exercised against real
  account state. Every suppression is logged with a `DRY-RUN:` prefix at
  WARNING level.
- **Idempotency / never double-place — write-ahead journal.** The placement
  intent is journalled (OPEN, deterministic tag, `broker_order_id=None`)
  BEFORE `kite.place_order` is called; the returned id is persisted after. A
  crash anywhere in that window leaves an *unconfirmed* row (OPEN, no broker
  id) that is resolved against the Kite order book **by tag** — at broker
  startup, inside `sync_orders`, and at the `place_order` idempotency gate —
  instead of being re-placed blind: found → adopt id/status/fills; confirmed
  absent → roll back to PENDING (+ risk alert) for retry, or place for real
  when resolution happens at the idempotency gate; order book unreadable →
  the row stays unconfirmed and BLOCKS any re-place. For every other
  non-PENDING journal state, `place_order` returns the stored order verbatim
  with NO API call — except a non-terminal `DRY-<n>` intent in live mode,
  which is superseded by a real placement (a morning dry-run rehearsal must
  not consume the day's real orders). The journal (the reused paper SQLite
  schema, keyed on `settings.live_db_path`) is the single source of "did we
  already send this?".
- **Reconciliation tag.** Kite order *tags* are capped at 20 alphanumeric
  characters, shorter than our 16-hex `client_order_id`, so the tag is derived
  as `sha1(client_order_id).hexdigest()[:18]` (18 lowercase-hex chars,
  deterministic, ≤20). `place_order` records both the returned
  `broker_order_id` and this tag on the journal row; `sync_orders` matches
  `kite.orders()` rows to journal orders by `broker_order_id` first, by tag as
  a defensive fallback.
- **Charges are ESTIMATES until contract-note ingestion.** A fill journalled by
  `sync_orders` on a newly-COMPLETE order carries a cost estimate from
  `CostModel.order_charges(side, product, value).total` (the single charge
  seam) evaluated at the broker's `average_price` — NOT the broker's actual
  contract-note charges (STT/stamp are whole-rupee-rounded per note, etc.).
  The estimate IS date-aware (`trade_date` = fill date picks the charge
  schedule in force) and dedupes the once-per-scrip-per-day DP charge against
  the same day's already-journalled sell fills (restart-safe). Live P&L that
  leans on `Fill.charges` is therefore approximate until contract notes are
  ingested (future work). **Fills are recorded only at a terminal
  transition**, for the not-yet-covered filled quantity: a COMPLETE order
  emits one Fill for the full quantity; a CANCELLED/REJECTED order with
  `filled_quantity > 0` (partial-then-terminal) emits a Fill for the filled
  part — owned shares are never invisible to the ledger. PARTIAL states
  update `filled_qty` only (no interim Fill); the covered-quantity delta
  keeps re-syncs idempotent.
- **Kite status mapping** (`kite.orders()[i]["status"]` → `OrderStatus`):
  `COMPLETE`→COMPLETE, `REJECTED`→REJECTED, `CANCELLED`→CANCELLED; every other
  (OPEN-ish) status — `OPEN`, `TRIGGER PENDING`, `VALIDATION PENDING`,
  `PUT ORDER REQ RECEIVED` and any *unrecognised* non-terminal status — maps to
  OPEN, except an OPEN-ish status with `filled_quantity > 0` maps to PARTIAL.
  Unknown statuses are deliberately treated as still-working, never terminal
  (fail safe: never silently drop an order). `sync_orders` is idempotent via
  the covered-quantity delta (a second sync never re-records a fill).
  Journal-terminal rows are normally skipped, with one deliberate exception:
  a journal-CANCELLED row whose Kite row shows COMPLETE or a larger
  `filled_quantity` is re-processed — the cancel/fill race self-heals (status
  corrected as a journal correction, missing fill recorded) instead of the
  filled shares staying invisible behind a terminal skip.
- **Equity** = `margins.cash_available` (Kite `available.live_balance`, falling
  back to `available.cash`) + Σ(qty·last_price) over holdings + Σ(qty·last_price)
  over positions, `last_price` falling back to `avg_price` only if the broker
  omitted it. Holdings and positions never overlap for the CNC delivery flow,
  so there is no double-counting. Holdings qty = `quantity + t1_quantity` (T1
  shares bought yesterday are ours and back a sell).
- **No local cash / oversell guard.** Unlike `PaperBroker`, the live broker
  runs no simulated ledger and therefore no local funds/holdings guard —
  Zerodha enforces margins and long-only holdings server-side and rejects the
  order. Such a rejection surfaces via the exception mapping (BrokerError) at
  placement and via `sync_orders` on reconciliation.
- **Exception mapping.** A `kiteconnect.exceptions.TokenException` on any
  call → `alerter.alert_token_expiry` + `AuthError`; on placement the
  write-ahead row is rolled back to PENDING (a token expiry is refused at the
  auth gate — nothing was placed; re-auth and retry the same idempotent
  `client_order_id`). Any OTHER placement exception is AMBIGUOUS (e.g. a
  timeout after Kite accepted) and is resolved against the order book by tag:
  found → the order IS live, adopt it and return normally; confirmed absent →
  journal REJECTED + `alert_rejection` + `BrokerError`; order book unreadable
  → leave the row OPEN/unconfirmed (blocks blind retry), risk-alert, raise.
- **Cancel marks CANCELLED on request acceptance.** `cancel_order` (and
  `cancel_all_open`, its per-order-fault-tolerant batch form used by the
  kill-switch CLI) marks the journal order CANCELLED once Kite *accepts* the
  cancel request. In the rare cancel/fill race the order may still fill at
  the broker; `sync_orders` reconciles from `kite.orders()` and is the source
  of truth — and (see the status-mapping entry) re-processes a
  journal-CANCELLED row when the broker shows fill evidence, so the race
  self-heals on the next sync instead of hiding behind the terminal skip. A
  never-placed row (PENDING planned / unconfirmed / DRY intent) is cancelled
  journal-only — no Kite call with a `None` or synthetic order id.
- **Day-start equity** (the max_daily_loss basis) is snapshotted into the
  journal lazily at the day's first order, stamped 09:15, exactly once — a
  mid-day restart recognises the existing snapshot and never overwrites it.
  The kill-switch check runs *before* the snapshot, so a halted broker touches
  no Kite API at all.
- `stream_ticks` is not implemented (raises `NotImplementedError` pointing at
  `paper.ticks.TickStreamer`); live tick ingestion is the paper stack's job.
- **Modifications are re-validated like fresh placements** (mirrors the paper
  broker): the kill switch is checked FIRST (an engaged switch blocks modify
  in both paper and live — a qty increase can raise exposure; cancels stay
  allowed because the engage flow depends on them), then the pre-trade risk
  rules run against the modified values before any `kite.modify_order` call;
  a violation raises and leaves the order working exactly as previously
  accepted (no journal write, no API call — the order is still live at the
  broker). Modifying a never-placed/unconfirmed/DRY row raises
  `OrderStateError` in live mode (there is nothing at Kite to modify). The
  orders-per-day rule is skipped (a modification is not a new placement).
  There is no local cash/oversell re-check — Zerodha enforces funds/holdings
  server-side.

## Live reconciliation & session runner (live/reconcile.py, live/runner.py, cli/live_cmds.py)

- **Reconciliation is detection-only** and runs `sync_orders` first; it then
  flags what sync cannot fix: `missing_at_broker` (journal OPEN/PARTIAL with
  no matching kite row — the dangerous direction), `qty_drift` (a matched row
  disagreeing on symbol/side/qty), and `status_drift` (matched pair still
  disagreeing after sync — this is how the cancel/fill race surfaces:
  journal CANCELLED vs kite COMPLETE). Kite rows matching NO journal
  broker_order_id/tag are deliberately NOT flagged — opaque hash tags cannot
  attribute them (another strategy on the same account, or a manual order);
  `unknown_at_broker` is reserved in the contract but never emitted today.
  Journal rows with a synthetic `DRY-<n>` broker id are skipped — a dry-run
  rehearsal must not raise `missing_at_broker` noise on a later live
  reconcile. In dry-run both reconcile passes short-circuit to `[]` with zero
  Kite calls.
- **One consolidated Telegram alert per reconcile pass** listing every
  mismatch — never one alert per mismatch (a drifted book must not flood).
- **The live planned-order queue lives in the runner, not the broker**
  (`ZerodhaLiveBroker` has no queue API): the runner reads/writes the same
  journal store (`save_order(planned_for=…)` / `planned_orders(day)`) and
  replicates paper's per-order fault tolerance at the open (kill switch halts
  the batch; risk rejection skips; broker/auth errors leave PENDING for the
  09:15–09:25 retry window). A LIVE session reads the queue with
  `planned_orders(day, include_dry_placed=True)`, so planned rows a morning
  dry-run rehearsal marked OPEN/`DRY-<n>` are still handed to the broker
  (which supersedes the dry intent with a real placement) — the runbook's
  "dry-run first, then --live" procedure places the day's real orders.
- **Cancelling a stale planned (never-placed) order is journal-only**: it has
  no `broker_order_id`, so it is transitioned CANCELLED directly on the store
  row — routing it through `broker.cancel_order` would hit the Kite API for
  an order that was never placed.
- **Live's session close now snapshots the day's close equity into the
  journal** (`LiveSessionRunner._snapshot_close_equity`, called from
  `on_session_close`), exactly mirroring `PaperBroker`'s close snapshot, so
  the live journal accumulates the same daily equity curve paper's does. It
  reads equity before margins so a margins-only failure still leaves a
  usable equity value on hand for sizing — the snapshot itself needs both
  and is skipped (logged, non-fatal) if either read fails; the close
  evaluation reuses the already-fetched equity rather than reading it a
  second time. `cli/live_cmds.py`'s `live report <strategy.yaml>` command
  builds an EOD report on demand from that journal by reusing
  `paper/eod.py::run_eod` unmodified — same HTML/JSON output paper gets,
  under `<artifacts_dir>/paper/<strategy.name>/`. Charges inside that report
  are `sync_orders`'s `CostModel` **estimates**, not broker-confirmed
  contract-note charges (see the charges assumption above). There is still
  **no automatic report generated in the close job** — unlike paper, which
  writes one on every close, live report generation stays an explicit,
  on-demand CLI action; live's close-job acceptance bar remains order-flow
  correctness (a dry-run session shows the exact intended
  `kite.place_order` kwargs).
- **The reconcile cron job window is enforced in the job body** (trading day
  + 09:15–15:30), not by the cron expression (`hour="9-15", minute="*/5"` is
  a superset that fires outside the session and no-ops).
- CLI safety split: `live status` always builds the broker with
  `dry_run=True` (can never mutate an order); `live reconcile` builds with
  `dry_run=False` (sync against the real book is the point); `live run`
  defaults to dry-run — `--live` is the explicit opt-in and prints a loud
  warning. `live killswitch engage` writes the kill-switch file FIRST, then
  best-effort cancels open orders (auth failure → a clear "handle it in
  Kite's web console" warning, never a crash).

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

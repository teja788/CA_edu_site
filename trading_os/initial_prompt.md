# CLAUDE CODE PROMPT — India Equity Backtesting & Algo Trading Platform

Copy everything below this line into Claude Code. Recommended: run it phase by phase (the plan is at the end), reviewing each milestone before continuing.

---

## ROLE

You are building a production-grade quantitative research and trading platform for **Indian cash equities (NSE)** for a single user. The platform has three lifecycle stages that share one codebase: (1) historical backtesting at scale, (2) paper trading on live market data, (3) live trading via Zerodha Kite Connect. Correctness and absence of bias matter more than speed of delivery. Do not take shortcuts that compromise accuracy.

## HARD REQUIREMENTS

1. **Language:** Python 3.11+. Use type hints everywhere. Use `pydantic` v2 for all configs and data models.
2. **Scope:** NSE cash equities only (no F&O). Both **daily (EOD)** and **minute-level intraday** data must be supported end to end.
3. **Scale:** The system must comfortably run **hundreds of strategy variants** over 10+ years of daily data for a 500-stock universe, and store/compare all results.
4. **Extensibility:** New strategies must be addable without touching engine code — strategies are defined declaratively (config + small plugin classes).
5. **One broker abstraction:** `BacktestBroker`, `PaperBroker`, and `ZerodhaLiveBroker` implement the same interface, so a strategy graduates from backtest → paper → live with a config change only.
6. **No hardcoded credentials.** All secrets via `.env` / environment variables. Add `.env` to `.gitignore` from the first commit.
7. Write **pytest unit tests** for every module as you build it, not at the end. Critical financial math (returns, costs, position sizing) needs known-answer tests verified by hand.

## TECH STACK (use exactly this unless you find a blocking problem — if so, stop and explain)

- **Data/compute:** `polars` (primary) + `pandas` (interop), `numpy`
- **Storage:** Parquet files partitioned by symbol/timeframe + **DuckDB** for querying; SQLite via `sqlmodel` for run metadata, experiment results, orders, and trade logs
- **Vectorized backtests:** `vectorbt` (open-source version) for fast mass parameter scans
- **Event-driven backtests:** custom engine (spec below) — do NOT use backtrader/zipline (unmaintained/poor fit)
- **Broker API:** official `kiteconnect` Python library; `pyotp` for TOTP in the login helper
- **Scheduling:** `APScheduler` for daily jobs (data sync, token refresh reminder, EOD reports)
- **CLI:** `typer`. **Reports:** `quantstats` tearsheets + custom HTML reports with `plotly`
- **Config:** YAML strategy/experiment configs parsed into pydantic models
- **Tooling:** `uv` for env/deps, `ruff` for lint/format, `pytest` + `pytest-cov`

## ARCHITECTURE — MODULES

```
platform/
  config/          # pydantic settings, YAML loaders
  data/            # ingestion, storage, corporate actions, universe
  strategies/      # strategy framework + strategy library
  engine/          # vectorized + event-driven backtest engines
  costs/           # Indian transaction cost & slippage models
  analytics/       # metrics, tearsheets, walk-forward, robustness
  experiments/     # batch runner, results DB, comparison UI/reports
  broker/          # broker abstraction + Kite implementation
  paper/           # paper trading engine on live ticks
  live/            # live trading runner, risk controls, kill switch
  cli/             # typer commands
  tests/
```

---

## MODULE 1 — DATA LAYER (the foundation; get this right first)

### 1a. Kite Connect ingestion
- Auth: Kite access tokens **expire daily**. Build a login helper that opens the Kite login URL, captures the `request_token` from the redirect, exchanges it for an access token, and caches it for the day. Support optional TOTP-assisted flow with `pyotp`. Fail with a clear message when the token is stale.
- Historical candles API constraints — respect them in code:
  - Rate limit: **3 requests/second** for historical API. Build a token-bucket rate limiter.
  - Max span per request: ~2000 days for `day` candles, ~60 days for `minute` candles. Build an automatic **date-chunking** fetcher with retry + exponential backoff.
- Fetch and cache the **instruments dump** daily (maps tradingsymbol ↔ instrument_token). Handle symbol changes over time (maintain a symbol-mapping table).
- Incremental sync: a `data sync` CLI command that tops up all locally stored symbols to the latest candle, both daily and minute.
- Store raw data exactly as received (immutable), and adjusted data separately. Never overwrite raw data.

### 1b. Corporate actions & adjustment
- Kite's historical candles are generally split/bonus adjusted, but you must NOT assume this silently. Build a **validation job** that detects unadjusted jumps (>40% overnight gap without market-wide moves) and flags symbols for review.
- Maintain a corporate-actions table (splits, bonuses, symbol changes, delistings). Source: user-provided CSVs to start; design so a scraper/vendor can be plugged in later.
- Dividends: store separately; total-return calculations must optionally add dividends back (momentum ranking should use total returns where possible).

### 1c. Survivorship bias — CRITICAL
- Backtests must select stocks from the **index constituents as of each historical rebalance date**, never today's list.
- Build a `universe` module: point-in-time membership table (symbol, index, start_date, end_date). Seed it from user-provided historical constituent files (NSE/niftyindices publishes change announcements); provide an importer for CSVs.
- Every backtest run must record which universe definition it used. If point-in-time data is missing for the requested period, the run must **loudly warn** that results carry survivorship bias.
- Handle delisted/suspended stocks: if a held stock is delisted, the engine must exit it at last traded price (configurable haircut, default −20%) rather than silently dropping it.

### 1d. Data quality
- Automated checks on every sync: missing trading days (validate against an NSE holiday calendar you maintain), zero/negative prices, duplicate timestamps, extreme outliers, volume anomalies. Write a `data doctor` CLI command that prints a health report.

---

## MODULE 2 — STRATEGY FRAMEWORK

Strategies are declarative pipelines with these composable pieces:
1. **Universe** (e.g., point-in-time Nifty 500, liquidity filter: min median daily traded value)
2. **Signals / Indicators** — reusable, registered functions computing per-stock time series. Three tiers, all exposed through one uniform registry so strategies reference any indicator by name + params in YAML:
   - **Built-in library:** integrate `pandas-ta` (pure-Python, no C build issues) so the full standard set is available out of the box — RSI, MACD, ADX, ATR, Bollinger Bands, Stochastic, SuperTrend, Donchian, Keltner, OBV, VWAP, ROC, CCI, Ichimoku, and 100+ more. Wrap them behind the registry so a strategy YAML says e.g. `{name: rsi, params: {length: 14}}` regardless of the underlying library.
   - **Quant/factor signals (custom):** returns over window, realized volatility, risk-adjusted momentum, distance from 52-week high, return smoothness / information discreteness, beta, residual momentum vs index.
   - **User plugins:** a `signals/custom/` folder where a new indicator = one decorated function (`@register_signal("my_indicator")`) taking OHLCV → series; auto-discovered at startup, immediately usable in YAML, and usable in both engines. Include a template file and a doc page showing how to add one.
   - **Cross-timeframe support:** indicators can be computed on daily data and consumed by an intraday strategy (and vice versa via resampling), with the look-ahead guard enforcing that only completed bars are visible.
   - Indicator values must be computed once per run and cached (keyed by symbol + indicator + params + data snapshot) so 100-combo grids don't recompute identical signals.
3. **Score** — combine signals into a ranking score (weighted z-scores by default)
4. **Filters** — regime filters (e.g., index above 200-DMA), eligibility filters
5. **Selection** — top-N or top-percentile, with buffer zones to reduce churn (e.g., enter at top 25, exit only if drops below rank 40)
6. **Position sizing** — equal weight, inverse volatility, volatility targeting (portfolio-level target vol with exposure scaling), fixed fractional; max position and max sector caps
7. **Rebalance schedule** — monthly/weekly/quarterly on Nth trading day, or event-driven (for intraday strategies)
8. **Risk overlays** — trailing stops (ATR-based, percentage, MA-cross), portfolio kill-switch drawdown level

A strategy = YAML file referencing registered components + parameters. Example to include as `strategies/examples/momentum_composite.yaml`:
- Universe: Nifty 500 PIT, liquidity ≥ ₹2cr median daily value
- Score: 0.5 × z(12-1 month return / realized vol) + 0.3 × z(price / 52wk high) + 0.2 × z(return smoothness)
- Filter: Nifty 50 > 200-DMA else move to cash
- Selection: top 25 with rank-40 exit buffer; equal weight; monthly rebalance; 3×ATR(14) trailing stop on closing basis
Also implement plain 12-1 momentum, dual momentum (index vs liquid-fund proxy), and a 200-DMA trend strategy as reference strategies.

**Look-ahead prevention is a framework guarantee, not a convention:** signals computed on data up to and including day T may only affect orders executed at **T+1 open** (configurable to T close for EOD-execution simulation, but default T+1 open). Build an automated **look-ahead detector test**: shift all input data forward one day and assert results change; inject a synthetic future-knowledge signal and assert the framework blocks it (signals must be produced through an API that only exposes data ≤ current simulation time).

---

## MODULE 3 — BACKTEST ENGINES (two, sharing strategy definitions)

### 3a. Vectorized engine (research/screening)
- Built on vectorbt: run a strategy across large parameter grids fast (e.g., 500 parameter combos over 10y daily in minutes).
- Approximations allowed (bar-close fills), but must still apply the full Indian cost model and record that it's the "fast" engine in results.

### 3b. Event-driven engine (validation/realism) — custom
- Bar-by-bar simulation loop (daily or minute bars): on each bar — update portfolio marks → check stops/risk overlays → generate/execute pending orders with the fill model → log everything.
- Fill model: market orders fill at next bar open + slippage; limit orders fill if price crosses; configurable slippage = max(fixed bps, impact model scaled by order size vs bar volume; default 10 bps large caps / 25 bps beyond Nifty 100 — put in config).
- Cash accounting to the paisa, including all charges per fill. Partial fills when order size > X% of bar volume (default 5%).
- Every promoted strategy must be validated on the event-driven engine before paper trading. Build a **reconciliation test**: same simple strategy on both engines must produce results within a defined tolerance; investigate if not.

---

## MODULE 4 — INDIAN COST MODEL (config-driven, versioned)

Implement as a dated, versioned config (`costs/schedules/zerodha_2026.yaml`) so charge changes don't require code changes. Include (verify current values against Zerodha's official charges page and cite it in a comment):
- **Delivery (CNC):** brokerage ₹0; STT 0.1% on buy AND sell; exchange transaction charges (NSE ~0.00297%); SEBI charges ₹10/crore; stamp duty 0.015% on buy; GST 18% on (brokerage + exchange + SEBI charges); DP charge per scrip per sell day (~₹15.93 incl. GST).
- **Intraday (MIS):** brokerage min(0.03%, ₹20) per order; STT 0.025% on sell only; stamp 0.003% on buy; same exchange/SEBI/GST logic.
- Unit-test the cost model against 3–4 hand-computed examples from Zerodha's brokerage calculator and document the expected numbers in the tests.
- Every backtest report must show gross vs net returns and total costs as % of capital, plus estimated STCG tax impact (configurable rate, default 20%) as an informational line.

---

## MODULE 5 — ANALYTICS, ROBUSTNESS & MULTIPLE-TESTING DEFENSE

Metrics per run: CAGR, volatility, Sharpe, Sortino, Calmar, max drawdown + duration, hit rate, turnover, avg holding period, exposure, alpha/beta vs Nifty 500 TRI (allow user-supplied benchmark series), monthly/yearly return tables, rolling 1y/3y Sharpe, top-10 drawdowns, per-trade distribution. Generate quantstats HTML tearsheets + a custom plotly report.

Because the user will test **hundreds of strategies**, guard against data-mined false positives:
1. **Mandatory train/holdout split:** default = last 2 years locked as out-of-sample holdout; the experiment runner refuses to score holdout more than a configured number of times per strategy family and logs every access.
2. **Walk-forward analysis:** rolling optimize-then-test windows; report OOS-only aggregated equity curve.
3. **Deflated Sharpe Ratio / multiple-testing correction:** implement DSR (Bailey & López de Prado) using the number of trials recorded in the experiments DB; every leaderboard must show DSR alongside raw Sharpe.
4. **Parameter-neighborhood robustness:** for any candidate, auto-run a ±20% perturbation grid on each parameter and report the performance cliff (a strategy whose Sharpe collapses under small perturbation is flagged).
5. **Monte Carlo:** trade-order bootstrap and skip-a-trade resampling for drawdown confidence bands.

**Experiments module:** batch runner (`experiments run grid.yaml`) that expands parameter grids, runs in parallel (multiprocessing), writes every run (config hash, code git hash, data snapshot id, engine, metrics, artifacts path) to SQLite, and provides `experiments leaderboard` / `experiments compare run1 run2` CLI + HTML comparison report. Every run must be exactly reproducible from its recorded config + data snapshot.

---

## MODULE 6 — BROKER ABSTRACTION + PAPER TRADING

Interface (`broker/base.py`): `place_order`, `modify_order`, `cancel_order`, `get_positions`, `get_holdings`, `get_margins`, `get_quote`, `stream_ticks(symbols, callback)`, with common order/position/fill dataclasses and a clear order state machine (PENDING → OPEN → PARTIAL/COMPLETE/CANCELLED/REJECTED).

**PaperBroker:**
- Subscribes to live ticks via Kite WebSocket (limit: 3000 instruments/connection — enforce) with auto-reconnect and tick persistence (append to Parquet for later analysis).
- Simulates fills against live quotes: market orders fill at best bid/ask ± slippage config; limit orders fill when touched (configurable: touch vs cross).
- Maintains a virtual ledger (cash, positions, full cost model applied) in SQLite; survives restarts.
- Runs a strategy on a schedule identical to how live would run it, and produces a **daily EOD report** comparing paper equity curve vs the backtest expectation for the same period (live/backtest divergence tracking — this is the acceptance test for going live).

**ZerodhaLiveBroker:**
- Thin, heavily-logged wrapper over kiteconnect order APIs. Note in docs: order placement requires a **registered static IP**, and there is **no sandbox** — paper mode is our sandbox.
- Safety features (non-negotiable, all default ON):
  - Global kill switch (file-based flag + CLI command) that cancels open orders and halts new ones
  - Pre-trade risk checks: max order value, max position %, max daily loss, max orders/day, restricted-symbol list, market-hours check
  - Order reconciliation loop: poll order book, detect mismatches between intended and actual state, alert
  - Dry-run mode that logs the exact API calls without sending
  - Idempotency: tag orders with strategy + client order ids; on restart, rebuild state from broker, never double-place
- Alerts via Telegram bot (optional config) for fills, rejections, risk triggers, and token expiry.

---

## MODEL ROUTING & TOKEN EFFICIENCY

The main session (you) runs on the most capable model and acts as **orchestrator and verifier only**: task decomposition, architecture decisions, integration, and mandatory review of accuracy-critical code. Delegate the bulk of the work to project subagents pinned to cheaper models. In Phase 0, create these files in `.claude/agents/` (YAML frontmatter: name, description, tools, model — write keyword-rich descriptions so auto-delegation works):

1. **`implementer`** — `model: sonnet`, tools: Read, Write, Edit, Bash, Glob, Grep. Does the majority of coding: data plumbing, storage, CLI commands, YAML loaders, indicator wrappers, report templates, refactors. Use proactively for any well-specified implementation task.
2. **`quant-engineer`** — `model: opus`, same tools. Reserved for algorithmically complex modules only: event-driven engine core, fill/slippage models, look-ahead guard, walk-forward, Deflated Sharpe, Monte Carlo. Description should say "use for complex quantitative/algorithmic logic".
3. **`test-writer`** — `model: sonnet`, tools: Read, Write, Edit, Bash, Glob, Grep. Writes pytest suites and synthetic OHLCV fixtures from a spec of expected behaviors.
4. **`explorer`** — `model: haiku`, read-only tools (Read, Grep, Glob, WebFetch, WebSearch). Codebase search, dependency/API doc lookups, summarizing files. (Claude Code's built-in Explore agent may cover this; use it if so.)
5. **`docs-writer`** — `model: haiku`, tools: Read, Write, Edit, Glob, Grep. README, assumptions.md, runbooks, docstring passes.
6. **`critical-reviewer`** — `model: inherit` (i.e., the main model), read-only tools. Reviews diffs before commit for: all financial math (returns, costs, sizing), look-ahead prevention, PIT universe logic, order/state machine, and live-trading risk controls.

**Routing rules for you (main session):**
- Never write routine code in the main context — delegate to `implementer` and keep only its summary.
- Anything that touches money math, bias prevention, or live order flow: implemented by `implementer`/`quant-engineer`, then MUST pass `critical-reviewer` before the phase is declared done. Everything else needs tests passing only.
- Keep subagent tasks tightly scoped (one module or one file cluster per delegation) so their contexts stay small; parallelize independent tasks.
- Don't pull large files into the main context; ask `explorer` for targeted summaries instead.

## BUILD PLAN — PHASES WITH ACCEPTANCE CRITERIA (work in this order; stop after each phase for review)

**Phase 0 — Skeleton:** repo layout, uv project, config system, logging, CI-ready pytest, CLAUDE.md describing architecture and conventions, and the six subagent files in `.claude/agents/` per the model-routing section. ✔ `pytest` green, `platform --help` works, subagents visible via `/agents`.

**Phase 1 — Data layer:** Kite auth helper, rate-limited chunked historical fetcher, Parquet/DuckDB store, instruments sync, holiday calendar, data doctor, corporate-actions table, PIT universe importer + API. ✔ Can sync 5 test symbols (daily + minute), data doctor passes, unit tests for chunking/rate limiter/PIT universe queries.

**Phase 2 — Cost model + strategy framework:** full Zerodha cost schedule with hand-verified tests; signal registry; YAML strategy loader; look-ahead-proof data access API + look-ahead detector tests. ✔ Cost tests match brokerage-calculator examples; look-ahead tests pass.

**Phase 3 — Engines:** vectorized engine on vectorbt; event-driven engine; reconciliation test between them; the four reference strategies running end to end on real synced data. ✔ 12-1 momentum backtest (2015→present, Nifty 100 PIT if constituent data provided, else flagged) produces a tearsheet; engines reconcile within tolerance.

**Phase 4 — Analytics + experiments:** full metrics, tearsheets, walk-forward, DSR, perturbation robustness, Monte Carlo; experiments DB, parallel grid runner, leaderboard, comparison reports, holdout lockout. ✔ A 100-combo grid run completes, leaderboard shows Sharpe + DSR, all runs reproducible.

**Phase 5 — Paper trading:** WebSocket streamer with reconnect + tick storage, PaperBroker with virtual ledger, scheduled strategy runner, EOD divergence report, Telegram alerts. ✔ A strategy paper-trades a full session and produces the EOD report.

**Phase 6 — Live trading:** ZerodhaLiveBroker, all safety features, dry-run mode, reconciliation loop, go-live runbook doc. ✔ Dry-run session shows correct intended orders; kill switch and risk checks have tests; runbook written.

## GENERAL INSTRUCTIONS TO YOU (CLAUDE CODE)

- Ask before adding any dependency not listed. Prefer boring, maintained libraries.
- Keep every module independently testable; no circular imports; engine must not import broker.
- Financial math in one well-tested `core` area — never duplicate return/cost calculations.
- Document every accuracy-relevant assumption in `docs/assumptions.md` (fill prices, slippage defaults, adjustment handling, delisting haircut, etc.).
- When real data is unavailable in tests, generate deterministic synthetic OHLCV fixtures — never call the live API from tests.
- If any Kite API behavior differs from this spec (limits, fields, auth), trust the live API and its official docs at https://kite.trade/docs/connect/ — then update `docs/assumptions.md` and tell me what changed.
- After each phase, print a summary: what was built, test coverage, what needs my manual input (e.g., historical constituent CSVs, API keys, static IP setup).

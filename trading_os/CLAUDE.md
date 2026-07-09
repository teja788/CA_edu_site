# tradingos — India Equity Research & Trading Platform

Production-grade quantitative research and trading platform for **Indian cash equities (NSE)**, single user. Three lifecycle stages, one codebase: (1) historical backtesting at scale, (2) paper trading on live data, (3) live trading via Zerodha Kite Connect. **Correctness and absence of bias beat speed of delivery — never take shortcuts that compromise accuracy.**

## Layout

Package is `src/tradingos/` (the spec's `platform/` name shadows the stdlib module; CLI entry point is still `platform`). Modules:

- `core/` — shared models (Order/Fill/Position/Trade, state machine), errors, logging, time utils. All timestamps are **tz-naive IST**.
- `config/` — pydantic-settings env config (`TOS_` prefix, `.env`); YAML strategy/grid schemas + loader.
- `data/` — Kite auth + rate-limited chunked fetcher, Parquet(+DuckDB) store, instruments, corporate actions, holiday calendar, PIT universe, data doctor.
- `strategies/` — signal registry (pandas-ta-classic wrappers + custom factors + auto-discovered plugins in `signals/custom/`), declarative YAML strategies in `examples/`.
- `engine/` — `dataview.py` look-ahead guard (THE safety boundary), event-driven engine (`event/`), vectorbt engine (`vectorized/`).
- `costs/` — versioned Zerodha charge schedules (`schedules/*.yaml`, immutable once dated) + `CostModel` (the ONLY place charges are computed).
- `analytics/` — metrics, tearsheets, walk-forward, Deflated Sharpe, Monte Carlo, perturbation robustness.
- `experiments/` — SQLite (sqlmodel) run registry, parallel grid runner, leaderboard/compare, holdout lockout.
- `broker/` — abstract `Broker` interface (+ Zerodha wrapper in `live/`). Engine must NOT import concrete brokers.
- `paper/`, `live/` — paper broker on live ticks; live runner with kill switch and pre-trade risk checks.
- `cli/` — typer app; run `uv run platform --help`.

## Hard rules

1. Python 3.12, type hints everywhere, pydantic v2 for configs and data models.
2. **No hardcoded credentials.** Secrets only via `.env` / env vars (`TOS_` prefix). `.env` is git-ignored.
3. **Look-ahead prevention is a framework guarantee**: strategy code only sees data through `engine/dataview.py::DataView` (bars ≤ now, completed bars only). Signals: row *t* uses only rows ≤ *t*. Default execution: signals at close of T → orders at T+1 open.
4. **Survivorship bias**: universes resolve from the point-in-time membership table; runs without PIT data must loudly warn.
5. Financial math lives in one place: returns/metrics in `analytics/metrics.py`, charges in `costs/model.py`. Never duplicate. Known-answer tests required.
6. Tests accompany every module (`tests/` mirrors package). Never call live APIs in tests — use synthetic OHLCV fixtures (`tests/fixtures/`).
7. No circular imports. `engine` must not import `broker` implementations, `paper` or `live`.
8. Raw market data is immutable — adjusted data is stored separately; never overwrite raw.
9. New strategies are YAML + registered components only — adding one must not touch engine code.
10. Document accuracy-relevant assumptions in `docs/assumptions.md` as you make them.

## Commands

- `uv sync` — install deps. `uv run pytest` — tests. `uv run ruff check src tests` — lint.
- `uv run platform --help` — CLI. Subcommands: `data`, `backtest`, `experiments`, `paper`, `live`.

## Conventions

- OHLCV frames: pandas (signal seam) or polars (storage seam); columns `ts, open, high, low, close, volume`; per-symbol pandas frames are indexed by tz-naive IST `DatetimeIndex`.
- Kite bar timestamps are bar-open; daily bars complete at 15:30 IST.
- Money: floats rounded to the paisa at ledger/cost boundaries (Decimal inside `CostModel`).
- Logging via `tradingos.core.logging.get_logger(__name__)`; no `print` outside CLI output.

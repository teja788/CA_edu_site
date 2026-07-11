"""backtest CLI commands (typer sub-app).

``platform backtest run STRATEGY.yaml`` loads a declarative strategy, runs it on
either the realistic event engine or the fast vectorized engine, prints a compact
summary and saves a reproducible artifacts bundle (meta.json / equity.parquet /
trades.json). Heavy imports (engines, data store, vectorbt) live inside the
command so ``platform --help`` stays instant.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Annotated

import typer

from tradingos.config.schemas import EngineMode
from tradingos.core.models import Timeframe

app = typer.Typer(no_args_is_help=True)


def _fail(message: str) -> None:
    """Print a clean error to stderr and exit non-zero (never a stack trace)."""
    typer.echo(f"error: {message}", err=True)
    raise typer.Exit(code=1)


@app.command()
def run(
    strategy: Annotated[Path, typer.Argument(help="Path to a strategy YAML file.")],
    engine: Annotated[
        EngineMode | None,
        typer.Option("--engine", help="Override the engine (default: the strategy's own)."),
    ] = None,
    symbols: Annotated[
        str | None,
        typer.Option("--symbols", help="Comma-separated symbols overriding the config universe."),
    ] = None,
    start: Annotated[
        str | None, typer.Option("--start", help="ISO start date override (YYYY-MM-DD).")
    ] = None,
    end: Annotated[
        str | None, typer.Option("--end", help="ISO end date override (YYYY-MM-DD).")
    ] = None,
    timeframe: Annotated[
        Timeframe | None,
        typer.Option("--timeframe", help="Bar timeframe override (default: the strategy's own)."),
    ] = None,
    adjusted: Annotated[
        bool, typer.Option("--adjusted/--no-adjusted", help="Use adjusted bars.")
    ] = True,
    out: Annotated[
        Path | None,
        typer.Option("--out", help="Artifacts dir (default: <artifacts>/runs/<name>-<hash>)."),
    ] = None,
) -> None:
    """Run STRATEGY on the event or vectorized engine and save the artifacts."""
    # -- heavy imports deferred to command invocation ----------------------
    from tradingos.config.loader import load_strategy
    from tradingos.config.settings import get_settings
    from tradingos.core.errors import TradingOSError
    from tradingos.data.store import BarStore
    from tradingos.experiments.runner import make_universe_resolver, resolve_symbols

    # -- load + apply overrides -------------------------------------------
    try:
        config = load_strategy(strategy)
    except TradingOSError as exc:
        _fail(str(exc))

    updates: dict[str, object] = {}
    if engine is not None:
        updates["engine"] = engine
    if timeframe is not None:
        updates["timeframe"] = timeframe
    if start is not None:
        try:
            updates["start"] = date.fromisoformat(start)
        except ValueError:
            _fail(f"invalid --start {start!r}: expected ISO date YYYY-MM-DD")
    if end is not None:
        try:
            updates["end"] = date.fromisoformat(end)
        except ValueError:
            _fail(f"invalid --end {end!r}: expected ISO date YYYY-MM-DD")
    if symbols is not None:
        syms = [s.strip() for s in symbols.split(",") if s.strip()]
        if not syms:
            _fail("--symbols was empty after parsing")
        updates["universe"] = config.universe.model_copy(update={"symbols": syms})
    if updates:
        config = config.model_copy(update=updates)

    # -- resolve which symbols to load ------------------------------------
    settings = get_settings()
    store = BarStore(settings)
    # Same convention as the experiments runner: explicit universe (else every
    # symbol the store holds) plus symbol-routed regime-filter targets. Which
    # of those are CANDIDATES on each rebalance date is decided by the
    # point-in-time resolver below, not here.
    load_symbols = resolve_symbols(config, store, config.timeframe)
    if not load_symbols:
        _fail("no symbols to load: give --symbols, an explicit universe, or sync data first")

    data = store.load_market_data(
        load_symbols,
        config.timeframe,
        start=None,
        end=None,
        adjusted=adjusted,
    )
    if not data.symbols:
        _fail(
            f"no {config.timeframe.value} data found for symbols "
            f"{sorted(load_symbols)} (adjusted={adjusted}); sync data first"
        )

    # -- pick engine + run ------------------------------------------------
    if config.engine == EngineMode.VECTORIZED:
        from tradingos.engine.vectorized.engine import VectorizedEngine

        eng: object = VectorizedEngine()
    else:
        from tradingos.engine.event.engine import EventEngine

        eng = EventEngine()

    # Direct runs get the SAME point-in-time universe resolver as every
    # experiments path (hard rule 4 — survivorship-bias defense): membership is
    # resolved as of each rebalance date, and a run without PIT data falls back
    # to all available symbols with a LOUD warning surfaced in the summary below.
    try:
        result = eng.run(config, data, make_universe_resolver(settings))  # type: ignore[attr-defined]
    except TradingOSError as exc:
        _fail(str(exc))

    # -- summary + save ---------------------------------------------------
    out_dir = out or (settings.artifacts_dir / "runs" / f"{config.name}-{config.config_hash()}")
    result.save(out_dir)

    n_bars = len(result.equity)
    final_eq = float(result.equity.iloc[-1]) if n_bars else config.capital
    final_gross = float(result.gross_equity.iloc[-1]) if n_bars else config.capital
    typer.echo(f"strategy   : {config.name}  ({config.engine.value} engine)")
    typer.echo(f"window     : {result.start} -> {result.end}   bars: {n_bars}")
    typer.echo(f"capital    : {config.capital:,.2f}")
    typer.echo(f"final equity: {final_eq:,.2f}")
    typer.echo(f"gross equity: {final_gross:,.2f}")
    typer.echo(
        f"total costs : {result.total_costs:,.2f}  "
        f"({result.costs_pct_of_capital * 100:.3f}% of capital)"
    )
    typer.echo(f"trades     : {len(result.trades)}")
    if result.warnings:
        typer.echo("warnings:")
        for w in result.warnings:
            typer.echo(f"  - {w}")
    typer.echo(f"artifacts  : {out_dir}")

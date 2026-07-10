"""paper CLI commands (typer sub-app): run a paper trading session (one
manual open+close cycle, or the live Mon-Fri scheduler on real ticks),
rebuild an EOD report on demand, and inspect the current state of a
strategy's paper ledger.

Heavy imports (broker, engine, data store, Kite ticker) are deferred inside
each command so ``platform --help`` stays instant, mirroring
``cli/backtest_cmds.py``.
"""

from __future__ import annotations

import time
from datetime import date
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(no_args_is_help=True)


def _fail(message: str) -> None:
    """Print a clean error to stderr and exit non-zero (never a stack trace)."""
    typer.echo(f"error: {message}", err=True)
    raise typer.Exit(code=1)


def _load_config(strategy: Path):
    from tradingos.config.loader import load_strategy
    from tradingos.core.errors import TradingOSError

    try:
        return load_strategy(strategy)
    except TradingOSError as exc:
        _fail(str(exc))


def _universe_symbols(config, bar_store) -> list[str]:
    """Same universe-symbol resolution as ``cli/backtest_cmds.py`` /
    ``paper/runner.py``: explicit universe symbols, else everything the store
    holds, plus any symbol-routed regime filter target."""
    symbols: set[str] = set(config.universe.symbols or [])
    if not symbols:
        symbols = set(bar_store.symbols(config.timeframe))
    for fspec in config.filters:
        routed = fspec.params.get("symbol")
        if routed:
            symbols.add(str(routed))
    return sorted(symbols)


def _resolved_capital(store, config) -> float:
    """Restart-safe capital: the store's stored run capital wins whenever a
    run already exists (mirrors ``paper/eod.py::build_paper_result``'s own
    precedence); otherwise the strategy's declared capital."""
    return store.capital() or config.capital


def _build_broker(settings, config, store, calendar, *, capital: float, enforce_market_hours: bool):
    from tradingos.paper.broker import PaperBroker

    return PaperBroker(
        settings,
        strategy_id=config.name,
        capital=capital,
        cost_schedule=config.costs.schedule,
        product=config.costs.product,
        calendar=calendar,
        store=store,
        enforce_market_hours=enforce_market_hours,
    )


@app.command()
def run(
    strategy: Annotated[Path, typer.Argument(help="Path to a strategy YAML file.")],
    capital: Annotated[
        float | None,
        typer.Option(
            "--capital",
            help="Starting capital for a NEW session (default: the strategy YAML's "
            "capital). Ignored once a session for this strategy already has stored "
            "capital.",
        ),
    ] = None,
    once: Annotated[
        bool,
        typer.Option(
            "--once/--schedule",
            help="Run one open+close cycle right now (default; also useful for tests / "
            "an EOD-only manual catch-up), or start the live Mon-Fri scheduler on real "
            "ticks and block until Ctrl-C.",
        ),
    ] = True,
) -> None:
    """Run STRATEGY as a paper session."""
    from tradingos.config.settings import get_settings
    from tradingos.core.timeutils import now_ist
    from tradingos.data.calendar import NSECalendar
    from tradingos.paper.ledgerdb import PaperStore
    from tradingos.paper.runner import PaperSessionRunner

    config = _load_config(strategy)
    settings = get_settings()
    calendar = NSECalendar(settings)
    store = PaperStore(settings.paper_db_path, config.name)

    # Precedence at session creation: explicit --capital > strategy YAML's
    # capital (the value the reference backtest also uses, so the divergence
    # comparison starts from the same base).
    store.ensure_run(capital if capital is not None else config.capital, config.config_hash())
    cap = _resolved_capital(store, config)
    # --once is explicitly "useful for tests" / a manual catch-up run at any
    # time of day -- only --schedule (real trading, cron-triggered exactly at
    # session open/close) enforces market-hours risk checks.
    broker = _build_broker(settings, config, store, calendar, capital=cap, enforce_market_hours=not once)
    runner = PaperSessionRunner(settings, config, broker, calendar=calendar, store=store)

    if once:
        today = now_ist().date()
        # No live stream in --once: the day's bar OPEN is fed as the day's
        # first (synthetic) tick so planned orders fill at open±slippage,
        # exactly the backtest's next-open convention.
        runner.prime_open_quotes(today)
        runner.on_session_open(today)
        report_path = runner.on_session_close(today)
        typer.echo(f"EOD report: {report_path}")
        return

    _run_schedule(settings, config, runner, broker)


def _run_schedule(settings, config, runner, broker) -> None:
    from tradingos.core.errors import AuthError, DataError
    from tradingos.data.auth import KiteAuth
    from tradingos.data.instruments import token_for
    from tradingos.data.store import BarStore
    from tradingos.paper.ticks import TickRecorder, TickStreamer

    if not settings.kite_api_key:
        _fail("TOS_KITE_API_KEY is not set; cannot start the live tick stream")
    try:
        access_token = KiteAuth(settings).get_access_token()
    except AuthError as exc:
        _fail(str(exc))

    bar_store = BarStore(settings)
    symbols = _universe_symbols(config, bar_store)
    token_to_symbol: dict[int, str] = {}
    for sym in symbols:
        try:
            token_to_symbol[token_for(sym, settings)] = sym
        except DataError as exc:
            typer.echo(f"warning: {exc}", err=True)
    if not token_to_symbol:
        _fail("no instrument tokens resolved for the strategy's universe; sync instruments first")

    recorder = TickRecorder(settings.ticks_dir)
    streamer = TickStreamer(
        settings.kite_api_key,
        access_token,
        token_to_symbol=token_to_symbol,
        on_tick=broker.on_tick,
        recorder=recorder,
    )
    scheduler = runner.build_scheduler()

    typer.echo(f"paper trading {config.name}: scheduler + live ticks starting (Ctrl-C to stop)")
    scheduler.start()
    streamer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        typer.echo("stopping...")
    finally:
        streamer.stop()
        recorder.close()
        scheduler.shutdown(wait=False)


@app.command()
def report(
    strategy: Annotated[Path, typer.Argument(help="Path to a strategy YAML file.")],
    date_: Annotated[
        str | None,
        typer.Option("--date", help="ISO date to report on (default: last snapshot day)."),
    ] = None,
) -> None:
    """Rebuild and write the EOD report for STRATEGY from the paper store,
    without placing any orders."""
    from tradingos.config.settings import get_settings
    from tradingos.data.calendar import NSECalendar
    from tradingos.paper.eod import run_eod
    from tradingos.paper.ledgerdb import PaperStore

    config = _load_config(strategy)

    day: date | None = None
    if date_ is not None:
        try:
            day = date.fromisoformat(date_)
        except ValueError:
            _fail(f"invalid --date {date_!r}: expected ISO date YYYY-MM-DD")

    settings = get_settings()
    calendar = NSECalendar(settings)
    store = PaperStore(settings.paper_db_path, config.name)
    cap = _resolved_capital(store, config)
    broker = _build_broker(settings, config, store, calendar, capital=cap, enforce_market_hours=False)
    positions = [*broker.get_holdings(), *broker.get_positions()]

    try:
        report_path = run_eod(settings, config, store, positions, day=day)
    except ValueError as exc:
        _fail(str(exc))
        return

    typer.echo(f"EOD report: {report_path}")


@app.command()
def status(
    strategy: Annotated[Path, typer.Argument(help="Path to a strategy YAML file.")],
) -> None:
    """Print cash, equity, holdings, working orders and today's fill count for
    STRATEGY's paper session (replayed from the store; no live ticks)."""
    from tradingos.config.settings import get_settings
    from tradingos.core.timeutils import now_ist
    from tradingos.data.calendar import NSECalendar
    from tradingos.paper.ledgerdb import PaperStore

    config = _load_config(strategy)
    settings = get_settings()
    calendar = NSECalendar(settings)
    store = PaperStore(settings.paper_db_path, config.name)
    cap = _resolved_capital(store, config)
    broker = _build_broker(settings, config, store, calendar, capital=cap, enforce_market_hours=False)

    typer.echo(f"strategy      : {config.name}")
    typer.echo(f"cash          : {broker.get_margins().cash_available:,.2f}")
    typer.echo(f"equity        : {broker.equity():,.2f}")

    holdings = sorted([*broker.get_holdings(), *broker.get_positions()], key=lambda p: p.symbol)
    if holdings:
        typer.echo("holdings:")
        for p in holdings:
            typer.echo(f"  {p.symbol:<12} qty={p.qty:>6} avg={p.avg_price:>10.2f}")
    else:
        typer.echo("holdings      : none")

    working = [o for o in broker.get_orders() if not o.status.is_terminal]
    typer.echo(f"working orders: {len(working)}")
    for o in working:
        typer.echo(f"  {o.client_order_id} {o.side.value} {o.qty} {o.symbol} ({o.status.value})")

    fills_today = store.fills(day=now_ist().date())
    typer.echo(f"fills today   : {len(fills_today)}")

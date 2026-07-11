"""live CLI commands (typer sub-app): run a live trading session (dry-run by
default), inspect account/journal state, rebuild an EOD equity report from
the live journal on demand, reconcile the journal against Kite, and operate
the global kill switch.

Heavy imports (broker, engine, data store, Kite auth) are deferred inside each
command so ``platform --help`` stays instant, mirroring ``cli/paper_cmds.py``.
"""

from __future__ import annotations

import time
from datetime import date
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(no_args_is_help=True)
killswitch_app = typer.Typer(no_args_is_help=True)
app.add_typer(
    killswitch_app, name="killswitch", help="Inspect / engage / disengage the global kill switch"
)


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


def _build_broker(settings, config, store, calendar, *, dry_run: bool):
    """Build the ``ZerodhaLiveBroker`` for STRATEGY. The sole seam CLI tests
    monkeypatch to inject a broker backed by a fake Kite client instead of a
    real login (mirrors ``cli/paper_cmds.py::_build_broker``)."""
    from tradingos.live.broker import ZerodhaLiveBroker

    return ZerodhaLiveBroker(
        settings,
        strategy_id=config.name,
        dry_run=dry_run,
        cost_schedule=config.costs.schedule,
        calendar=calendar,
        store=store,
    )


def _reconcile_once(broker) -> list:
    """Lazy indirection onto ``tradingos.live.reconcile.reconcile_once`` (a
    module built in parallel with this one) -- the seam CLI tests monkeypatch
    to avoid needing that module to exist."""
    from tradingos.live.reconcile import reconcile_once

    return reconcile_once(broker)


def _print_summary(broker, opened: list, queued: list, *, dry_run: bool) -> None:
    """Readable table of what a ``run --once`` cycle did / would do."""
    typer.echo(f"session open: placed {len(opened)} order(s)")
    for o in opened:
        typer.echo(f"  {o.client_order_id} {o.side.value} {o.qty} {o.symbol} -> {o.status.value}")

    if dry_run:
        typer.echo(f"intended broker calls ({len(broker.intended_calls)}):")
        for kw in broker.intended_calls:
            price = kw.get("price", "-")
            typer.echo(
                f"  {kw['tradingsymbol']:<12} {kw['transaction_type']:<4} "
                f"qty={kw['quantity']:>6} {kw['order_type']:<8} price={price} tag={kw['tag']}"
            )

    typer.echo(f"session close: queued {len(queued)} order(s) for next open")
    for o in queued:
        typer.echo(f"  {o.client_order_id} {o.side.value} {o.qty} {o.symbol}")

    if dry_run:
        typer.echo("DRY RUN -- nothing was sent to the broker.")


# ---------------------------------------------------------------------------
# live run
# ---------------------------------------------------------------------------


@app.command()
def run(
    strategy: Annotated[Path, typer.Argument(help="Path to a strategy YAML file.")],
    once: Annotated[
        bool,
        typer.Option(
            "--once/--schedule",
            help="Run one open+close cycle right now (default), or start the live "
            "Mon-Fri scheduler (open, close, reconciliation) and block until Ctrl-C.",
        ),
    ] = True,
    live: Annotated[
        bool,
        typer.Option(
            "--live/--dry-run",
            help="Send real orders to Zerodha. DEFAULT is --dry-run: nothing is sent "
            "to the broker -- orders are journalled and their exact intended Kite "
            "kwargs are printed instead.",
        ),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Skip the interactive '--live' confirmation prompt. Needed for "
            "unattended '--schedule --live' starts (e.g. from a systemd unit or a "
            "wrapper script with no attached terminal); has no effect without --live.",
        ),
    ] = False,
) -> None:
    """Run STRATEGY as a live trading session."""
    from tradingos.config.settings import get_settings
    from tradingos.core.errors import TradingOSError
    from tradingos.core.timeutils import now_ist
    from tradingos.data.calendar import NSECalendar
    from tradingos.live.runner import LiveSessionRunner
    from tradingos.paper.ledgerdb import PaperStore

    config = _load_config(strategy)
    settings = get_settings()
    calendar = NSECalendar(settings)
    store = PaperStore(settings.live_db_path, config.name)

    if live:
        typer.echo(
            "*** LIVE TRADING ENABLED -- real orders WILL be sent to Zerodha. ***", err=True
        )
        if not yes:
            # abort=True: a "no" (or a closed/non-interactive stdin) raises
            # typer.Abort -- exit code 1, nothing built or placed below.
            typer.confirm("Send REAL orders to Zerodha?", abort=True)

    try:
        broker = _build_broker(settings, config, store, calendar, dry_run=not live)
    except TradingOSError as exc:
        _fail(str(exc))
        return

    runner = LiveSessionRunner(settings, config, broker, calendar=calendar, store=store)

    if once:
        today = now_ist().date()
        try:
            opened = runner.on_session_open(today)
            queued = runner.on_session_close(today)
        except TradingOSError as exc:
            _fail(str(exc))
            return
        _print_summary(broker, opened, queued, dry_run=not live)
        return

    _run_schedule(config, runner)


def _run_schedule(config, runner) -> None:
    scheduler = runner.build_scheduler()
    typer.echo(f"live trading {config.name}: scheduler starting (Ctrl-C to stop)")
    scheduler.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        typer.echo("stopping...")
    finally:
        scheduler.shutdown(wait=False)


# ---------------------------------------------------------------------------
# live report
# ---------------------------------------------------------------------------


@app.command()
def report(
    strategy: Annotated[Path, typer.Argument(help="Path to a strategy YAML file.")],
    date_: Annotated[
        str | None,
        typer.Option("--date", help="ISO date to report on (default: last snapshot day)."),
    ] = None,
) -> None:
    """Rebuild and write an EOD equity report for STRATEGY off the LIVE
    journal, without placing any orders.

    Reuses ``paper/eod.py::run_eod`` (mirrors ``paper report``) -- the same
    HTML/JSON report paper trading produces, built from the live journal's
    equity snapshots (written by :meth:`~tradingos.live.runner.LiveSessionRunner.on_session_close`)
    and fills. Charges shown are the cost-model ESTIMATES ``sync_orders``
    records, not broker-confirmed contract-note charges -- see
    docs/assumptions.md."""
    from tradingos.config.settings import get_settings
    from tradingos.core.errors import TradingOSError
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
    store = PaperStore(settings.live_db_path, config.name)
    # dry_run=True: report generation is read-only and must never place or
    # mutate an order (mirrors `live status`).
    try:
        broker = _build_broker(settings, config, store, calendar, dry_run=True)
    except TradingOSError as exc:
        _fail(str(exc))
        return
    positions = [*broker.get_holdings(), *broker.get_positions()]

    try:
        report_path = run_eod(settings, config, store, positions, day=day)
    except ValueError as exc:
        _fail(str(exc))
        return

    typer.echo(f"EOD report: {report_path}")


# ---------------------------------------------------------------------------
# live status
# ---------------------------------------------------------------------------


@app.command()
def status(
    strategy: Annotated[Path, typer.Argument(help="Path to a strategy YAML file.")],
) -> None:
    """Print margins, equity, holdings/positions and working orders for
    STRATEGY's live session (reads Kite directly; never places an order)."""
    from tradingos.config.settings import get_settings
    from tradingos.core.errors import TradingOSError
    from tradingos.core.timeutils import now_ist
    from tradingos.data.calendar import NSECalendar
    from tradingos.paper.ledgerdb import PaperStore

    config = _load_config(strategy)
    settings = get_settings()
    calendar = NSECalendar(settings)
    store = PaperStore(settings.live_db_path, config.name)
    # dry_run=True: status is read-only. ZerodhaLiveBroker's read calls (margins /
    # holdings / positions / orders) run identically in dry-run, and this
    # guarantees the status command can never place or mutate an order.
    try:
        broker = _build_broker(settings, config, store, calendar, dry_run=True)
    except TradingOSError as exc:
        _fail(str(exc))
        return

    typer.echo(f"strategy      : {config.name}")
    margins = broker.get_margins()
    typer.echo(f"cash          : {margins.cash_available:,.2f}")
    typer.echo(f"used          : {margins.used:,.2f}")
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


# ---------------------------------------------------------------------------
# live reconcile
# ---------------------------------------------------------------------------


@app.command()
def reconcile(
    strategy: Annotated[Path, typer.Argument(help="Path to a strategy YAML file.")],
) -> None:
    """Reconcile STRATEGY's journal against ``kite.orders()`` and report any
    mismatches. Exit code 1 if any mismatch is found, 0 otherwise."""
    from tradingos.config.settings import get_settings
    from tradingos.core.errors import TradingOSError
    from tradingos.data.calendar import NSECalendar
    from tradingos.paper.ledgerdb import PaperStore

    config = _load_config(strategy)
    settings = get_settings()
    calendar = NSECalendar(settings)
    store = PaperStore(settings.live_db_path, config.name)
    try:
        # dry_run=False: sync_orders (inside reconcile_once) is a no-op in
        # dry-run because nothing was ever placed at the real broker.
        broker = _build_broker(settings, config, store, calendar, dry_run=False)
        mismatches = _reconcile_once(broker)
    except TradingOSError as exc:
        _fail(str(exc))
        return

    if not mismatches:
        typer.echo("no mismatches")
        return

    for m in mismatches:
        ident = m.symbol or m.client_order_id
        typer.echo(f"{m.kind}: {ident} -- {m.detail}")
    raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# live killswitch status|engage|disengage
# ---------------------------------------------------------------------------


@killswitch_app.command("status")
def killswitch_status() -> None:
    """Print whether the kill switch is engaged, its reason, and its file path."""
    from tradingos.broker.killswitch import KillSwitch
    from tradingos.config.settings import get_settings

    settings = get_settings()
    ks = KillSwitch.from_settings(settings)
    if ks.is_active:
        typer.echo(f"kill switch   : ENGAGED (reason: {ks.reason() or 'unknown'})")
    else:
        typer.echo("kill switch   : not engaged")
    typer.echo(f"path          : {ks.path}")


@killswitch_app.command("engage")
def killswitch_engage(
    reason: Annotated[
        str, typer.Option("--reason", help="Why the switch is being engaged (required).")
    ],
    strategy: Annotated[
        Path | None,
        typer.Option(
            "--strategy", help="Strategy YAML whose open orders should also be cancelled."
        ),
    ] = None,
    cancel_open: Annotated[
        bool,
        typer.Option(
            "--cancel-open/--no-cancel-open",
            help="Also cancel --strategy's open orders via the broker (needs Kite "
            "credentials). Default ON.",
        ),
    ] = True,
) -> None:
    """Engage the kill switch (halts new orders platform-wide), then --
    if --strategy is given -- cancel that strategy's open orders."""
    from tradingos.broker.killswitch import KillSwitch
    from tradingos.config.settings import get_settings
    from tradingos.core.errors import AuthError

    settings = get_settings()
    ks = KillSwitch.from_settings(settings)
    # Engage FIRST -- halt new orders even if everything below fails.
    ks.engage(reason)
    typer.echo(f"kill switch engaged: {reason}")

    if strategy is None:
        typer.echo(
            "warning: no --strategy given; open orders were NOT touched. Cancel them "
            "manually (e.g. in Kite's web console) if needed.",
            err=True,
        )
        return

    if not cancel_open:
        typer.echo("--no-cancel-open: open orders were NOT touched.")
        return

    config = _load_config(strategy)
    from tradingos.data.calendar import NSECalendar
    from tradingos.paper.ledgerdb import PaperStore

    calendar = NSECalendar(settings)
    store = PaperStore(settings.live_db_path, config.name)
    try:
        broker = _build_broker(settings, config, store, calendar, dry_run=False)
        cancelled = broker.cancel_all_open()
    except AuthError as exc:
        typer.echo(
            f"warning: could not cancel open orders for {config.name} (Kite auth "
            f"failed: {exc}); open orders were NOT cancelled -- handle them in Kite's "
            "web console.",
            err=True,
        )
        return
    typer.echo(f"cancelled {len(cancelled)} open order(s) for {config.name}")


@killswitch_app.command("disengage")
def killswitch_disengage() -> None:
    """Disengage the kill switch."""
    from tradingos.broker.killswitch import KillSwitch
    from tradingos.config.settings import get_settings

    settings = get_settings()
    ks = KillSwitch.from_settings(settings)
    ks.disengage()
    typer.echo("kill switch disengaged")

"""data CLI commands (typer sub-app). Commands are added as modules land.

Heavy imports are deferred inside each command so ``platform --help`` stays
instant, mirroring the other cli/ modules.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from tradingos.core.models import Timeframe

app = typer.Typer(no_args_is_help=True)


def _fail(message: str) -> None:
    """Print a clean error to stderr and exit non-zero (never a stack trace)."""
    typer.echo(f"error: {message}", err=True)
    raise typer.Exit(code=1)


def _build_kite(settings):
    """Build an authenticated Kite client, or a clean failure. AuthError's own
    message already tells the user to run `platform data login` (see
    ``KiteAuth.get_access_token``)."""
    from tradingos.core.errors import AuthError
    from tradingos.data.auth import KiteAuth

    try:
        return KiteAuth(settings).kite()
    except AuthError as exc:
        _fail(str(exc))


@app.command()
def login(
    no_browser: Annotated[
        bool,
        typer.Option(
            "--no-browser",
            help="Print the Kite login URL instead of opening a browser (e.g. on a "
            "headless box); the local callback server still captures the redirect.",
        ),
    ] = False,
    totp: Annotated[
        bool,
        typer.Option(
            "--totp",
            help="Use the unofficial TOTP-assisted login (needs TOS_KITE_USER_ID / "
            "TOS_KITE_PASSWORD / TOS_KITE_TOTP_SECRET) instead of the interactive "
            "redirect flow.",
        ),
    ] = False,
) -> None:
    """Obtain today's Kite access token and cache it (tokens expire daily).

    The morning pre-open step for paper --schedule and live sessions; see
    docs/runbook.md section 3.
    """
    from tradingos.config.settings import get_settings
    from tradingos.core.errors import AuthError
    from tradingos.data.auth import KiteAuth

    settings = get_settings()
    auth = KiteAuth(settings)
    try:
        if totp:
            auth.totp_login()
        else:
            auth.interactive_login(open_browser=not no_browser)
    except AuthError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from None
    # Never print the token itself -- only where it was cached.
    typer.echo(f"access token cached for today at {settings.token_cache_path}")


# ---------------------------------------------------------------------------
# data sync
# ---------------------------------------------------------------------------


@app.command()
def sync(
    symbols: Annotated[list[str], typer.Argument(help="Tradingsymbols to sync.")],
    timeframe: Annotated[
        list[Timeframe] | None,
        typer.Option(
            "--timeframe", help="Bar timeframe(s) to sync (repeatable; default: day)."
        ),
    ] = None,
    start: Annotated[
        str | None,
        typer.Option(
            "--start",
            help="ISO start date for a symbol/timeframe with no stored history yet "
            "(default: 2010-01-01).",
        ),
    ] = None,
) -> None:
    """Top up local storage for SYMBOLS to the latest candle."""
    from datetime import date

    from tradingos.config.settings import get_settings
    from tradingos.data.sync import sync_symbols

    timeframes = timeframe or [Timeframe.DAY]
    default_start = date(2010, 1, 1)
    if start is not None:
        try:
            default_start = date.fromisoformat(start)
        except ValueError:
            _fail(f"invalid --start {start!r}: expected ISO date YYYY-MM-DD")

    settings = get_settings()
    kite = _build_kite(settings)
    results = sync_symbols(kite, settings, symbols, timeframes, default_start=default_start)

    failed = 0
    for r in results:
        if r.error is not None:
            failed += 1
            typer.echo(f"{r.symbol:<12} {r.timeframe.value:<6} FAILED: {r.error}")
        else:
            extent = f"{r.from_ts} .. {r.to_ts}" if r.rows_added else "already up to date"
            typer.echo(f"{r.symbol:<12} {r.timeframe.value:<6} +{r.rows_added} bar(s)  {extent}")

    typer.echo(f"synced {len(results) - failed}/{len(results)} symbol x timeframe pair(s)")
    if failed:
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# data instruments
# ---------------------------------------------------------------------------


@app.command()
def instruments() -> None:
    """Sync the NSE cash-equity instrument master (and detect symbol renames)."""
    from tradingos.config.settings import get_settings
    from tradingos.data.instruments import sync_instruments

    settings = get_settings()
    kite = _build_kite(settings)
    summary = sync_instruments(kite, settings)

    typer.echo(f"fetched        : {summary['fetched']}")
    typer.echo(f"added          : {summary['added']}")
    typer.echo(f"updated        : {summary['updated']}")
    typer.echo(f"symbol changes : {summary['symbol_changes']}")


# ---------------------------------------------------------------------------
# data doctor
# ---------------------------------------------------------------------------


@app.command()
def doctor(
    symbols: Annotated[
        list[str] | None,
        typer.Argument(help="Symbols to check (default: everything the store holds)."),
    ] = None,
    timeframe: Annotated[
        Timeframe, typer.Option("--timeframe", help="Bar timeframe to check.")
    ] = Timeframe.DAY,
) -> None:
    """Run data-quality checks over stored bars and print a health report."""
    from tradingos.config.settings import get_settings
    from tradingos.data.calendar import NSECalendar
    from tradingos.data.doctor import DataDoctor
    from tradingos.data.store import BarStore

    settings = get_settings()
    store = BarStore(settings)
    calendar = NSECalendar(settings)
    report = DataDoctor(store, calendar).run(timeframe, symbols=symbols)

    typer.echo(report.render())
    if report.errors:
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# data import-universe / import-actions / import-dividends
# ---------------------------------------------------------------------------


@app.command("import-universe")
def import_universe(
    csv_path: Annotated[Path, typer.Argument(help="Path to a membership CSV.")],
) -> None:
    """Import point-in-time index membership rows (index_name,symbol,start_date,end_date)."""
    from tradingos.config.settings import get_settings
    from tradingos.core.errors import DataError
    from tradingos.data.universe import import_membership_csv

    settings = get_settings()
    try:
        n = import_membership_csv(csv_path, settings)
    except DataError as exc:
        _fail(str(exc))
        return
    typer.echo(f"imported {n} row(s)")


@app.command("import-actions")
def import_actions(
    csv_path: Annotated[Path, typer.Argument(help="Path to a corporate-actions CSV.")],
) -> None:
    """Import corporate actions (symbol,ex_date,action_type,ratio_num,ratio_den,new_symbol,note)."""
    from tradingos.config.settings import get_settings
    from tradingos.core.errors import DataError
    from tradingos.data.actions import import_actions_csv

    settings = get_settings()
    try:
        n = import_actions_csv(csv_path, settings)
    except DataError as exc:
        _fail(str(exc))
        return
    typer.echo(f"imported {n} row(s)")


@app.command("import-dividends")
def import_dividends(
    csv_path: Annotated[Path, typer.Argument(help="Path to a dividends CSV.")],
) -> None:
    """Import cash dividends (symbol,ex_date,amount)."""
    from tradingos.config.settings import get_settings
    from tradingos.core.errors import DataError
    from tradingos.data.actions import import_dividends_csv

    settings = get_settings()
    try:
        n = import_dividends_csv(csv_path, settings)
    except DataError as exc:
        _fail(str(exc))
        return
    typer.echo(f"imported {n} row(s)")


# ---------------------------------------------------------------------------
# data adjust
# ---------------------------------------------------------------------------


@app.command()
def adjust(
    symbols: Annotated[list[str], typer.Argument(help="Symbols to rebuild adjusted bars for.")],
    timeframe: Annotated[
        Timeframe, typer.Option("--timeframe", help="Bar timeframe to rebuild.")
    ] = Timeframe.DAY,
) -> None:
    """Rebuild each symbol's adjusted OHLCV series from raw bars + corporate actions.

    After the rebuild, each adjusted series is run through the
    ``validate_adjustments`` review queue: an overnight move that SURVIVES
    adjustment and is not explained by a recorded action on that ex-date
    points at a missing/incorrect corporate action and is printed as a
    ``review:`` line (advisory -- exit code is unaffected).
    """
    from tradingos.config.settings import get_settings
    from tradingos.core.errors import DataError
    from tradingos.data.actions import build_adjusted, get_actions, validate_adjustments
    from tradingos.data.store import BarStore

    settings = get_settings()
    store = BarStore(settings)
    failed = 0
    succeeded: list[str] = []
    for symbol in symbols:
        try:
            rows = build_adjusted(symbol, timeframe, settings, store=store)
        except DataError as exc:
            failed += 1
            typer.echo(f"{symbol:<12} {timeframe.value:<6} FAILED: {exc}")
            continue
        succeeded.append(symbol)
        typer.echo(f"{symbol:<12} {timeframe.value:<6} {rows} adjusted bar(s) written")

    frames = {}
    actions_by_symbol = {}
    for symbol in succeeded:
        if not store.has_adjusted(symbol, timeframe):
            continue  # empty raw -> nothing to validate
        frames[symbol] = store.read_adjusted(symbol, timeframe).to_pandas().set_index("ts")
        actions_by_symbol[symbol] = get_actions(symbol, settings)
    for flag in validate_adjustments(frames, actions_by_symbol):
        typer.echo(
            f"review: {flag.symbol} {flag.date} overnight move {flag.gap:+.1%} survives "
            "adjustment and is not explained by any recorded corporate action -- "
            "check for a missing/incorrect split or bonus"
        )

    typer.echo(f"adjusted {len(symbols) - failed}/{len(symbols)} symbol(s)")
    if failed:
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# data migrate-symbol
# ---------------------------------------------------------------------------


@app.command("migrate-symbol")
def migrate_symbol(
    old_symbol: Annotated[str, typer.Argument(help="Symbol the stored history sits under.")],
    new_symbol: Annotated[str, typer.Argument(help="Current tradingsymbol to migrate it to.")],
) -> None:
    """Migrate stored history across a symbol rename (OLD_SYMBOL -> NEW_SYMBOL).

    Relocates raw bars for every timeframe (append-only merge when both names
    already hold bars -- the repair path for history orphaned by a rename),
    re-keys corporate actions and dividends, rebuilds the adjusted series for
    the new name, and records the rename in the symbol-mapping table if
    `data instruments` hadn't already.
    """
    from tradingos.config.settings import get_settings
    from tradingos.core.errors import DataError
    from tradingos.data.actions import build_adjusted, migrate_symbol_actions
    from tradingos.data.instruments import record_symbol_change
    from tradingos.data.store import BarStore

    if old_symbol == new_symbol:
        _fail("old and new symbol are identical; nothing to migrate")

    settings = get_settings()
    store = BarStore(settings)
    migrated_any = False
    raw_migrated: list[Timeframe] = []
    for tf in (Timeframe.DAY, Timeframe.MINUTE):
        try:
            moved = store.migrate_symbol(old_symbol, new_symbol, tf)
        except DataError as exc:
            _fail(str(exc))
            return
        if moved is None:
            continue
        migrated_any = True
        raw_migrated.append(tf)
        typer.echo(f"{tf.value:<6} migrated {moved} raw bar(s) {old_symbol} -> {new_symbol}")

    # Actions/dividends move BEFORE the adjusted rebuild so the rebuild sees
    # the full action history under the new name.
    counts = migrate_symbol_actions(old_symbol, new_symbol, settings)
    if counts["actions"] or counts["dividends"]:
        migrated_any = True
        typer.echo(
            f"moved {counts['actions']} corporate action(s) and "
            f"{counts['dividends']} dividend(s) to {new_symbol}"
        )

    for tf in raw_migrated:
        try:
            rows = build_adjusted(new_symbol, tf, settings, store=store)
        except DataError as exc:
            typer.echo(f"{tf.value:<6} adjusted rebuild FAILED: {exc}", err=True)
            continue
        typer.echo(f"{tf.value:<6} rebuilt {rows} adjusted bar(s) for {new_symbol}")

    if not migrated_any:
        _fail(
            f"nothing to migrate: no stored bars, corporate actions or dividends "
            f"found under {old_symbol}"
        )

    if record_symbol_change(old_symbol, new_symbol, settings):
        typer.echo(f"recorded symbol change {old_symbol} -> {new_symbol}")
    else:
        typer.echo(f"symbol change {old_symbol} -> {new_symbol} already recorded")

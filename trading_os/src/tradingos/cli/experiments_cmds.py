"""experiments CLI commands (typer sub-app).

``platform experiments`` drives the grid runner, leaderboard, pairwise compare,
holdout scoring (under the lockout) and single-run inspection. Heavy imports
(engines, data store, DB) live inside each command so ``platform --help`` stays
instant, mirroring ``backtest_cmds.py``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(no_args_is_help=True)


def _fail(message: str) -> None:
    """Print a clean error to stderr and exit non-zero (never a stack trace)."""
    typer.echo(f"error: {message}", err=True)
    raise typer.Exit(code=1)


@app.command()
def run(
    grid_yaml: Annotated[Path, typer.Argument(help="Path to a grid YAML file.")],
    parallel: Annotated[
        int | None,
        typer.Option("--parallel", help="Worker processes (default: grid/cpu count)."),
    ] = None,
    holdout_years: Annotated[
        float, typer.Option("--holdout-years", help="Years of data withheld as holdout.")
    ] = 2.0,
    adjusted: Annotated[
        bool, typer.Option("--adjusted/--no-adjusted", help="Use adjusted bars.")
    ] = True,
) -> None:
    """Expand GRID_YAML, run every variant on a train window, and register runs."""
    from tradingos.config.loader import load_grid
    from tradingos.config.settings import get_settings
    from tradingos.core.errors import TradingOSError
    from tradingos.experiments.leaderboard import get_run, leaderboard
    from tradingos.experiments.runner import run_grid

    try:
        grid = load_grid(grid_yaml)
    except TradingOSError as exc:
        _fail(str(exc))

    settings = get_settings()
    try:
        ids = run_grid(
            grid,
            settings,
            holdout_years=holdout_years,
            parallel=parallel,
            timeframe=grid.base.timeframe,
            adjusted=adjusted,
        )
    except TradingOSError as exc:
        _fail(str(exc))

    statuses = [get_run(i, settings).status for i in ids]
    n_done = statuses.count("done")
    n_err = statuses.count("error")
    typer.echo(f"grid       : {grid.name}")
    typer.echo(f"runs       : {len(ids)}  (done: {n_done}, error: {n_err})")

    board = leaderboard(settings, family=grid.name, top=5)
    typer.echo("\ntop 5 by sharpe:")
    typer.echo(board.to_string(index=False))


@app.command()
def leaderboard(
    family: Annotated[
        str | None, typer.Option("--family", help="Limit to one grid family.")
    ] = None,
    top: Annotated[int, typer.Option("--top", help="Number of rows to show.")] = 20,
    sort: Annotated[
        str, typer.Option("--sort", help="Sort key: sharpe|dsr|cagr|calmar.")
    ] = "sharpe",
) -> None:
    """Show the leaderboard (both Sharpe and DSR columns always shown)."""
    from tradingos.config.settings import get_settings
    from tradingos.experiments.leaderboard import leaderboard as _leaderboard

    settings = get_settings()
    try:
        board = _leaderboard(settings, family=family, top=top, sort=sort)
    except ValueError as exc:
        _fail(str(exc))

    if board.empty:
        typer.echo("no runs registered yet.")
        return
    typer.echo(board.to_string(index=False))


@app.command()
def compare(
    run_a: Annotated[int, typer.Argument(help="First run id.")],
    run_b: Annotated[int, typer.Argument(help="Second run id.")],
    out: Annotated[
        Path | None,
        typer.Option("--out", help="Write a self-contained equity-overlay HTML here."),
    ] = None,
) -> None:
    """Compare two runs' metrics; optionally write an equity-overlay report."""
    from tradingos.config.settings import get_settings
    from tradingos.core.errors import TradingOSError
    from tradingos.experiments.leaderboard import compare as _compare

    settings = get_settings()
    try:
        table = _compare(run_a, run_b, settings, out_path=out)
    except TradingOSError as exc:
        _fail(str(exc))

    typer.echo(table.to_string())
    if out is not None:
        typer.echo(f"\nreport: {out}")


@app.command("score-holdout")
def score_holdout(
    family: Annotated[str, typer.Argument(help="Grid family to score on the holdout.")],
    top: Annotated[int, typer.Option("--top", help="Top-N train runs to score.")] = 1,
    max_evals: Annotated[
        int, typer.Option("--max-evals", help="Lockout: total holdout accesses allowed.")
    ] = 3,
    sort: Annotated[
        str, typer.Option("--sort", help="Rank train runs by this metric.")
    ] = "sharpe",
) -> None:
    """Score the top train runs on the withheld holdout (subject to the lockout)."""
    from tradingos.config.settings import get_settings
    from tradingos.core.errors import HoldoutLockedError, TradingOSError
    from tradingos.experiments.holdout import score_holdout as _score_holdout

    settings = get_settings()
    try:
        ids = _score_holdout(
            family, settings, top=top, max_evals=max_evals, sort=sort
        )
    except HoldoutLockedError as exc:
        _fail(str(exc))
    except (TradingOSError, ValueError) as exc:
        _fail(str(exc))

    if not ids:
        typer.echo(f"no eligible train runs to score for family {family!r}.")
        return
    typer.echo(f"scored {len(ids)} holdout run(s): ids={ids}")


@app.command()
def show(
    run_id: Annotated[int, typer.Argument(help="Run id to inspect.")],
) -> None:
    """Print a run's fields and its full metrics dict."""
    from tradingos.config.settings import get_settings
    from tradingos.core.errors import TradingOSError
    from tradingos.experiments.leaderboard import get_run

    settings = get_settings()
    try:
        run = get_run(run_id, settings)
    except TradingOSError as exc:
        _fail(str(exc))

    fields = [
        ("id", run.id),
        ("family", run.family),
        ("variant_name", run.variant_name),
        ("engine", run.engine),
        ("status", run.status),
        ("is_holdout", run.is_holdout),
        ("train_end", run.train_end),
        ("config_hash", run.config_hash),
        ("code_git_hash", run.code_git_hash),
        ("snapshot_id", run.snapshot_id),
        ("sharpe", run.sharpe),
        ("cagr", run.cagr),
        ("max_drawdown", run.max_drawdown),
        ("calmar", run.calmar),
        ("n_bars", run.n_bars),
        ("n_trades", run.n_trades),
        ("artifacts_path", run.artifacts_path),
        ("error", run.error),
    ]
    for key, value in fields:
        typer.echo(f"{key:15}: {value}")
    typer.echo("\nmetrics:")
    typer.echo(json.dumps(json.loads(run.metrics_json or "{}"), indent=2, sort_keys=True))

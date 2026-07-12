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
    run_a: Annotated[
        int | None, typer.Argument(help="First run id (legacy two-run mode).")
    ] = None,
    run_b: Annotated[
        int | None, typer.Argument(help="Second run id (legacy two-run mode).")
    ] = None,
    out: Annotated[
        Path | None,
        typer.Option(
            "--out", help="Write a self-contained equity-overlay HTML (legacy two-run mode)."
        ),
    ] = None,
    families: Annotated[
        str | None,
        typer.Option(
            "--families", help="fnmatch glob filter on family name, e.g. 'adhoc_b2*'."
        ),
    ] = None,
    baseline: Annotated[
        int | None,
        typer.Option(
            "--baseline", help="Run id to diff against (default: latest marked run)."
        ),
    ] = None,
    markdown: Annotated[
        bool,
        typer.Option("--markdown", help="Emit a markdown table with delta-vs-baseline columns."),
    ] = False,
    all_runs: Annotated[
        bool,
        typer.Option("--all", help="Include every matching run, not just latest per family."),
    ] = False,
) -> None:
    """Compare runs' metrics.

    Two modes:

    * Legacy: ``compare RUN_A RUN_B [--out FILE]`` — two-column metric table,
      optionally an equity-overlay HTML report.
    * Multi-run: ``compare [--families GLOB] [--baseline RUN_ID] [--markdown]
      [--all]`` — one row per selected run (latest per family unless
      ``--all``) with Δ-vs-baseline columns; baseline defaults to the latest
      run marked via ``platform experiments mark``.
    """
    from tradingos.config.settings import get_settings
    from tradingos.core.errors import TradingOSError

    settings = get_settings()
    multi_mode = families is not None or baseline is not None or markdown or all_runs

    if run_a is not None or run_b is not None:
        if run_a is None or run_b is None:
            _fail("legacy two-run mode requires both RUN_A and RUN_B")
        if multi_mode:
            _fail(
                "cannot combine RUN_A/RUN_B with --families/--baseline/--markdown/--all"
            )
        from tradingos.experiments.leaderboard import compare as _compare

        try:
            table = _compare(run_a, run_b, settings, out_path=out)
        except TradingOSError as exc:
            _fail(str(exc))

        typer.echo(table.to_string())
        if out is not None:
            typer.echo(f"\nreport: {out}")
        return

    from tradingos.experiments.leaderboard import compare_runs, to_markdown_table

    try:
        board = compare_runs(settings, families=families, baseline=baseline, all_runs=all_runs)
    except TradingOSError as exc:
        _fail(str(exc))

    if board.empty:
        typer.echo("no runs matched.")
        return

    if markdown:
        typer.echo(to_markdown_table(board))
    else:
        typer.echo(board.to_string(index=False))


@app.command()
def mark(
    run_id: Annotated[int, typer.Argument(help="Run id to mark/unmark.")],
    unset: Annotated[
        bool, typer.Option("--unset", help="Clear the mark instead of setting it.")
    ] = False,
) -> None:
    """Mark (or ``--unset`` to unmark) a run as the default baseline for
    ``platform experiments compare --markdown``."""
    from tradingos.config.settings import get_settings
    from tradingos.core.errors import TradingOSError
    from tradingos.experiments.leaderboard import mark_run

    settings = get_settings()
    try:
        run = mark_run(run_id, settings, marked=not unset)
    except TradingOSError as exc:
        _fail(str(exc))

    state = "marked" if run.is_marked else "unmarked"
    typer.echo(f"run {run.id} ({run.family}/{run.variant_name}) {state}.")


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

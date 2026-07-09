"""Typer CLI root. Subcommand groups are registered from their own modules;
each group lives with its domain (data, backtest, experiments, paper, live).

Entry point: `platform` (see pyproject [project.scripts]).
"""

from __future__ import annotations

import logging

import typer

from tradingos.config.settings import get_settings
from tradingos.core.logging import setup_logging

app = typer.Typer(
    name="platform",
    help="India equity (NSE) backtesting, paper and live trading platform.",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)


@app.callback()
def _init(verbose: bool = typer.Option(False, "--verbose", "-v", help="Debug logging")) -> None:
    settings = get_settings()
    level = logging.DEBUG if verbose else getattr(logging, settings.log_level.upper(), 20)
    setup_logging(level=level)


@app.command()
def version() -> None:
    """Print platform version."""
    import tradingos

    typer.echo(f"tradingos {tradingos.__version__}")


def _register_groups() -> None:
    # imported lazily so a broken optional area doesn't kill the whole CLI
    from tradingos.cli import backtest_cmds, data_cmds, experiments_cmds, live_cmds, paper_cmds

    app.add_typer(data_cmds.app, name="data", help="Sync, inspect and validate market data")
    app.add_typer(backtest_cmds.app, name="backtest", help="Run backtests and reports")
    app.add_typer(experiments_cmds.app, name="experiments", help="Grid runs, leaderboard, compare")
    app.add_typer(paper_cmds.app, name="paper", help="Paper trading on live ticks")
    app.add_typer(live_cmds.app, name="live", help="Live trading (Zerodha), kill switch, dry-run")


_register_groups()


if __name__ == "__main__":
    app()

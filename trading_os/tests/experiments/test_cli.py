"""CLI smoke: run -> leaderboard -> show -> compare via typer's CliRunner."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from tradingos.cli import main as cli_main
from tradingos.config.settings import Settings

runner = CliRunner()


def test_cli_run_leaderboard_show_compare(
    cli_env: tuple[Settings, Path], tmp_path: Path
) -> None:
    _settings, yaml_path = cli_env

    # run the grid (sequential; no spawn under CliRunner)
    res_run = runner.invoke(
        cli_main.app,
        ["experiments", "run", str(yaml_path), "--parallel", "1", "--holdout-years", "0.5"],
    )
    assert res_run.exit_code == 0, res_run.output
    assert "done: 4" in res_run.output
    assert "cli_fam" in res_run.output

    # leaderboard always shows BOTH sharpe and dsr columns
    res_lb = runner.invoke(cli_main.app, ["experiments", "leaderboard", "--family", "cli_fam"])
    assert res_lb.exit_code == 0, res_lb.output
    assert "sharpe" in res_lb.output
    assert "dsr" in res_lb.output

    # show a single run's fields + metrics
    res_show = runner.invoke(cli_main.app, ["experiments", "show", "1"])
    assert res_show.exit_code == 0, res_show.output
    assert "metrics:" in res_show.output
    assert "config_hash" in res_show.output

    # compare two runs, writing the self-contained HTML report
    out_html = tmp_path / "cmp.html"
    res_cmp = runner.invoke(
        cli_main.app, ["experiments", "compare", "1", "2", "--out", str(out_html)]
    )
    assert res_cmp.exit_code == 0, res_cmp.output
    assert out_html.exists()


def test_cli_score_holdout_lockout_exits_nonzero(cli_env: tuple[Settings, Path]) -> None:
    _settings, yaml_path = cli_env
    res_run = runner.invoke(
        cli_main.app,
        ["experiments", "run", str(yaml_path), "--parallel", "1", "--holdout-years", "0.5"],
    )
    assert res_run.exit_code == 0, res_run.output

    # quota exhausted immediately (top=3 > max-evals=2) -> non-zero, no stacktrace
    res_hold = runner.invoke(
        cli_main.app,
        ["experiments", "score-holdout", "cli_fam", "--top", "3", "--max-evals", "2"],
    )
    assert res_hold.exit_code != 0
    assert "error:" in res_hold.output
    assert "LOCKED" in res_hold.output
    assert "Traceback" not in res_hold.output

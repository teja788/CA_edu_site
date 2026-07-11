"""Leaderboard: query-time DSR, sorting, and holdout exclusion."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from tradingos.config.schemas import GridSpec
from tradingos.config.settings import Settings
from tradingos.experiments.holdout import score_holdout
from tradingos.experiments.leaderboard import compare, leaderboard
from tradingos.experiments.runner import run_grid

HOLDOUT_YEARS = 0.5


def test_dsr_present_and_finite_sorting_and_holdout_excluded(
    seeded_settings: Settings, grid: GridSpec
) -> None:
    ids = run_grid(grid, seeded_settings, holdout_years=HOLDOUT_YEARS, parallel=1)
    assert len(ids) == 4

    board = leaderboard(seeded_settings, family=grid.name, top=20)
    assert list(board.columns) == [
        "id",
        "family",
        "variant_name",
        "engine",
        "sharpe",
        "dsr",
        "cagr",
        "max_drawdown",
        "calmar",
        "total_costs_pct",
        "n_trades",
        "tainted",
        "n_warnings",
        "overrides",
    ]
    assert len(board) == 4
    # DSR is finite for the 4-run family (>= 2 finite trial Sharpes).
    assert board["dsr"].notna().all()

    # sort by sharpe: non-NaN values descending
    by_sharpe = leaderboard(seeded_settings, family=grid.name, sort="sharpe")["sharpe"].dropna()
    assert list(by_sharpe) == sorted(by_sharpe, reverse=True)

    # sort by dsr: non-NaN values descending, NaN last
    dsr_col = leaderboard(seeded_settings, family=grid.name, sort="dsr")["dsr"]
    non_nan = [x for x in dsr_col if pd.notna(x)]
    assert non_nan == sorted(non_nan, reverse=True)

    # score a holdout run; it must NOT appear on the default leaderboard
    score_holdout(grid.name, seeded_settings, top=1, max_evals=3)
    board_after = leaderboard(seeded_settings, family=grid.name, top=20)
    assert len(board_after) == 4  # still only the 4 train runs
    assert not board_after["variant_name"].str.contains("holdout").any()


def test_compare_writes_selfcontained_html(
    seeded_settings: Settings, grid: GridSpec, tmp_path: Path
) -> None:
    ids = run_grid(grid, seeded_settings, holdout_years=HOLDOUT_YEARS, parallel=1)
    out = tmp_path / "compare.html"
    table = compare(ids[0], ids[-1], seeded_settings, out_path=out)

    # two-column metric table with shared metric keys
    assert table.shape[1] == 2
    assert "sharpe" in table.index
    assert out.exists()
    html = out.read_text()
    assert "tos-compare-equity" in html  # deterministic div id
    assert "plotly" in html.lower()  # plotly.js inlined

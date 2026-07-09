"""Reproducibility: a freshly registered run re-runs bit-for-bit."""

from __future__ import annotations

from tradingos.config.schemas import GridSpec
from tradingos.config.settings import Settings
from tradingos.experiments.leaderboard import reproduce
from tradingos.experiments.runner import run_grid

HOLDOUT_YEARS = 0.5


def test_reproduce_is_true_for_fresh_grid_runs(
    seeded_settings: Settings, grid: GridSpec
) -> None:
    ids = run_grid(grid, seeded_settings, holdout_years=HOLDOUT_YEARS, parallel=1)
    # every train run reconstructs from its stored config + clamp and matches
    # its saved equity curve exactly.
    for i in ids:
        assert reproduce(i, seeded_settings) is True

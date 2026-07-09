"""Holdout lockout: quota enforcement, audit rows, out-of-sample window."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlmodel import select

from tradingos.config.schemas import GridSpec
from tradingos.config.settings import Settings
from tradingos.core.errors import HoldoutLockedError
from tradingos.engine.result import BacktestResult
from tradingos.experiments.db import session_scope
from tradingos.experiments.holdout import score_holdout
from tradingos.experiments.leaderboard import get_run
from tradingos.experiments.models import ExperimentRun, HoldoutAccess
from tradingos.experiments.runner import run_grid

HOLDOUT_YEARS = 0.5


def _counts(settings: Settings, family: str) -> tuple[int, int]:
    """(HoldoutAccess rows, is_holdout ExperimentRun rows) for a family."""
    with session_scope(settings) as session:
        access = session.exec(
            select(HoldoutAccess).where(HoldoutAccess.family == family)
        ).all()
        runs = session.exec(
            select(ExperimentRun).where(ExperimentRun.family == family)
        ).all()
        # read attributes inside the session (rows detach/expire on close)
        return len(access), sum(1 for r in runs if r.is_holdout)


def test_lockout_allows_up_to_quota_then_raises(
    seeded_settings: Settings, grid: GridSpec
) -> None:
    run_grid(grid, seeded_settings, holdout_years=HOLDOUT_YEARS, parallel=1)
    fam = grid.name

    # first two accesses succeed under max_evals=2
    first = score_holdout(fam, seeded_settings, top=1, max_evals=2)
    second = score_holdout(fam, seeded_settings, top=1, max_evals=2)
    assert len(first) == 1
    assert len(second) == 1

    n_access, n_holdout = _counts(seeded_settings, fam)
    assert n_access == 2  # one audit row per access
    assert n_holdout == 2  # one is_holdout run per access

    # the holdout equity STARTS strictly AFTER train_end (out-of-sample window)
    holdout_run = get_run(first[0], seeded_settings)
    assert holdout_run.is_holdout
    equity = BacktestResult.load(Path(holdout_run.artifacts_path)).equity
    assert equity.index.min().date() > holdout_run.train_end

    # third access exceeds the quota
    with pytest.raises(HoldoutLockedError, match="LOCKED"):
        score_holdout(fam, seeded_settings, top=1, max_evals=2)


def test_top3_refuses_before_any_scoring(seeded_settings: Settings, grid: GridSpec) -> None:
    run_grid(grid, seeded_settings, holdout_years=HOLDOUT_YEARS, parallel=1)
    fam = grid.name

    with pytest.raises(HoldoutLockedError, match="prevent data-mining"):
        score_holdout(fam, seeded_settings, top=3, max_evals=2)

    # NO partial scoring: no audit rows and no holdout runs were created
    n_access, n_holdout = _counts(seeded_settings, fam)
    assert n_access == 0
    assert n_holdout == 0

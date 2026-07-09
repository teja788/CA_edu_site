"""run_grid end-to-end: sequential and spawn parity, clamp recording, worker
error path. EVENT engine only (no vectorbt import in the suite)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from tradingos.config.schemas import (
    EngineMode,
    GridSpec,
    ScoreSpec,
    SignalSpec,
    StrategyConfig,
    UniverseSpec,
)
from tradingos.config.settings import Settings
from tradingos.engine.result import BacktestResult
from tradingos.experiments.leaderboard import get_run
from tradingos.experiments.runner import _run_variant, run_grid

HOLDOUT_YEARS = 0.5


def test_sequential_and_spawn_produce_identical_done_runs(
    make_seeded: Callable[[str], Settings], grid: GridSpec
) -> None:
    seq_settings = make_seeded("seq")
    par_settings = make_seeded("par")

    ids_seq = run_grid(grid, seq_settings, holdout_years=HOLDOUT_YEARS, parallel=1)
    ids_par = run_grid(grid, par_settings, holdout_years=HOLDOUT_YEARS, parallel=2)

    runs_seq = [get_run(i, seq_settings) for i in ids_seq]
    runs_par = [get_run(i, par_settings) for i in ids_par]

    # 4 done rows in each execution mode
    assert len(ids_seq) == 4
    assert len(ids_par) == 4
    assert all(r.status == "done" for r in runs_seq)
    assert all(r.status == "done" for r in runs_par)

    # identical config hashes (per variant) regardless of parallelism
    assert sorted(r.config_hash for r in runs_seq) == sorted(r.config_hash for r in runs_par)

    # metric columns and DSR inputs populated
    for r in runs_seq:
        assert r.n_bars is not None and r.n_bars > 0
        assert r.sharpe is not None
        assert r.ret_kurt is not None  # non-excess kurtosis recorded
        assert r.metrics_json and r.metrics_json != "{}"


def test_train_clamp_recorded_and_equity_ends_by_train_end(
    seeded_settings: Settings, grid: GridSpec
) -> None:
    ids = run_grid(grid, seeded_settings, holdout_years=HOLDOUT_YEARS, parallel=1)
    for i in ids:
        run = get_run(i, seeded_settings)
        assert run.train_end is not None  # the clamp actually applied is recorded
        assert not run.is_holdout
        equity = BacktestResult.load(Path(run.artifacts_path)).equity
        # every train run's data ends ON or BEFORE the clamp (holdout is withheld)
        assert equity.index.max().date() <= run.train_end


def test_worker_records_error_on_missing_data_without_killing_grid(
    seeded_settings: Settings,
) -> None:
    """A variant whose universe has no data must yield status='error' (so the
    parent records it and the grid survives) rather than raising."""
    bad_config = StrategyConfig(
        name="ghost__0000",
        engine=EngineMode.EVENT,
        universe=UniverseSpec(symbols=["GHOST"], point_in_time=False),
        signals=[SignalSpec(id="mom", name="return_over_window", params={"window": 20})],
        score=ScoreSpec(type="single"),
    )
    payload = {
        "family": "ghostfam",
        "variant_name": "ghost__0000",
        "config_hash": "deadbeefdeadbeef",
        "config_json": "{}",
        "config_run": bad_config.model_dump(mode="json"),
        "overrides_json": "{}",
        "code_git_hash": "unknown",
        "snapshot_id": "snap",
        "engine": "event",
        "is_holdout": False,
        "train_end": None,
        "artifacts_path": str(seeded_settings.artifacts_dir / "experiments" / "ghost"),
        "data_dir": str(seeded_settings.data_dir),
        "artifacts_dir": str(seeded_settings.artifacts_dir),
        "symbols": ["GHOST"],
        "timeframe": "day",
        "adjusted": True,
    }
    row = _run_variant(payload)
    assert row["status"] == "error"
    assert row["error"]  # non-empty message
    assert row["sharpe"] is None
    assert row["metrics_json"] == "{}"

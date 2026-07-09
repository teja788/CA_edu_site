"""Shared fixtures for the experiments tests.

Builds a small seeded BarStore in tmp_path (the tests/cli pattern) and a 2x2
EVENT-engine grid over three synthetic symbols. ~2.5 years of daily bars so a
``holdout_years=0.5`` split leaves ~2 years of train data — enough for finite
metrics while still exercising the train/holdout clamp.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from pathlib import Path

import polars as pl
import pytest
import yaml
from fixtures.synthetic import synthetic_daily

from tradingos.config.schemas import (
    EngineMode,
    ExecutionSpec,
    GridSpec,
    RebalanceSpec,
    ScoreSpec,
    SelectionSpec,
    SignalSpec,
    SizingSpec,
    StrategyConfig,
    UniverseSpec,
)
from tradingos.config.settings import Settings
from tradingos.core.models import Timeframe
from tradingos.data.store import BarStore

SYMBOLS = ["AAA", "BBB", "CCC"]
DATA_START = date(2019, 1, 1)
DATA_END = date(2021, 6, 30)  # ~2.5y so a 0.5y holdout leaves ~2y of train data
HOLDOUT_YEARS = 0.5


def build_grid(name: str = "momfam") -> GridSpec:
    """A 2x2 EVENT-engine momentum sweep (window x selection.n)."""
    base = StrategyConfig(
        name="mom",
        engine=EngineMode.EVENT,
        start=DATA_START,
        end=None,  # left open so the train_end clamp is what bounds the run
        capital=1_000_000.0,
        universe=UniverseSpec(symbols=list(SYMBOLS), point_in_time=False),
        signals=[SignalSpec(id="mom", name="return_over_window", params={"window": 20})],
        score=ScoreSpec(type="single"),
        selection=SelectionSpec(method="top_n", n=1, exit_rank=3),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.9),
        rebalance=RebalanceSpec(frequency="monthly", trading_day=1),
        execution=ExecutionSpec(timing="next_open", slippage_bps=0.0, max_participation=1.0),
    )
    return GridSpec(
        name=name,
        base=base,
        sweep={"signals.mom.params.window": [20, 60], "selection.n": [1, 2]},
        engine=EngineMode.EVENT,
        max_parallel=2,
    )


def seed_store(settings: Settings) -> None:
    store = BarStore(settings)
    for sym in SYMBOLS:
        pdf = synthetic_daily(sym, start=DATA_START, end=DATA_END)
        pldf = pl.from_pandas(pdf.reset_index(names="ts"))
        store.write_raw(sym, Timeframe.DAY, pldf)


@pytest.fixture()
def exp_settings(tmp_path: Path) -> Settings:
    settings = Settings(
        data_dir=tmp_path / "data", artifacts_dir=tmp_path / "artifacts", _env_file=None
    )
    settings.ensure_dirs()
    return settings


@pytest.fixture()
def seeded_settings(exp_settings: Settings) -> Settings:
    seed_store(exp_settings)
    return exp_settings


@pytest.fixture()
def grid() -> GridSpec:
    return build_grid()


@pytest.fixture()
def make_seeded(tmp_path: Path) -> Callable[[str], Settings]:
    """Factory: build a fresh, seeded Settings under a tmp subdir (for tests that
    need two independent stores, e.g. sequential vs spawn)."""

    def _make(sub: str) -> Settings:
        settings = Settings(
            data_dir=tmp_path / sub / "data",
            artifacts_dir=tmp_path / sub / "artifacts",
            _env_file=None,
        )
        settings.ensure_dirs()
        seed_store(settings)
        return settings

    return _make


@pytest.fixture()
def cli_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Settings, Path]:
    """Seeded store + a grid YAML on disk, with get_settings monkeypatched to the
    tmp settings (the tests/cli pattern)."""
    settings = Settings(
        data_dir=tmp_path / "data", artifacts_dir=tmp_path / "artifacts", _env_file=None
    )
    settings.ensure_dirs()
    seed_store(settings)
    # The commands import get_settings at call time; patch the source binding
    # (and the root callback's own binding) so the CLI sees the tmp store.
    monkeypatch.setattr("tradingos.config.settings.get_settings", lambda: settings)
    monkeypatch.setattr("tradingos.cli.main.get_settings", lambda: settings)

    grid = build_grid("cli_fam")
    yaml_path = tmp_path / "grid.yaml"
    yaml_path.write_text(yaml.safe_dump(grid.model_dump(mode="json")))
    return settings, yaml_path

"""Generic variant harness: dotted-path override application, end-to-end
run_variants persistence, and the run-variants CLI command.

Synthetic fixtures only (never live APIs). The end-to-end test hands
run_variants a pre-built MarketData so no BarStore is needed; the CLI test
seeds a tmp store (the tests/cli pattern)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import polars as pl
import pytest
import yaml
from fixtures.synthetic import synthetic_universe
from typer.testing import CliRunner

from tradingos.cli import main as cli_main
from tradingos.config.schemas import (
    EngineMode,
    ExecutionSpec,
    RebalanceSpec,
    ScoreSpec,
    SelectionSpec,
    SignalSpec,
    SizingSpec,
    StrategyConfig,
    UniverseSpec,
)
from tradingos.config.settings import Settings
from tradingos.core.errors import ConfigError
from tradingos.core.models import Timeframe
from tradingos.data.store import BarStore
from tradingos.engine.dataview import MarketData
from tradingos.experiments.leaderboard import get_run
from tradingos.experiments.variants import build_variant_config, run_variants

SYMBOLS = ["AAA", "BBB", "CCC"]
DATA_START = date(2019, 1, 1)
DATA_END = date(2021, 6, 30)


def _base() -> StrategyConfig:
    return StrategyConfig(
        name="mom",
        engine=EngineMode.EVENT,
        start=DATA_START,
        end=DATA_END,
        capital=1_000_000.0,
        universe=UniverseSpec(symbols=list(SYMBOLS), point_in_time=False),
        signals=[SignalSpec(id="mom", name="return_over_window", params={"window": 20})],
        score=ScoreSpec(type="single"),
        selection=SelectionSpec(method="top_n", n=1, exit_rank=3),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.9),
        rebalance=RebalanceSpec(frequency="monthly", trading_day=1),
        execution=ExecutionSpec(timing="next_open", slippage_bps=0.0, max_participation=1.0),
    )


def _market_data() -> MarketData:
    return MarketData(
        synthetic_universe(SYMBOLS, start=DATA_START, end=DATA_END),
        timeframe=Timeframe.DAY,
        snapshot_id="synthtest",
    )


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    s = Settings(
        data_dir=tmp_path / "data", artifacts_dir=tmp_path / "artifacts", _env_file=None
    )
    s.ensure_dirs()
    return s


# --------------------------------------------------------------------------- #
# Dotted-path override application                                             #
# --------------------------------------------------------------------------- #
def test_nested_override_reruns_validation() -> None:
    cfg = build_variant_config(_base(), "mom_exit2", {"selection.exit_rank": 2})
    assert cfg.name == "mom_exit2"
    assert cfg.selection.exit_rank == 2
    # untouched fields survive
    assert cfg.selection.n == 1
    assert cfg.capital == 1_000_000.0


def test_whole_spec_replacement() -> None:
    """A single-segment path replaces a whole nested spec; validation reruns so
    the new signals/score are checked as a set (score refers to the new id)."""
    cfg = build_variant_config(
        _base(),
        "mom_reweighted",
        {
            "signals": [
                {"id": "r6", "name": "return_over_window", "params": {"window": 120}},
                {"id": "r12", "name": "return_over_window", "params": {"window": 240}},
            ],
            "score": {"type": "weighted_zscore", "weights": {"r6": 0.5, "r12": 0.5}},
        },
    )
    assert [s.id for s in cfg.signals] == ["r6", "r12"]
    assert cfg.score is not None and cfg.score.weights == {"r6": 0.5, "r12": 0.5}


def test_illegal_override_raises_configerror() -> None:
    """exit_rank < n is rejected by the SelectionSpec validator on rebuild."""
    with pytest.raises(ConfigError):
        build_variant_config(_base(), "bad", {"selection.n": 5})  # n(5) > exit_rank(3)


def test_unknown_path_raises_rather_than_silently_noop() -> None:
    with pytest.raises(ConfigError):
        build_variant_config(_base(), "typo", {"selektion.exit_rank": 2})


def test_score_weight_unknown_signal_id_rejected() -> None:
    with pytest.raises(ConfigError):
        build_variant_config(_base(), "bad", {"score.weights": {"ghost": 1.0}})


# --------------------------------------------------------------------------- #
# End-to-end run_variants                                                      #
# --------------------------------------------------------------------------- #
def test_run_variants_persists_artifacts_and_rows(settings: Settings) -> None:
    variants = {
        "v_exit2": {"selection.exit_rank": 2},
        "v_win60": {"signals.mom.params.window": 60},
    }
    stats = run_variants(
        _base(), variants, settings, family_prefix="unittest", data=_market_data()
    )

    # two done stats in declared order
    assert [s["variant"] for s in stats] == ["v_exit2", "v_win60"]
    assert all("status" not in s for s in stats)  # done stats carry the batch shape

    # two ExperimentRun rows, both done (read fields inside the session)
    from sqlmodel import select

    from tradingos.experiments.db import session_scope
    from tradingos.experiments.models import ExperimentRun

    with session_scope(settings) as session:
        rows = list(session.exec(select(ExperimentRun)))
        assert len(rows) == 2
        assert all(r.status == "done" for r in rows)
        assert {r.family for r in rows} == {
            "adhoc_v_exit2_unittest",
            "adhoc_v_win60_unittest",
        }
        by_variant = {r.variant_name: r.artifacts_path for r in rows}

    # artifacts: files per run, and summary.json matches the returned stats
    for stat in stats:
        run_dir = Path(by_variant[stat["variant"]])
        for fname in ("net_equity_curve.csv", "trades.csv", "summary.json"):
            assert (run_dir / fname).exists(), fname
        summary = json.loads((run_dir / "summary.json").read_text())
        assert summary == stat

    # comparison JSON written with both variants
    comparisons = list((settings.artifacts_dir / "adhoc").glob("unittest_comparison_*.json"))
    assert len(comparisons) == 1
    payload = json.loads(comparisons[0].read_text())
    assert payload["n_variants"] == 2
    assert [v["variant"] for v in payload["variants"]] == ["v_exit2", "v_win60"]


def test_run_variants_one_bad_variant_does_not_abort_batch(settings: Settings) -> None:
    variants = {
        "good": {"selection.exit_rank": 2},
        "bad": {"selection.n": 5},  # n > exit_rank -> illegal
    }
    stats = run_variants(
        _base(), variants, settings, family_prefix="mixed", data=_market_data()
    )
    by_name = {s["variant"]: s for s in stats}
    assert "status" not in by_name["good"]
    assert by_name["bad"]["status"] == "error"
    assert "message" in by_name["bad"]

    # only the good variant produced a DB row
    from sqlmodel import select

    from tradingos.experiments.db import session_scope
    from tradingos.experiments.models import ExperimentRun

    with session_scope(settings) as session:
        rows = list(session.exec(select(ExperimentRun)))
        assert len(rows) == 1
        assert rows[0].variant_name == "good"


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
runner = CliRunner()


def test_cli_run_variants_with_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = Settings(
        data_dir=tmp_path / "data", artifacts_dir=tmp_path / "artifacts", _env_file=None
    )
    settings.ensure_dirs()
    store = BarStore(settings)
    for sym, pdf in synthetic_universe(SYMBOLS, start=DATA_START, end=DATA_END).items():
        store.write_raw(sym, Timeframe.DAY, pl.from_pandas(pdf.reset_index(names="ts")))
    monkeypatch.setattr("tradingos.config.settings.get_settings", lambda: settings)
    monkeypatch.setattr("tradingos.cli.main.get_settings", lambda: settings)

    base_yaml = tmp_path / "base.yaml"
    base_yaml.write_text(yaml.safe_dump(_base().model_dump(mode="json")))
    variants_yaml = tmp_path / "variants.yaml"
    variants_yaml.write_text(
        yaml.safe_dump(
            {
                "v_exit2": {"selection.exit_rank": 2},
                "v_win60": {"signals.mom.params.window": 60},
            }
        )
    )

    res = runner.invoke(
        cli_main.app,
        [
            "experiments",
            "run-variants",
            str(base_yaml),
            "--variants-file",
            str(variants_yaml),
            "--family-prefix",
            "clivar",
        ],
    )
    assert res.exit_code == 0, res.output
    assert "done: 2" in res.output

    ids = [1, 2]
    statuses = {get_run(i, settings).status for i in ids}
    assert statuses == {"done"}


def test_cli_run_variants_set_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = Settings(
        data_dir=tmp_path / "data", artifacts_dir=tmp_path / "artifacts", _env_file=None
    )
    settings.ensure_dirs()
    store = BarStore(settings)
    for sym, pdf in synthetic_universe(SYMBOLS, start=DATA_START, end=DATA_END).items():
        store.write_raw(sym, Timeframe.DAY, pl.from_pandas(pdf.reset_index(names="ts")))
    monkeypatch.setattr("tradingos.config.settings.get_settings", lambda: settings)
    monkeypatch.setattr("tradingos.cli.main.get_settings", lambda: settings)

    base_yaml = tmp_path / "base.yaml"
    base_yaml.write_text(yaml.safe_dump(_base().model_dump(mode="json")))

    res = runner.invoke(
        cli_main.app,
        [
            "experiments",
            "run-variants",
            str(base_yaml),
            "--set",
            "selection.exit_rank=2",
            "--name",
            "solo",
            "--family-prefix",
            "cliset",
        ],
    )
    assert res.exit_code == 0, res.output
    assert "done: 1" in res.output
    assert get_run(1, settings).variant_name == "solo"

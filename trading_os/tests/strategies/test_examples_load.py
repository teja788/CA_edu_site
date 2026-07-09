"""Every YAML in strategies/examples/ must load via load_strategy without
error. These are the four reference strategies from initial_prompt.md
MODULE 2 (momentum_composite, momentum_12_1, dual_momentum, trend_200dma).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tradingos.config.loader import load_grid, load_strategy
from tradingos.config.schemas import StrategyConfig

EXAMPLES_DIR = (
    Path(__file__).resolve().parents[2] / "src" / "tradingos" / "strategies" / "examples"
)


def _example_paths() -> list[Path]:
    return sorted(EXAMPLES_DIR.glob("*.yaml"))


def test_examples_dir_exists_and_is_non_empty() -> None:
    assert EXAMPLES_DIR.is_dir()
    assert _example_paths(), f"no YAML files found under {EXAMPLES_DIR}"


def test_examples_dir_has_all_four_reference_strategies() -> None:
    names = {p.stem for p in _example_paths()}
    required = {"momentum_composite", "momentum_12_1", "dual_momentum", "trend_200dma"}
    assert required <= names, f"missing reference strategies: {required - names}"


@pytest.mark.parametrize("path", _example_paths(), ids=lambda p: p.stem)
def test_example_strategy_loads_and_validates(path: Path) -> None:
    cfg = load_strategy(path)
    assert isinstance(cfg, StrategyConfig)
    assert cfg.name == path.stem
    assert cfg.description.strip(), f"{path.name} should have a non-empty description"
    assert cfg.start is not None and cfg.end is not None
    assert cfg.start < cfg.end
    assert cfg.capital > 0


def test_momentum_composite_score_weights_reference_declared_signal_ids() -> None:
    cfg = load_strategy(EXAMPLES_DIR / "momentum_composite.yaml")
    signal_ids = {s.id for s in cfg.signals}
    assert cfg.score is not None
    assert cfg.score.type == "weighted_zscore"
    assert set(cfg.score.weights) <= signal_ids, "score references an undeclared signal id"
    assert set(cfg.score.weights) == signal_ids, "every declared signal should be scored"
    assert pytest.approx(sum(cfg.score.weights.values())) == 1.0


def test_momentum_composite_matches_the_spec_shape() -> None:
    cfg = load_strategy(EXAMPLES_DIR / "momentum_composite.yaml")
    assert cfg.universe.index == "NIFTY500"
    assert cfg.universe.point_in_time is True
    assert cfg.universe.min_median_traded_value == pytest.approx(2e7)
    assert cfg.score.weights == {
        "mom_12_1": pytest.approx(0.5),
        "dist_52w_high": pytest.approx(0.3),
        "smoothness": pytest.approx(0.2),
    }
    assert [f.name for f in cfg.filters] == ["index_above_ma"]
    # `symbol` is the reserved engine routing key (Phase 3): index_above_ma is a
    # regime gate evaluated on the "NIFTY 50" series, not the traded symbol.
    assert cfg.filters[0].params == {"window": 200, "symbol": "NIFTY 50"}
    assert cfg.selection.n == 25
    assert cfg.selection.exit_rank == 40
    assert cfg.sizing.method == "equal_weight"
    assert cfg.rebalance.frequency == "monthly"
    assert cfg.rebalance.trading_day == 1
    assert [o.name for o in cfg.overlays] == ["trailing_stop_atr"]
    assert cfg.overlays[0].params == {"atr_window": 14, "multiple": 3.0}
    assert cfg.execution.timing == "next_open"
    assert cfg.costs.schedule == "zerodha_2026"
    assert cfg.costs.product == "CNC"


def test_dual_momentum_is_a_two_symbol_non_pit_universe() -> None:
    cfg = load_strategy(EXAMPLES_DIR / "dual_momentum.yaml")
    assert cfg.universe.point_in_time is False
    assert cfg.universe.symbols is not None
    assert set(cfg.universe.symbols) == {"NIFTYBEES", "LIQUIDBEES"}
    assert cfg.selection.n == 1
    assert cfg.rebalance.frequency == "monthly"


def test_trend_200dma_is_single_symbol_with_index_above_ma_filter() -> None:
    cfg = load_strategy(EXAMPLES_DIR / "trend_200dma.yaml")
    assert cfg.universe.symbols == ["NIFTYBEES"]
    assert cfg.selection.n == 1
    assert [f.name for f in cfg.filters] == ["index_above_ma"]
    assert cfg.filters[0].params["window"] == 200


def test_momentum_12_1_is_a_plain_top_n_momentum_baseline() -> None:
    cfg = load_strategy(EXAMPLES_DIR / "momentum_12_1.yaml")
    assert len(cfg.signals) == 1
    assert cfg.signals[0].name == "return_over_window"
    assert cfg.selection.n == 20
    assert not cfg.filters
    assert not cfg.overlays


def test_grid_loader_smoke_with_inline_base(tmp_path: Path) -> None:
    grid_yaml = """
name: smoke_grid
base:
  name: smoke_base
  universe: {symbols: [INFY, TCS], point_in_time: false}
  signals: [{id: mom, name: return_over_window, params: {window: 252}}]
  score: {type: weighted_zscore, weights: {mom: 1.0}}
sweep:
  signals.mom.params.window: [126, 252]
  selection.n: [10, 20]
engine: vectorized
"""
    p = tmp_path / "grid.yaml"
    p.write_text(grid_yaml)
    grid = load_grid(p)
    assert grid.name == "smoke_grid"
    assert grid.base.name == "smoke_base"
    assert grid.sweep["selection.n"] == [10, 20]
    assert grid.sweep["signals.mom.params.window"] == [126, 252]


def test_grid_loader_smoke_with_base_as_path_reference(tmp_path: Path) -> None:
    base_path = tmp_path / "base.yaml"
    base_path.write_text(
        "name: smoke_base\n"
        "universe: {symbols: [INFY], point_in_time: false}\n"
    )
    grid_path = tmp_path / "grid.yaml"
    grid_path.write_text(f"name: smoke_grid_ref\nbase: {base_path.name}\nsweep: {{}}\n")

    grid = load_grid(grid_path)
    assert grid.base.name == "smoke_base"
    assert grid.base.universe.symbols == ["INFY"]

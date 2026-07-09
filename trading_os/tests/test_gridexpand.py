"""Grid expansion: dotted paths, signal-id addressing, validation, determinism."""

from __future__ import annotations

import pytest

from tradingos.config.gridexpand import expand_grid, expand_gridspec
from tradingos.config.schemas import (
    EngineMode,
    GridSpec,
    ScoreSpec,
    SelectionSpec,
    SignalSpec,
    StrategyConfig,
)
from tradingos.core.errors import ConfigError


def _base() -> StrategyConfig:
    return StrategyConfig(
        name="grid_base",
        signals=[SignalSpec(id="mom", name="return_over_window", params={"window": 252})],
        score=ScoreSpec(type="weighted_zscore", weights={"mom": 1.0}),
        selection=SelectionSpec(method="top_n", n=20, exit_rank=40),
    )


def test_empty_sweep_returns_base_untouched() -> None:
    base = _base()
    variants = expand_grid(base, {})
    assert len(variants) == 1
    assert variants[0].config is base
    assert variants[0].overrides == {}


def test_cartesian_product_count_and_deterministic_naming() -> None:
    sweep = {
        "signals.mom.params.window": [126, 189, 252],
        "selection.n": [10, 20],
    }
    variants = expand_grid(_base(), sweep)
    assert len(variants) == 6
    assert [v.config.name for v in variants] == [f"grid_base__{i:04d}" for i in range(6)]
    # keys sorted -> ["selection.n", "signals.mom.params.window"]; product
    # varies the LAST key fastest, so window cycles within each n value.
    assert variants[0].overrides == {"selection.n": 10, "signals.mom.params.window": 126}
    assert variants[1].overrides == {"selection.n": 10, "signals.mom.params.window": 189}
    assert variants[1].config.signals[0].params["window"] == 189
    assert variants[1].config.selection.n == 10
    # base is never mutated
    assert _base().selection.n == 20

    again = expand_grid(_base(), sweep)
    assert [v.overrides for v in again] == [v.overrides for v in variants]


def test_signal_id_addressing_errors_on_unknown_id() -> None:
    with pytest.raises(ConfigError, match="no signal with id 'nope'"):
        expand_grid(_base(), {"signals.nope.params.window": [10]})


def test_unknown_path_errors_loudly() -> None:
    with pytest.raises(ConfigError, match="does not exist"):
        expand_grid(_base(), {"selection.bogus_field": [1]})
    with pytest.raises(ConfigError, match="does not exist"):
        expand_grid(_base(), {"not_a_section.x": [1]})


def test_invalid_combo_fails_validation_naming_the_overrides() -> None:
    # exit_rank (40) < n (50) violates the SelectionSpec validator.
    with pytest.raises(ConfigError, match="selection.n.*50"):
        expand_grid(_base(), {"selection.n": [50]})


def test_empty_value_list_rejected() -> None:
    with pytest.raises(ConfigError, match="non-empty list"):
        expand_grid(_base(), {"selection.n": []})


def test_gridspec_engine_applied_to_every_variant() -> None:
    grid = GridSpec(
        name="g",
        base=_base(),
        sweep={"selection.n": [10, 20]},
        engine=EngineMode.VECTORIZED,
    )
    variants = expand_gridspec(grid)
    assert len(variants) == 2
    assert all(v.config.engine == EngineMode.VECTORIZED for v in variants)

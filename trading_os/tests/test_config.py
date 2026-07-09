from __future__ import annotations

from pathlib import Path

import pytest

from tradingos.config.loader import load_strategy
from tradingos.config.schemas import EngineMode, StrategyConfig
from tradingos.core.errors import ConfigError

MINIMAL_YAML = """
name: test_momentum
engine: event
capital: 500000
universe:
  symbols: [INFY, TCS, RELIANCE]
  point_in_time: false
signals:
  - {id: mom, name: return_over_window, params: {window: 252, skip: 21}}
  - {id: vol, name: realized_vol, params: {window: 63}}
score:
  type: weighted_zscore
  weights: {mom: 0.7, vol: -0.3}
selection: {method: top_n, n: 2, exit_rank: 3}
rebalance: {frequency: monthly, trading_day: 1}
"""


def test_load_minimal_strategy(tmp_path: Path) -> None:
    p = tmp_path / "s.yaml"
    p.write_text(MINIMAL_YAML)
    cfg = load_strategy(p)
    assert cfg.name == "test_momentum"
    assert cfg.engine == EngineMode.EVENT
    assert cfg.selection.exit_rank == 3
    assert cfg.signals[1].params == {"window": 63}
    assert cfg.execution.timing == "next_open"  # default: no look-ahead


def test_config_hash_stable_and_sensitive(tmp_path: Path) -> None:
    p = tmp_path / "s.yaml"
    p.write_text(MINIMAL_YAML)
    a, b = load_strategy(p), load_strategy(p)
    assert a.config_hash() == b.config_hash()
    b.capital = 999
    assert a.config_hash() != b.config_hash()


def test_score_referencing_unknown_signal_rejected() -> None:
    with pytest.raises(Exception, match="unknown signal ids"):
        StrategyConfig.model_validate(
            {
                "name": "bad",
                "signals": [{"id": "a", "name": "rsi"}],
                "score": {"type": "weighted_zscore", "weights": {"nope": 1.0}},
            }
        )


def test_exit_rank_below_n_rejected() -> None:
    with pytest.raises(Exception, match="exit_rank"):
        StrategyConfig.model_validate(
            {"name": "bad", "selection": {"method": "top_n", "n": 25, "exit_rank": 20}}
        )


def test_missing_file_clear_error() -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_strategy("does/not/exist.yaml")

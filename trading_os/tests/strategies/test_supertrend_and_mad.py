"""Unit tests: supertrend_bullish filter, ma_distance signal, regime-kind map.

PIT certification of both comes free from the registry sweep in
test_lookahead_detector.py; these tests cover behavior and known answers.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tradingos.config.schemas import RegimeSignalSpec
from tradingos.engine.event.strategy_runtime import _regime_signal_to_filter
from tradingos.strategies.registry import get_filter, get_signal


def _frame(close: np.ndarray) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=len(close), freq="B")
    return pd.DataFrame(
        {
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": np.full(len(close), 1_000.0),
        },
        index=idx,
    )


class TestSupertrendBullish:
    def test_steady_uptrend_turns_and_stays_true(self) -> None:
        close = np.linspace(100, 200, 300)
        out = get_filter("supertrend_bullish").fn(_frame(close), period=10, multiplier=3.0)
        assert out.dtype == bool
        assert not out.iloc[:10].any()  # ATR warm-up is False
        assert out.iloc[-1]
        # once flipped up in a monotone rise, it never flips back
        first_true = int(np.argmax(out.to_numpy()))
        assert out.iloc[first_true:].all()

    def test_crash_flips_state_false(self) -> None:
        close = np.concatenate([np.linspace(100, 200, 200), np.linspace(200, 120, 30)])
        out = get_filter("supertrend_bullish").fn(_frame(close), period=10, multiplier=3.0)
        assert out.iloc[199]  # bullish at the top
        assert not out.iloc[-1]  # 40% slide breaks the lower band

    def test_flat_series_stays_false_forever(self) -> None:
        close = np.full(120, 100.0)
        out = get_filter("supertrend_bullish").fn(_frame(close), period=10, multiplier=3.0)
        # close never exceeds hl2 + 3*ATR, so the bearish start never flips
        assert not out.any()

    def test_causality_future_bars_do_not_change_past_state(self) -> None:
        close = np.concatenate([np.linspace(100, 180, 200), np.linspace(180, 90, 50)])
        f = _frame(close)
        base = get_filter("supertrend_bullish").fn(f, period=10, multiplier=3.0)
        mutated = f.copy()
        mutated.iloc[220:, mutated.columns.get_indexer(["high", "low", "close"])] *= 3.0
        again = get_filter("supertrend_bullish").fn(mutated, period=10, multiplier=3.0)
        pd.testing.assert_series_equal(base.iloc[:220], again.iloc[:220])

    def test_bad_params_raise(self) -> None:
        with pytest.raises(ValueError):
            get_filter("supertrend_bullish").fn(_frame(np.full(30, 100.0)), period=0)
        with pytest.raises(ValueError):
            get_filter("supertrend_bullish").fn(_frame(np.full(30, 100.0)), multiplier=0.0)


class TestMaDistance:
    def test_known_answer_flat_then_step(self) -> None:
        close = np.concatenate([np.full(200, 100.0), np.full(50, 110.0)])
        out = get_signal("ma_distance").fn(_frame(close), fast=21, slow=200)
        assert out.iloc[:199].isna().all()  # slow SMA warm-up
        assert out.iloc[199] == pytest.approx(0.0)
        # after 21 bars at 110 the fast SMA is fully 110; slow blends 150/50
        expected = 110.0 / ((150 * 100.0 + 50 * 110.0) / 200) - 1.0
        assert out.iloc[249] == pytest.approx(expected, rel=1e-12)

    def test_bad_windows_raise(self) -> None:
        f = _frame(np.full(30, 100.0))
        with pytest.raises(ValueError):
            get_signal("ma_distance").fn(f, fast=0, slow=200)
        with pytest.raises(ValueError):
            get_signal("ma_distance").fn(f, fast=200, slow=200)


class TestRegimeKindMapping:
    def test_supertrend_kind_maps_with_defaults(self) -> None:
        name, params = _regime_signal_to_filter(RegimeSignalSpec(kind="supertrend"))
        assert name == "supertrend_bullish"
        assert params == {"period": 10, "multiplier": 3.0}

    def test_supertrend_kind_passes_params(self) -> None:
        spec = RegimeSignalSpec(kind="supertrend", params={"period": 14, "multiplier": 2.5})
        _, params = _regime_signal_to_filter(spec)
        assert params == {"period": 14, "multiplier": 2.5}

    def test_bad_supertrend_params_rejected_at_spec(self) -> None:
        with pytest.raises(ValueError):
            RegimeSignalSpec(kind="supertrend", params={"period": 0})
        with pytest.raises(ValueError):
            RegimeSignalSpec(kind="supertrend", params={"multiplier": -1})

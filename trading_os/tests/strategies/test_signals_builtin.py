"""Spot-checks for builtin (pandas-ta) signal wrappers.

`strategies/signals/builtin.py` is out of this task's scope (owned
separately) and is only a stub docstring as of this writing. These checks
are written against the *names* the platform spec calls out (rsi, sma, macd,
atr) but skip gracefully — rather than fail — when a given wrapper isn't
registered yet, so this suite goes green immediately and starts exercising
real assertions the moment builtin.py is populated. `test_lookahead_detector`
separately certifies every registered signal (including these) for the PIT
rule; this file is about shape/dtype/known-answer checks instead.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest
from fixtures.synthetic import synthetic_daily, trading_days

from tradingos.strategies import registry
from tradingos.strategies.registry import compute_signal


def _registered_names() -> set[str]:
    registry.ensure_discovered()
    return {d.name for d in registry.list_signals()}


def _has(name: str) -> bool:
    return name in _registered_names()


def test_every_builtin_signal_returns_aligned_float64_series() -> None:
    """Generic shape/dtype contract for whatever builtin.py currently
    registers, regardless of which specific indicators it ends up with."""
    registry.ensure_discovered()
    builtins = [d for d in registry.list_signals() if d.tier == "builtin"]
    if not builtins:
        pytest.skip("strategies/signals/builtin.py has not registered any signals yet")

    df = synthetic_daily("BUILTIN_SHAPE_TEST", start=date(2020, 1, 1), end=date(2022, 12, 31))
    for d in builtins:
        out = compute_signal(d.name, df, {})
        assert isinstance(out, pd.Series), d.name
        assert len(out) == len(df), d.name
        assert (out.index == df.index).all(), d.name
        assert out.dtype == np.float64, d.name


def test_rsi_is_bounded_zero_to_hundred_once_warmed_up() -> None:
    if not _has("rsi"):
        pytest.skip("builtin.py has not registered 'rsi' yet")
    df = synthetic_daily("RSI_TEST", start=date(2020, 1, 1), end=date(2022, 12, 31))
    out = compute_signal("rsi", df, {})
    assert isinstance(out, pd.Series)
    assert len(out) == len(df)

    warmed = out.dropna()
    assert not warmed.empty, "rsi should produce values once warmed up on 3y of daily data"
    assert warmed.between(0, 100).all(), "RSI must lie in [0, 100]"


def test_sma_of_a_constant_series_equals_the_constant() -> None:
    """Hand-checkable known-answer case: the simple moving average of a
    perfectly flat price series is that same constant, once warmed up."""
    if not _has("sma"):
        pytest.skip("builtin.py has not registered 'sma' yet")
    idx = trading_days(date(2021, 1, 1), date(2021, 6, 30))
    const_df = pd.DataFrame(
        {
            "open": 100.0,
            "high": 100.0,
            "low": 100.0,
            "close": 100.0,
            "volume": 1_000_000,
        },
        index=idx,
    )
    out = compute_signal("sma", const_df, {"length": 10})
    warmed = out.dropna()
    assert not warmed.empty
    assert np.allclose(warmed.to_numpy(), 100.0)


def test_atr_is_non_negative_once_warmed_up() -> None:
    if not _has("atr"):
        pytest.skip("builtin.py has not registered 'atr' yet")
    df = synthetic_daily("ATR_TEST", start=date(2020, 1, 1), end=date(2022, 12, 31))
    out = compute_signal("atr", df, {})
    warmed = out.dropna()
    assert not warmed.empty
    assert (warmed >= 0).all(), "Average True Range cannot be negative"


def test_macd_line_shape_and_dtype() -> None:
    if not _has("macd"):
        pytest.skip("builtin.py has not registered 'macd' yet")
    df = synthetic_daily("MACD_TEST", start=date(2020, 1, 1), end=date(2022, 12, 31))
    out = compute_signal("macd", df, {})
    assert isinstance(out, pd.Series)
    assert len(out) == len(df)
    assert out.dtype == np.float64
    assert out.dropna().shape[0] > 0

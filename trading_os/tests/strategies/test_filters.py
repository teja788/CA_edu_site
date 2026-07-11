"""Known-answer tests for the whipsaw-reduction filters (band hysteresis,
N-day confirmation, golden cross). Causality of every registered filter is
certified separately by the look-ahead detector suite."""

from __future__ import annotations

import pandas as pd

from tradingos.strategies.filters import (
    above_ma_band,
    above_ma_confirm,
    fast_ma_above_slow_ma,
)


def _frame(closes: list[float]) -> pd.DataFrame:
    idx = pd.date_range("2021-01-01", periods=len(closes), freq="B")
    return pd.DataFrame(
        {
            "open": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
            "close": closes,
            "volume": [1000] * len(closes),
        },
        index=idx,
    )


# ---------------------------------------------------------------------------
# above_ma_band
# ---------------------------------------------------------------------------


def test_band_holds_state_inside_dead_zone() -> None:
    # window=3; the rolling MA includes the current bar.
    # 104: MA=101.33, entry=103.36 -> ON. 101: MA=101.67, band [99.63,103.70]
    # -> held. 100: MA=101.67, exit=99.63 -> held. 95: MA=98.67, exit=96.69
    # -> OFF. 100: MA=98.33, band [96.36,100.30] -> held OFF.
    closes = [100.0, 100.0, 100.0, 104.0, 101.0, 100.0, 95.0, 100.0]
    out = above_ma_band(_frame(closes), window=3, entry_mult=1.02, exit_mult=0.98)
    # warm-up rows (need 3 bars) are False
    assert not out.iloc[0] and not out.iloc[1]
    assert not out.iloc[2]          # 100 == MA, not above entry band
    assert out.iloc[3]              # 104 clears the entry band -> ON
    assert out.iloc[4]              # 101: dead zone -> held ON
    assert out.iloc[5]              # 100: dead zone -> held ON
    assert not out.iloc[6]          # 95 breaks the exit band -> OFF
    assert not out.iloc[7]          # 100: dead zone -> held OFF


def test_band_false_during_warmup_and_all_nan_safe() -> None:
    out = above_ma_band(_frame([100.0, 101.0]), window=200)
    assert not out.any()
    assert out.dtype == bool


# ---------------------------------------------------------------------------
# above_ma_confirm
# ---------------------------------------------------------------------------


def test_confirm_needs_n_consecutive_closes() -> None:
    # window=2. One bar above then a dip must NOT flip ON with days=2;
    # two consecutive closes above must.
    closes = [100.0, 100.0, 104.0, 99.0, 104.0, 106.0, 90.0, 89.0, 88.0]
    out = above_ma_confirm(_frame(closes), window=2, days=2)
    assert not out.iloc[2]  # first close above: run == 1 < 2
    assert not out.iloc[3]  # dipped back: run reset
    assert not out.iloc[4]  # above again: run == 1
    assert out.iloc[5]      # second consecutive above -> ON
    assert out.iloc[6]      # one close below: run == 1 -> still ON
    assert not out.iloc[7]  # second consecutive below -> OFF
    assert not out.iloc[8]


# ---------------------------------------------------------------------------
# fast_ma_above_slow_ma
# ---------------------------------------------------------------------------


def test_golden_cross_warmup_and_cross() -> None:
    # 5 flat bars warm both windows (fast=2, slow=4), then a steady rise
    # lifts the fast MA above the slow one.
    closes = [100.0, 100.0, 100.0, 100.0, 100.0, 110.0, 120.0, 130.0]
    out = fast_ma_above_slow_ma(_frame(closes), fast=2, slow=4)
    assert not out.iloc[:4].any()   # slow MA needs 4 bars; warm-up is False
    assert not out.iloc[4]          # flat: fast == slow, not strictly above
    assert out.iloc[5] and out.iloc[6] and out.iloc[7]


def test_golden_cross_turns_false_in_downtrend() -> None:
    closes = [130.0, 120.0, 110.0, 100.0, 90.0, 80.0, 70.0, 60.0]
    out = fast_ma_above_slow_ma(_frame(closes), fast=2, slow=4)
    assert not out.iloc[3:].any()

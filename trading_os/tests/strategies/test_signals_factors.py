"""Known-answer tests for `strategies/signals/factors.py`.

CLAUDE.md hard rule 5 requires known-answer tests for critical financial
math. Every arithmetic fixture below is small (5-8 rows) and its expected
value is derived by hand in a comment next to the assertion — most as exact
rational/decimal arithmetic (no floating point roundoff to worry about,
`pytest.approx` still guards the sub-ulp noise from `**`/`pct_change`), one
(`realized_vol` / `risk_adjusted_momentum`) via an explicit ddof=1
variance derivation reduced to a clean fraction (1/75) so the annualized
value is `sqrt(252/75)` — shown step by step below.

Look-ahead safety (PIT) for these signals is NOT re-tested here: every
signal registered anywhere, including these five, is certified by the
shared `tests/strategies/test_lookahead_detector.py` suite. This file is
about shape/dtype/known-answer correctness instead, mirroring
`test_signals_builtin.py`'s division of labor.
"""

from __future__ import annotations

import math
from datetime import date

import numpy as np
import pandas as pd
import pytest
from fixtures.synthetic import synthetic_daily

from tradingos.strategies import registry
from tradingos.strategies.registry import compute_signal

_FACTOR_NAMES = (
    "return_over_window",
    "realized_vol",
    "risk_adjusted_momentum",
    "distance_from_52w_high",
    "return_smoothness",
)


def _idx(n: int) -> pd.DatetimeIndex:
    """n consecutive business days, tz-naive, starting on a Monday."""
    return pd.bdate_range(date(2021, 1, 4), periods=n)


def _frame(closes: list[float], total_return_close: list[float] | None = None) -> pd.DataFrame:
    idx = _idx(len(closes))
    data = {"close": closes}
    if total_return_close is not None:
        data["total_return_close"] = total_return_close
    return pd.DataFrame(data, index=idx)


# ---------------------------------------------------------------------------
# registration sanity
# ---------------------------------------------------------------------------


def test_all_five_factors_are_registered_with_factor_tier() -> None:
    registry.ensure_discovered()
    registered = {d.name: d for d in registry.list_signals()}
    for name in _FACTOR_NAMES:
        assert name in registered, f"{name} is not registered"
        assert registered[name].tier == "factor", f"{name} should be tier='factor'"


def test_every_factor_returns_aligned_float64_series() -> None:
    df = synthetic_daily("FACTORS_SHAPE_TEST", start=date(2020, 1, 1), end=date(2022, 12, 31))
    for name in _FACTOR_NAMES:
        out = compute_signal(name, df, {})
        assert isinstance(out, pd.Series), name
        assert len(out) == len(df), name
        assert (out.index == df.index).all(), name
        assert out.dtype == np.float64, name


# ---------------------------------------------------------------------------
# return_over_window
# ---------------------------------------------------------------------------


def test_return_over_window_hand_computed_with_skip() -> None:
    # closes[i] = 100 * 1.1**i for i in 0..5: constant +10%/day compounding.
    closes = [100.0, 110.0, 121.0, 133.1, 146.41, 161.051]
    df = _frame(closes)
    out = compute_signal("return_over_window", df, {"window": 4, "skip": 1})

    # window=4, skip=1: P[t-1] / P[t-4] - 1. Over any 3-bar gap on this
    # series the return is exactly 1.1**3 - 1 = 0.331 (constant, since the
    # daily growth rate is constant), independent of where the 3-bar window
    # sits:
    #   t=4: P[3]/P[0] - 1 = 133.1/100 - 1 = 0.331
    #   t=5: P[4]/P[1] - 1 = 146.41/110 - 1 = 0.331
    assert out.iloc[4] == pytest.approx(0.331)
    assert out.iloc[5] == pytest.approx(0.331)
    # rows 0-3: P.shift(4) has fewer than 4 prior rows -> NaN
    assert out.iloc[:4].isna().all()


def test_return_over_window_prefers_total_return_close_over_close() -> None:
    # close is flat (0% every day); total_return_close carries the same
    # +10%/day growth as the fixture above. A momentum factor must rank on
    # total-return, not the (possibly dividend-suppressed) raw close.
    flat_close = [100.0] * 6
    tr_close = [100.0, 110.0, 121.0, 133.1, 146.41, 161.051]
    df = _frame(flat_close, total_return_close=tr_close)
    out = compute_signal("return_over_window", df, {"window": 4, "skip": 1})

    # Same arithmetic as the previous test, now sourced from
    # total_return_close: 0.331 at t=4 and t=5, NOT 0.0 (which is what
    # plain `close` would give).
    assert out.iloc[4] == pytest.approx(0.331)
    assert out.iloc[5] == pytest.approx(0.331)


def test_return_over_window_requires_window_greater_than_skip() -> None:
    df = _frame([100.0, 101.0, 102.0, 103.0, 104.0])
    with pytest.raises(ValueError, match="window > skip >= 0"):
        compute_signal("return_over_window", df, {"window": 3, "skip": 3})
    with pytest.raises(ValueError, match="window > skip >= 0"):
        compute_signal("return_over_window", df, {"window": 3, "skip": 5})
    with pytest.raises(ValueError, match="window > skip >= 0"):
        compute_signal("return_over_window", df, {"window": 3, "skip": -1})


# ---------------------------------------------------------------------------
# realized_vol
# ---------------------------------------------------------------------------


def test_realized_vol_matches_hand_computed_std() -> None:
    # closes -> daily returns of exactly +10%, -10%, +10% (clean decimals:
    # 100->110 is +0.10, 110->99 is -0.10, 99->108.9 is +0.10).
    closes = [100.0, 110.0, 99.0, 108.9]
    df = _frame(closes)
    out = compute_signal("realized_vol", df, {"window": 3})

    # r = [0.10, -0.10, 0.10]; mean = 0.10/3 = 1/30.
    # deviations: 1/10-1/30=1/15, -1/10-1/30=-2/15, 1/10-1/30=1/15
    # sum of squares = 1/225 + 4/225 + 1/225 = 6/225 = 2/75
    # variance (ddof=1, n=3) = (2/75) / 2 = 1/75
    # std = sqrt(1/75); annualized = sqrt(1/75) * sqrt(252) = sqrt(252/75)
    expected = math.sqrt(252 / 75)
    assert out.iloc[3] == pytest.approx(expected)
    # fewer than `window`=3 return observations before row 3 -> NaN
    assert out.iloc[:3].isna().all()


def test_realized_vol_of_a_flat_series_is_exactly_zero() -> None:
    df = _frame([100.0] * 6)
    out = compute_signal("realized_vol", df, {"window": 3})
    warmed = out.dropna()
    assert not warmed.empty
    assert (warmed == 0.0).all()


# ---------------------------------------------------------------------------
# risk_adjusted_momentum
# ---------------------------------------------------------------------------


def test_risk_adjusted_momentum_is_the_ratio_of_its_two_components() -> None:
    closes = [100.0, 110.0, 99.0, 108.9]
    df = _frame(closes)
    ram_params = {"window": 3, "skip": 0, "vol_window": 3}

    ret = compute_signal("return_over_window", df, {"window": 3, "skip": 0})
    vol = compute_signal("realized_vol", df, {"window": 3})
    ram = compute_signal("risk_adjusted_momentum", df, ram_params)

    # return_over_window(window=3, skip=0) at t=3: close[3]/close[0] - 1
    #   = 108.9/100 - 1 = 0.089 exactly
    assert ret.iloc[3] == pytest.approx(0.089)
    # realized_vol(window=3) at t=3: sqrt(252/75), from the previous test
    assert vol.iloc[3] == pytest.approx(math.sqrt(252 / 75))
    # ratio: 0.089 / sqrt(252/75)
    assert ram.iloc[3] == pytest.approx(0.089 / math.sqrt(252 / 75))
    assert ram.iloc[3] == pytest.approx(ret.iloc[3] / vol.iloc[3])


def test_risk_adjusted_momentum_is_nan_when_vol_is_exactly_zero() -> None:
    # a perfectly flat close series: return_over_window is 0.0 (well
    # defined, P[t]/P[t-window]-1 = 100/100-1 = 0), but realized_vol is
    # exactly 0.0 (zero variance) -> the ratio must be NaN, not +/-inf and
    # not a silently "correct-looking" 0.0/0.0 = nan-by-luck value.
    df = _frame([100.0] * 6)

    ret = compute_signal("return_over_window", df, {"window": 3, "skip": 0})
    assert ret.iloc[3] == pytest.approx(0.0)

    ram = compute_signal(
        "risk_adjusted_momentum", df, {"window": 3, "skip": 0, "vol_window": 3}
    )
    assert math.isnan(ram.iloc[3])
    assert math.isnan(ram.iloc[4])
    assert math.isnan(ram.iloc[5])


def test_risk_adjusted_momentum_requires_window_greater_than_skip() -> None:
    df = _frame([100.0, 101.0, 102.0, 103.0, 104.0])
    with pytest.raises(ValueError, match="window > skip >= 0"):
        compute_signal(
            "risk_adjusted_momentum", df, {"window": 3, "skip": 3, "vol_window": 3}
        )


# ---------------------------------------------------------------------------
# distance_from_52w_high
# ---------------------------------------------------------------------------


def test_distance_from_52w_high_is_zero_on_a_monotonic_increasing_series() -> None:
    # every close is a new running high, so close IS the rolling max at
    # every warmed-up row -> distance is exactly 0.0 throughout.
    closes = [100.0, 105.0, 110.0, 115.0, 120.0]
    df = _frame(closes)
    out = compute_signal("distance_from_52w_high", df, {"window": 3})

    assert out.iloc[2] == pytest.approx(0.0)
    assert out.iloc[3] == pytest.approx(0.0)
    assert out.iloc[4] == pytest.approx(0.0)
    assert out.iloc[:2].isna().all()


def test_distance_from_52w_high_on_a_peak_then_fall_series() -> None:
    closes = [100.0, 120.0, 90.0, 80.0, 70.0]
    df = _frame(closes)
    out = compute_signal("distance_from_52w_high", df, {"window": 3})

    # t=2: window = [100,120,90], max=120, close=90 -> 90/120 - 1 = -0.25
    assert out.iloc[2] == pytest.approx(-0.25)
    # t=3: window = [120,90,80], max=120, close=80 -> 80/120 - 1 = -1/3
    assert out.iloc[3] == pytest.approx(-1.0 / 3.0)
    # t=4: window = [90,80,70], max=90, close=70 -> 70/90 - 1 = -2/9
    assert out.iloc[4] == pytest.approx(-2.0 / 9.0)

    warmed = out.dropna()
    assert (warmed >= -1.0).all() and (warmed <= 0.0).all()


# ---------------------------------------------------------------------------
# return_smoothness
# ---------------------------------------------------------------------------


def test_return_smoothness_smooth_uptrend_scores_higher_than_jumpy_same_return() -> None:
    # Both series start at 100 and end at 121.550625 (total return exactly
    # +21.550625%), so any score difference is attributable to smoothness,
    # not to a different total return.
    smooth_up = [100.0, 105.0, 110.25, 115.7625, 121.550625]  # +5%/day, every day
    jumpy_up = [100.0, 95.0, 90.0, 85.0, 121.550625]  # 3 down days + 1 big up jump

    df_smooth = _frame(smooth_up)
    df_jumpy = _frame(jumpy_up)
    out_smooth = compute_signal("return_smoothness", df_smooth, {"window": 4})
    out_jumpy = compute_signal("return_smoothness", df_jumpy, {"window": 4})

    # smooth: r = [0.05]*4 -> pct_pos=1.0, pct_neg=0.0, cum_ret=+0.2155>0
    # -> sign=+1, ID = 1*(0-1) = -1, signal = -ID = 1.0
    assert out_smooth.iloc[4] == pytest.approx(1.0)
    # jumpy: r = [-0.05, -0.0526.., -0.0556.., +0.4300..] -> pct_pos=0.25,
    # pct_neg=0.75, cum_ret=+0.2155>0 -> sign=+1,
    # ID = 1*(0.75-0.25) = 0.5, signal = -ID = -0.5
    assert out_jumpy.iloc[4] == pytest.approx(-0.5)
    assert out_smooth.iloc[4] > out_jumpy.iloc[4]

    # confirm the "same total return" premise via return_over_window
    ret_smooth = compute_signal("return_over_window", df_smooth, {"window": 4, "skip": 0})
    ret_jumpy = compute_signal("return_over_window", df_jumpy, {"window": 4, "skip": 0})
    assert ret_smooth.iloc[4] == pytest.approx(ret_jumpy.iloc[4])


def test_return_smoothness_is_symmetric_for_downtrends() -> None:
    # Mirror image of the uptrend case: both start at 100 and end at
    # 81.450625 (total return exactly -18.549375%).
    smooth_down = [100.0, 95.0, 90.25, 85.7375, 81.450625]  # -5%/day, every day
    jumpy_down = [100.0, 105.0, 110.0, 115.0, 81.450625]  # 3 up days + 1 big down jump

    df_smooth = _frame(smooth_down)
    df_jumpy = _frame(jumpy_down)
    out_smooth = compute_signal("return_smoothness", df_smooth, {"window": 4})
    out_jumpy = compute_signal("return_smoothness", df_jumpy, {"window": 4})

    # smooth: r = [-0.05]*4 -> pct_pos=0.0, pct_neg=1.0, cum_ret=-0.1855<0
    # -> sign=-1, ID = -1*(1-0) = -1, signal = -ID = 1.0
    # (same score as the smooth UPtrend case: only smoothness matters here)
    assert out_smooth.iloc[4] == pytest.approx(1.0)
    # jumpy: r = [0.05, 0.0476.., 0.0455.., -0.2917..] -> pct_pos=0.75,
    # pct_neg=0.25, cum_ret=-0.1855<0 -> sign=-1,
    # ID = -1*(0.25-0.75) = 0.5, signal = -ID = -0.5
    assert out_jumpy.iloc[4] == pytest.approx(-0.5)
    assert out_smooth.iloc[4] > out_jumpy.iloc[4]

    ret_smooth = compute_signal("return_over_window", df_smooth, {"window": 4, "skip": 0})
    ret_jumpy = compute_signal("return_over_window", df_jumpy, {"window": 4, "skip": 0})
    assert ret_smooth.iloc[4] == pytest.approx(ret_jumpy.iloc[4])


def test_return_smoothness_min_periods_gates_the_structural_nan() -> None:
    # close.pct_change() has exactly one structural NaN (row 0, no prior
    # close); min_periods=window must gate every window that still
    # contains it, leaving only the last row valid on a 5-row/window=4 frame.
    closes = [100.0, 105.0, 110.25, 115.7625, 121.550625]
    df = _frame(closes)
    out = compute_signal("return_smoothness", df, {"window": 4})
    assert out.iloc[:4].isna().all()
    assert not math.isnan(out.iloc[4])

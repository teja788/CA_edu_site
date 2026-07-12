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


# ---------------------------------------------------------------------------
# residual_momentum (Blitz, Huij & Martens 2011): 12-1 momentum of
# market-model residuals, standardized by residual sigma. Needs a
# `benchmark_close` column (routed by the engine from the SignalSpec
# `benchmark` field).
# ---------------------------------------------------------------------------


def _closes_from_returns(r: np.ndarray, s0: float = 100.0) -> np.ndarray:
    """Price path whose simple returns are exactly ``r`` (r[0] is ignored)."""
    c = np.empty(len(r), dtype="float64")
    c[0] = s0
    for i in range(1, len(r)):
        c[i] = c[i - 1] * (1.0 + r[i])
    return c


def _resid_mom_frame(r_bench: np.ndarray, r_stock: np.ndarray) -> pd.DataFrame:
    idx = _idx(len(r_bench))
    return pd.DataFrame(
        {
            "close": _closes_from_returns(r_stock),
            "benchmark_close": _closes_from_returns(r_bench),
        },
        index=idx,
    )


def _resid_mom_oracle(
    df: pd.DataFrame, window: int, skip: int, beta_window: int
) -> np.ndarray:
    """Independent brute-force oracle: an explicit per-window OLS + 12-1
    aggregation, deliberately written with Python loops (allowed in tests) so
    it shares no code path with the vectorized implementation under test."""
    rs = df["close"].pct_change().to_numpy()
    rb = df["benchmark_close"].pct_change().to_numpy()
    n = len(df)
    resid = np.full(n, np.nan)
    for t in range(n):
        lo = t - beta_window + 1
        if lo < 0:
            continue
        ys, xs = rs[lo : t + 1], rb[lo : t + 1]
        if np.isnan(ys).any() or np.isnan(xs).any():
            continue
        xbar, ybar = xs.mean(), ys.mean()
        varx = ((xs - xbar) ** 2).sum() / (len(xs) - 1)
        if varx == 0:
            continue
        beta = ((xs - xbar) * (ys - ybar)).sum() / (len(xs) - 1) / varx
        alpha = ybar - beta * xbar
        resid[t] = ys[-1] - (alpha + beta * xs[-1])
    e_skip = pd.Series(resid).shift(skip).to_numpy()
    out = np.full(n, np.nan)
    for t in range(n):
        lo = t - window + 1
        if lo < 0:
            continue
        w = e_skip[lo : t + 1]
        if np.isnan(w).any():
            continue
        sd = w.std(ddof=1)
        if sd == 0:
            continue
        out[t] = w.sum() / sd
    return out


def test_residual_momentum_registered_as_factor_tier() -> None:
    registry.ensure_discovered()
    registered = {d.name: d for d in registry.list_signals()}
    assert "residual_momentum" in registered
    assert registered["residual_momentum"].tier == "factor"


def test_residual_momentum_matches_an_independent_ols_oracle() -> None:
    # Known-answer via an oracle: the vectorized rolling-OLS implementation must
    # reproduce an explicit per-window ordinary-least-squares fit + 12-1
    # aggregation on a seeded frame, everywhere the oracle is defined.
    rng = np.random.default_rng(0)
    n = 400
    r_bench = 0.01 * rng.standard_normal(n)
    r_bench[0] = 0.0
    r_stock = 1.3 * r_bench + 0.003 * rng.standard_normal(n)
    r_stock[0] = 0.0
    df = _resid_mom_frame(r_bench, r_stock)

    params = {"window": 60, "skip": 5, "beta_window": 40}
    out = compute_signal("residual_momentum", df, params).to_numpy()
    oracle = _resid_mom_oracle(df, **params)

    valid = ~np.isnan(oracle)
    assert valid.sum() > 250  # the oracle is defined over most of the frame
    np.testing.assert_allclose(out[valid], oracle[valid], rtol=1e-9, atol=1e-11)
    # NaN structure agrees too (warm-up region)
    assert np.array_equal(np.isnan(out), np.isnan(oracle))


def test_residual_momentum_recovers_the_residual_drift_direction() -> None:
    # Construct r_stock = beta*r_bench + residual. A residual that RAMPS UP over
    # time leaves recent residuals above their trailing mean (which alpha
    # absorbs) -> positive residual momentum; a ramp DOWN -> negative. A
    # pure-beta stock whose only residual is a zero-drift alternation scores ~0.
    rng = np.random.default_rng(0)
    n = 400
    r_bench = 0.01 * rng.standard_normal(n)
    r_bench[0] = 0.0
    params = {"window": 120, "skip": 10, "beta_window": 120}

    ramp = np.linspace(0.0, 0.02, n)
    up = _resid_mom_frame(r_bench, 1.3 * r_bench + ramp)
    down = _resid_mom_frame(r_bench, 1.3 * r_bench - ramp)
    # zero-drift residual: a mean-zero alternation (nonzero dispersion so the
    # standardization is defined, but its trailing sum ~cancels).
    alt = 0.005 * ((-1.0) ** np.arange(n))
    flat = _resid_mom_frame(r_bench, 1.3 * r_bench + alt)

    s_up = compute_signal("residual_momentum", up, params).iloc[-1]
    s_down = compute_signal("residual_momentum", down, params).iloc[-1]
    s_flat = compute_signal("residual_momentum", flat, params).iloc[-1]

    assert s_up > 100.0  # strongly positive: recent residuals sit above trend
    assert s_down < -100.0  # symmetric, strongly negative
    assert s_up == pytest.approx(-s_down, rel=1e-3)  # the two are mirror images
    # the pure-beta (zero residual DRIFT) stock scores near zero, orders of
    # magnitude smaller than the drifted stocks.
    assert abs(s_flat) < 5.0


def test_residual_momentum_raises_without_a_benchmark_close_column() -> None:
    df = _frame([100.0, 101.0, 102.0, 103.0, 104.0])  # no benchmark_close
    with pytest.raises(ValueError, match="benchmark_close"):
        compute_signal("residual_momentum", df, {"window": 3, "skip": 0, "beta_window": 3})


def test_residual_momentum_rejects_bad_windows() -> None:
    df = _resid_mom_frame(np.zeros(6), np.zeros(6))
    with pytest.raises(ValueError, match="window > skip >= 0"):
        compute_signal("residual_momentum", df, {"window": 3, "skip": 3, "beta_window": 3})
    with pytest.raises(ValueError, match="beta_window >= 2"):
        compute_signal("residual_momentum", df, {"window": 3, "skip": 0, "beta_window": 1})


def test_residual_momentum_nan_until_warmed_up() -> None:
    rng = np.random.default_rng(1)
    n = 300
    r_bench = 0.01 * rng.standard_normal(n)
    r_bench[0] = 0.0
    df = _resid_mom_frame(r_bench, 1.1 * r_bench + 0.002 * rng.standard_normal(n))
    window, skip, beta_window = 100, 5, 80
    out = compute_signal(
        "residual_momentum", df, {"window": window, "skip": skip, "beta_window": beta_window}
    )
    # first fully-warmed row: beta_window returns start at index 1 (row 0's
    # return is NaN), so residuals begin at index beta_window; shift(skip)
    # pushes that to beta_window+skip; a full `window` of them ends at
    # beta_window + skip + window - 1.
    first_valid = beta_window + skip + window - 1
    assert out.iloc[:first_valid].isna().all()
    assert not math.isnan(out.iloc[first_valid])

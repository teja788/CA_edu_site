"""Known-answer tests for analytics/metrics.py.

Every non-trivial expectation is a hand-computed literal with the arithmetic
written out in a comment, in the style of tests/engine/test_event_ledger.py.
Financial math has exactly one home (CLAUDE.md rule 5); these tests pin it.
"""

from __future__ import annotations

import math
from datetime import date, datetime

import numpy as np
import pandas as pd
import pytest
from fixtures.synthetic import synthetic_daily

from tradingos.analytics.metrics import (
    _METRIC_KEYS,
    compute_metrics,
    drawdown_series,
    monthly_returns,
    rolling_sharpe,
    top_drawdowns,
    yearly_returns,
)
from tradingos.config.schemas import EngineMode
from tradingos.core.models import Trade
from tradingos.engine.result import BacktestResult

_SQRT252 = math.sqrt(252)


def _result(
    equity: pd.Series,
    trades: list[Trade] | None = None,
    total_costs: float = 0.0,
    capital: float | None = None,
) -> BacktestResult:
    """Minimal BacktestResult for metrics tests.

    BacktestResult is a plain dataclass and compute_metrics never reads
    ``config``, so we pass ``config=None`` to keep fixtures decoupled from the
    (large) StrategyConfig schema.
    """
    cap = float(equity.iloc[0]) if capital is None else capital
    return BacktestResult(
        config=None,  # type: ignore[arg-type]  # unused by compute_metrics
        engine=EngineMode.EVENT,
        start=equity.index[0].date(),
        end=equity.index[-1].date(),
        capital=cap,
        equity=equity,
        gross_equity=equity,
        trades=trades or [],
        total_costs=total_costs,
    )


def _trade(
    *,
    qty: int,
    entry: float,
    exit_: float,
    entry_ts: datetime,
    exit_ts: datetime,
    entry_costs: float = 0.0,
    exit_costs: float = 0.0,
    symbol: str = "X",
) -> Trade:
    return Trade(
        symbol=symbol,
        qty=qty,
        entry_ts=entry_ts,
        exit_ts=exit_ts,
        entry_price=entry,
        exit_price=exit_,
        entry_costs=entry_costs,
        exit_costs=exit_costs,
    )


# --------------------------------------------------------------------------- #
# Core return/risk metrics on a tiny hand-computed equity path                 #
# --------------------------------------------------------------------------- #
def test_scalar_metrics_on_hand_computed_equity() -> None:
    # equity 100 -> 110 -> 99 -> 108.9 on four consecutive calendar days.
    # returns = [110/100-1, 99/110-1, 108.9/99-1] = [+0.10, -0.10, +0.10]
    idx = pd.date_range("2020-01-01", periods=4, freq="D")
    eq = pd.Series([100.0, 110.0, 99.0, 108.9], index=idx)
    m = compute_metrics(_result(eq, total_costs=0.0, capital=100.0))

    # total_return = 108.9/100 - 1 = 0.089
    assert m["total_return"] == pytest.approx(0.089)
    # cagr = (108.9/100)^(252/3) - 1
    assert m["cagr"] == pytest.approx((1.089) ** (252 / 3) - 1.0)

    r = np.array([0.10, -0.10, 0.10])
    # mean = 0.0333333 ; std(ddof=1) = 0.1154701
    # vol = std * sqrt(252) = 1.83303...
    assert m["vol"] == pytest.approx(r.std(ddof=1) * _SQRT252)
    # sharpe = mean/std * sqrt(252) = 4.582576
    assert m["sharpe"] == pytest.approx(r.mean() / r.std(ddof=1) * _SQRT252)
    # sortino: downside_dev = sqrt(mean([0, 0.01, 0])) = sqrt(0.0033333) = 0.0577350
    # sortino = mean/downside_dev * sqrt(252) = 9.165151
    downside = np.minimum(r, 0.0)
    assert m["sortino"] == pytest.approx(
        r.mean() / math.sqrt((downside**2).mean()) * _SQRT252
    )

    # cummax = [100,110,110,110]; dd = [0,0,99/110-1,108.9/110-1] = [0,0,-0.10,-0.01]
    assert m["max_drawdown"] == pytest.approx(-0.10)
    # peak 110 at day 2 never recovers -> underwater to last bar: day4 - day2 = 2 days
    assert m["max_dd_duration_days"] == 2.0
    # calmar = cagr / |max_dd| = cagr / 0.10
    assert m["calmar"] == pytest.approx(m["cagr"] / 0.10)

    # no trades -> trade-derived metrics NaN
    for key in ("hit_rate", "turnover", "avg_holding_days", "exposure"):
        assert math.isnan(m[key])
    assert m["n_trades"] == 0.0
    # no benchmark -> alpha/beta NaN
    assert math.isnan(m["alpha"]) and math.isnan(m["beta"])
    # costs 0 / capital 100 = 0
    assert m["total_costs_pct"] == 0.0
    assert m["final_equity"] == pytest.approx(108.9)


def test_total_costs_pct_uses_capital() -> None:
    idx = pd.date_range("2020-01-01", periods=3, freq="D")
    eq = pd.Series([100_000.0, 101_000.0, 100_500.0], index=idx)
    # total_costs 250 / capital 100000 = 0.0025
    m = compute_metrics(_result(eq, total_costs=250.0, capital=100_000.0))
    assert m["total_costs_pct"] == pytest.approx(0.0025)


# --------------------------------------------------------------------------- #
# Drawdown depth & duration on a deterministic two-peak path                    #
# --------------------------------------------------------------------------- #
def test_two_peak_drawdown_depth_and_duration() -> None:
    # 100,110,100,120,60,90,120 over 7 consecutive days.
    # cummax   = 100,110,110,120,120,120,120
    # drawdown = 0, 0, -0.0909, 0, -0.50, -0.25, 0
    idx = pd.date_range("2021-03-01", periods=7, freq="D")
    eq = pd.Series([100.0, 110.0, 100.0, 120.0, 60.0, 90.0, 120.0], index=idx)
    m = compute_metrics(_result(eq))

    # deepest point is 60 from a peak of 120: 60/120 - 1 = -0.50
    assert m["max_drawdown"] == pytest.approx(-0.50)
    # Two episodes: 110->100->120 spans day2->day4 (2 days); 120->60->90->120
    # spans day4->day7 (3 days). Longest peak-to-recovery = 3 calendar days.
    assert m["max_dd_duration_days"] == 3.0


def test_top_drawdowns_ranks_and_bounds() -> None:
    idx = pd.date_range("2021-03-01", periods=7, freq="D")
    eq = pd.Series([100.0, 110.0, 100.0, 120.0, 60.0, 90.0, 120.0], index=idx)
    td = top_drawdowns(eq)
    assert list(td.columns) == ["peak", "trough", "recovery", "depth", "days"]
    # deepest episode first: depth -0.50, peak day4 (120), trough day5 (60),
    # recovery day7 (120), duration 3 days.
    assert td.iloc[0]["depth"] == pytest.approx(-0.50)
    assert td.iloc[0]["peak"] == idx[3]
    assert td.iloc[0]["trough"] == idx[4]
    assert td.iloc[0]["recovery"] == idx[6]
    assert td.iloc[0]["days"] == 3.0
    # second episode shallower
    assert td.iloc[1]["depth"] == pytest.approx(100.0 / 110.0 - 1.0)


def test_top_drawdowns_unrecovered_has_nat_recovery() -> None:
    # ends underwater: 100,120,90 -> peak 120 never regained
    idx = pd.date_range("2021-04-01", periods=3, freq="D")
    eq = pd.Series([100.0, 120.0, 90.0], index=idx)
    td = top_drawdowns(eq)
    assert pd.isna(td.iloc[0]["recovery"])  # NaT — never recovered
    assert td.iloc[0]["peak"] == idx[1]
    # days = peak(day2) -> last bar(day3) = 1 calendar day
    assert td.iloc[0]["days"] == 1.0


def test_drawdown_series_values() -> None:
    idx = pd.date_range("2020-01-01", periods=4, freq="D")
    eq = pd.Series([100.0, 110.0, 99.0, 108.9], index=idx)
    dd = drawdown_series(eq)
    # equity/cummax - 1 = [0, 0, -0.10, -0.01]
    assert list(np.round(dd.to_numpy(), 6)) == [0.0, 0.0, -0.10, -0.01]


# --------------------------------------------------------------------------- #
# Trade-derived metrics: hit rate, turnover, exposure, holding                  #
# --------------------------------------------------------------------------- #
def test_hit_rate_counts_strictly_positive_net_pnl() -> None:
    idx = pd.date_range("2020-01-01", periods=2, freq="D")
    eq = pd.Series([1000.0, 1000.0], index=idx)
    ts0, ts1 = datetime(2020, 1, 1), datetime(2020, 1, 2)
    trades = [
        # net (110-100)*10 - (1+1) = 98  -> win
        _trade(qty=10, entry=100, exit_=110, entry_ts=ts0, exit_ts=ts1,
               entry_costs=1.0, exit_costs=1.0),
        # net (90-100)*10 = -100 -> loss
        _trade(qty=10, entry=100, exit_=90, entry_ts=ts0, exit_ts=ts1),
        # net 0 -> NOT counted (strictly > 0)
        _trade(qty=5, entry=200, exit_=200, entry_ts=ts0, exit_ts=ts1),
        # net (210-200)*5 = 50 -> win
        _trade(qty=5, entry=200, exit_=210, entry_ts=ts0, exit_ts=ts1),
    ]
    m = compute_metrics(_result(eq, trades=trades))
    # 2 wins out of 4 trades
    assert m["hit_rate"] == pytest.approx(0.5)
    assert m["n_trades"] == 4.0


def test_turnover_exposure_holding_hand_computed() -> None:
    # Flat equity 1000 across Jan1..Jan5 so mean(equity) = 1000 exactly.
    idx = pd.date_range("2020-01-01", periods=5, freq="D")
    eq = pd.Series([1000.0] * 5, index=idx)
    # t1 open Jan1..Jan2 (entry Jan1, exit Jan3); notional 10*100 = 1000
    # t2 open Jan2..Jan3 (entry Jan2, exit Jan4); notional  5*200 = 1000
    t1 = _trade(qty=10, entry=100, exit_=100,
                entry_ts=datetime(2020, 1, 1), exit_ts=datetime(2020, 1, 3))
    t2 = _trade(qty=5, entry=200, exit_=200,
                entry_ts=datetime(2020, 1, 2), exit_ts=datetime(2020, 1, 4))
    m = compute_metrics(_result(eq, trades=[t1, t2]))

    # turnover = (Σentry + Σexit)/2 / mean_eq / years
    #          = (2000 + 2000)/2 / 1000 / (4/252) = 2 * 252/4 = 126.0
    assert m["turnover"] == pytest.approx(126.0)
    # exposure per bar (entry notional of open trades / equity):
    #   Jan1: t1 -> 1000/1000 = 1.0
    #   Jan2: t1+t2 -> 2000/1000 = 2.0
    #   Jan3: t2 -> 1000/1000 = 1.0
    #   Jan4, Jan5: none -> 0
    # mean([1,2,1,0,0]) = 0.8
    assert m["exposure"] == pytest.approx(0.8)
    # holding: both 2 days -> mean 2.0
    assert m["avg_holding_days"] == pytest.approx(2.0)


# --------------------------------------------------------------------------- #
# Benchmark regression                                                         #
# --------------------------------------------------------------------------- #
def test_alpha_zero_beta_one_when_benchmark_is_equity() -> None:
    idx = pd.date_range("2020-01-01", periods=6, freq="D")
    eq = pd.Series([100.0, 101.0, 99.0, 102.0, 105.0, 103.0], index=idx)
    m = compute_metrics(_result(eq), benchmark=eq.copy())
    # regressing a series on itself: beta == 1, alpha == 0 exactly
    assert m["beta"] == pytest.approx(1.0)
    assert m["alpha"] == pytest.approx(0.0, abs=1e-12)


def test_alpha_beta_nan_without_benchmark() -> None:
    idx = pd.date_range("2020-01-01", periods=6, freq="D")
    eq = pd.Series([100.0, 101.0, 99.0, 102.0, 105.0, 103.0], index=idx)
    m = compute_metrics(_result(eq), benchmark=None)
    assert math.isnan(m["alpha"]) and math.isnan(m["beta"])


def test_alpha_beta_nan_when_overlap_too_small() -> None:
    idx = pd.date_range("2020-01-01", periods=6, freq="D")
    eq = pd.Series([100.0, 101.0, 99.0, 102.0, 105.0, 103.0], index=idx)
    # benchmark overlaps on only 2 dates -> < 3 return observations -> NaN
    bench = pd.Series([50.0, 51.0], index=idx[:2])
    m = compute_metrics(_result(eq), benchmark=bench)
    assert math.isnan(m["alpha"]) and math.isnan(m["beta"])


def test_beta_greater_than_one_for_levered_equity() -> None:
    # equity moves exactly 2x the benchmark each day -> beta == 2
    idx = pd.date_range("2020-01-01", periods=6, freq="D")
    br = np.array([0.01, -0.02, 0.03, -0.01, 0.02])
    bench_levels = 100.0 * np.concatenate([[1.0], np.cumprod(1.0 + br)])
    eq_levels = 100.0 * np.concatenate([[1.0], np.cumprod(1.0 + 2.0 * br)])
    bench = pd.Series(bench_levels, index=idx)
    eq = pd.Series(eq_levels, index=idx)
    m = compute_metrics(_result(eq), benchmark=bench)
    assert m["beta"] == pytest.approx(2.0, rel=1e-6)


# --------------------------------------------------------------------------- #
# Table / series helpers                                                       #
# --------------------------------------------------------------------------- #
def test_monthly_and_yearly_returns_compound() -> None:
    # Jan: 100 -> 110 (+10%); Feb: 110 -> 99 -> 108.9
    # Feb return compounds -0.10 then +0.10 -> 0.9*1.1 - 1 = -0.01
    idx = pd.DatetimeIndex(["2020-01-15", "2020-01-31", "2020-02-14", "2020-02-28"])
    eq = pd.Series([100.0, 110.0, 99.0, 108.9], index=idx)
    mr = monthly_returns(eq)
    assert mr.loc[2020, "Jan"] == pytest.approx(0.10)
    assert mr.loc[2020, "Feb"] == pytest.approx(-0.01)
    # YTD = 1.10 * 0.99 - 1 = 0.089
    assert mr.loc[2020, "YTD"] == pytest.approx(0.089)
    # months with no data are NaN
    assert math.isnan(mr.loc[2020, "Jun"])

    yr = yearly_returns(eq)
    # full-year compound = 1.1 * 0.9 * 1.1 - 1 = 0.089
    assert yr.loc[2020] == pytest.approx(0.089)


def test_rolling_sharpe_window() -> None:
    idx = pd.date_range("2020-01-01", periods=4, freq="D")
    eq = pd.Series([100.0, 110.0, 99.0, 108.9], index=idx)
    rs = rolling_sharpe(eq, window=3)
    # first three positions lack a full 3-return window -> NaN
    assert rs.iloc[:3].isna().all()
    # last window = returns [0.10,-0.10,0.10] -> same as the full-sample sharpe
    r = np.array([0.10, -0.10, 0.10])
    assert rs.iloc[-1] == pytest.approx(r.mean() / r.std(ddof=1) * _SQRT252)


def test_rolling_sharpe_flat_window_is_nan_not_inf() -> None:
    idx = pd.date_range("2020-01-01", periods=5, freq="D")
    eq = pd.Series([100.0] * 5, index=idx)  # flat -> zero vol
    rs = rolling_sharpe(eq, window=3)
    assert not np.isinf(rs.to_numpy()).any()


# --------------------------------------------------------------------------- #
# Degenerate inputs & full-key invariants                                       #
# --------------------------------------------------------------------------- #
def test_degenerate_inputs_return_all_nan_dict() -> None:
    empty = pd.Series(dtype=float)
    m_empty = compute_metrics(_result_from_empty(empty))
    assert set(m_empty) == set(_METRIC_KEYS)
    assert all(math.isnan(v) for v in m_empty.values())

    one = pd.Series([100.0], index=pd.date_range("2020-01-01", periods=1))
    m_one = compute_metrics(_result_from_empty(one))
    assert set(m_one) == set(_METRIC_KEYS)
    assert all(math.isnan(v) for v in m_one.values())


def _result_from_empty(equity: pd.Series) -> BacktestResult:
    """BacktestResult wrapper that tolerates an empty/1-point equity index."""
    if len(equity):
        start = equity.index[0].date()
        end = equity.index[-1].date()
    else:
        start = end = date(2020, 1, 1)
    return BacktestResult(
        config=None,  # type: ignore[arg-type]
        engine=EngineMode.EVENT,
        start=start,
        end=end,
        capital=100_000.0,
        equity=equity,
        gross_equity=equity,
        trades=[],
        total_costs=0.0,
    )


def test_synthetic_equity_invariants() -> None:
    close = synthetic_daily(symbol="INV", start=date(2018, 1, 1), end=date(2020, 12, 31))[
        "close"
    ]
    m = compute_metrics(_result(close))
    # every key present, every value a float, none infinite
    assert set(m) == set(_METRIC_KEYS)
    assert all(isinstance(v, float) for v in m.values())
    assert not any(math.isinf(v) for v in m.values())
    # drawdown is a fraction in [-1, 0]; sharpe/vol finite
    assert -1.0 <= m["max_drawdown"] <= 0.0
    assert math.isfinite(m["sharpe"])
    assert math.isfinite(m["vol"]) and m["vol"] > 0.0
    assert math.isfinite(m["total_return"])
    # drawdown series bounded in [-1, 0] and full-length
    dd = drawdown_series(close)
    assert len(dd) == len(close)
    assert (dd <= 1e-12).all() and (dd >= -1.0 - 1e-9).all()

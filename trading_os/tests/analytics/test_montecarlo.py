"""Tests for analytics/montecarlo.py.

The centrepiece is a 3-trade case whose 6 permutations are enumerable by hand,
so the Monte Carlo percentile bands can be bounded against the exact drawdown
distribution. Also: determinism (same seed -> identical result), the
permutation-invariance of final equity under shuffle, and degenerate inputs.
"""

from __future__ import annotations

import math
from datetime import datetime

from tradingos.analytics.montecarlo import MonteCarloResult, drawdown_bands
from tradingos.core.models import Trade

_TS0 = datetime(2020, 1, 1)
_TS1 = datetime(2020, 1, 2)


def _trade(net_pnl: float, symbol: str = "X") -> Trade:
    """Trade whose net_pnl == ``net_pnl`` (entry 100, no costs)."""
    return Trade(
        symbol=symbol,
        qty=1,
        entry_ts=_TS0,
        exit_ts=_TS1,
        entry_price=100.0,
        exit_price=100.0 + net_pnl,
    )


def test_shuffle_bands_within_enumerated_drawdown_distribution() -> None:
    # PnLs [+100, -50, +30], capital 1000. All 6 orderings, drawdown vs peak:
    #   [-50,100,30] & [-50,30,100] -> -50/1000        = -0.050000  (deepest)
    #   [30,-50,100]                -> -50/1030        = -0.048544
    #   [100,-50,30]                -> -50/1100        = -0.045455
    #   [100,30,-50] & [30,100,-50] -> -50/1130        = -0.044248  (shallowest)
    # So every percentile must lie in [-50/1000, -50/1130].
    trades = [_trade(100), _trade(-50), _trade(30)]
    enum_min = -50 / 1000  # deepest
    enum_max = -50 / 1130  # shallowest
    mc = drawdown_bands(trades, capital=1000.0, n_paths=20_000, seed=42, method="shuffle")

    # float tolerance: percentile interpolation vs the literal bound may differ
    # by ~1 ULP because the path arithmetic rounds differently than -50/D.
    tol = 1e-9
    assert enum_min - tol <= mc.max_dd_p5
    assert mc.max_dd_p95 <= enum_max + tol
    assert mc.max_dd_p5 <= mc.max_dd_p50 <= mc.max_dd_p95
    # all drawdowns negative
    assert mc.max_dd_p50 < 0.0

    # Final equity is permutation-invariant under shuffle: capital + Σpnl = 1080.
    assert mc.final_equity_p5 == 1080.0
    assert mc.final_equity_p50 == 1080.0
    assert mc.final_equity_p95 == 1080.0

    assert mc.n_paths == 20_000
    assert mc.method == "shuffle"


def test_same_seed_is_deterministic() -> None:
    trades = [_trade(100), _trade(-50), _trade(30), _trade(-20), _trade(75)]
    a = drawdown_bands(trades, capital=1000.0, n_paths=5000, seed=7, method="shuffle")
    b = drawdown_bands(trades, capital=1000.0, n_paths=5000, seed=7, method="shuffle")
    assert a == b  # dataclass equality over every field


def test_skip_method_perturbs_final_equity() -> None:
    # 10 trades, skip_fraction 0.2 -> drop floor(2) = 2 trades per path, so the
    # surviving PnL sum (and hence final equity) varies across paths.
    trades = [_trade(v) for v in (100, -50, 30, -20, 75, -10, 40, -60, 90, -25)]
    mc = drawdown_bands(
        trades, capital=1000.0, n_paths=5000, skip_fraction=0.2, seed=3, method="skip"
    )
    assert mc.method == "skip"
    # dropping trades spreads the terminal wealth distribution
    assert mc.final_equity_p5 < mc.final_equity_p95
    assert mc.max_dd_p5 <= mc.max_dd_p50 <= mc.max_dd_p95
    assert mc.max_dd_p50 < 0.0
    # drawdowns are fractional, never below -100%
    assert mc.max_dd_p5 >= -1.0


def test_skip_determinism() -> None:
    trades = [_trade(v) for v in (100, -50, 30, -20, 75, -10, 40, -60, 90, -25)]
    a = drawdown_bands(trades, capital=1000.0, n_paths=3000, seed=9, method="skip")
    b = drawdown_bands(trades, capital=1000.0, n_paths=3000, seed=9, method="skip")
    assert a == b


def test_empty_and_single_trade_return_nan_result() -> None:
    empty = drawdown_bands([], capital=1000.0, n_paths=500, method="shuffle")
    assert isinstance(empty, MonteCarloResult)
    assert math.isnan(empty.max_dd_p5)
    assert math.isnan(empty.max_dd_p50)
    assert math.isnan(empty.final_equity_p50)
    # metadata still echoes the request
    assert empty.n_paths == 500
    assert empty.method == "shuffle"

    one = drawdown_bands([_trade(10)], capital=1000.0, n_paths=500, method="skip")
    assert math.isnan(one.max_dd_p50)
    assert one.method == "skip"


def test_drawdown_p5_is_the_worse_tail() -> None:
    # By convention p5 <= p95 (p5 is deeper/worse). Confirm on a wide sample.
    trades = [_trade(v) for v in (200, -150, 80, -90, 120, -60)]
    mc = drawdown_bands(trades, capital=1000.0, n_paths=8000, seed=11, method="shuffle")
    assert mc.max_dd_p5 <= mc.max_dd_p95  # p5 deeper (more negative)

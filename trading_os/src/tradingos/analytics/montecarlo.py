"""Monte Carlo drawdown / terminal-wealth bands from a trade sequence.

Given the realized per-trade NET PnLs, resample the trade order (or drop a
random subset of trades) many times to build a distribution of equity paths,
then report percentile bands for max drawdown and final equity. This answers
"how much of my backtest's smoothness was luck of ordering?" — a strategy whose
5th-percentile drawdown is far deeper than the single realized path is fragile.

Two resampling methods:

* ``"shuffle"`` — permute the sequence of per-trade PnLs (order is luck; the SET
  of trades is held fixed). Final equity is therefore identical across every
  path (sum is order-invariant); only the drawdown path differs.
* ``"skip"`` — randomly drop ``floor(skip_fraction * n)`` trades WITHOUT
  replacement, keeping the surviving trades in their original order. This
  perturbs both the drawdown and the final equity.

Determinism: a fresh ``numpy.random.Generator`` is seeded per call from ``seed``;
the global RNG is NEVER touched. Same ``seed`` + args -> identical result.

Percentile convention: ``p5`` is the WORSE tail. ``max_dd_p5`` means "5% of
simulated paths had a drawdown deeper (more negative) than this"; ``max_dd_p95``
is the shallow/optimistic tail. For final equity, ``p5`` is the low/pessimistic
tail. Drawdowns are negative fractions vs the running peak.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np

from tradingos.core.models import Trade

Method = Literal["shuffle", "skip"]


@dataclass
class MonteCarloResult:
    """Percentile bands from a Monte Carlo resampling of the trade sequence.

    Drawdowns are negative fractions; ``p5`` is the worse/deeper tail (5% of
    paths were worse than this), ``p95`` the shallower/optimistic tail. Final
    equity ``p5`` is the low tail. ``n_paths`` and ``method`` echo the run
    configuration. Degenerate inputs (fewer than 2 trades) yield NaN stats.
    """

    max_dd_p5: float
    max_dd_p50: float
    max_dd_p95: float
    final_equity_p5: float
    final_equity_p50: float
    final_equity_p95: float
    n_paths: int
    method: str


def _nan_result(n_paths: int, method: str) -> MonteCarloResult:
    """A MonteCarloResult with NaN stats (too few trades to resample)."""
    return MonteCarloResult(
        max_dd_p5=math.nan,
        max_dd_p50=math.nan,
        max_dd_p95=math.nan,
        final_equity_p5=math.nan,
        final_equity_p50=math.nan,
        final_equity_p95=math.nan,
        n_paths=n_paths,
        method=method,
    )


def _path_max_drawdown(pnls: np.ndarray, capital: float) -> float:
    """Max drawdown (negative fraction vs running peak) of one PnL sequence.

    The path starts at ``capital`` and accrues ``cumsum(pnls)``; the leading
    ``capital`` point seeds the running peak so a first-trade loss is measured
    against starting capital.
    """
    path = np.empty(pnls.size + 1, dtype=float)
    path[0] = capital
    path[1:] = capital + np.cumsum(pnls)
    peak = np.maximum.accumulate(path)
    dd = path / peak - 1.0
    return float(dd.min())


def drawdown_bands(
    trades: list[Trade],
    capital: float,
    n_paths: int = 1000,
    skip_fraction: float = 0.1,
    seed: int = 42,
    method: Method = "shuffle",
) -> MonteCarloResult:
    """Monte Carlo max-drawdown and final-equity percentile bands.

    Parameters
    ----------
    trades
        Closed round-trip trades; only ``net_pnl`` is used.
    capital
        Starting capital seeding each path.
    n_paths
        Number of resampled paths.
    skip_fraction
        For ``method="skip"``, the fraction of trades dropped per path
        (``floor(skip_fraction * n)`` trades, without replacement).
    seed
        Seeds a per-call ``numpy.random.Generator`` (global RNG untouched).
    method
        ``"shuffle"`` (permute order) or ``"skip"`` (drop a random subset).

    Returns
    -------
    MonteCarloResult
        NaN-filled when there are fewer than 2 trades.
    """
    pnls = np.array([t.net_pnl for t in trades], dtype=float)
    n = pnls.size
    if n < 2:
        return _nan_result(n_paths, method)

    rng = np.random.default_rng(seed)
    max_dds = np.empty(n_paths, dtype=float)
    finals = np.empty(n_paths, dtype=float)

    if method == "skip":
        k = math.floor(skip_fraction * n)  # trades dropped per path

    for i in range(n_paths):
        if method == "shuffle":
            # Order is luck; the set of PnLs (and thus final equity) is fixed.
            sample = rng.permutation(pnls)
        elif method == "skip":
            # Drop k trades without replacement; survivors keep original order.
            if k > 0:
                drop = rng.choice(n, size=k, replace=False)
                keep = np.ones(n, dtype=bool)
                keep[drop] = False
                sample = pnls[keep]
            else:
                sample = pnls
        else:  # pragma: no cover - guarded by the Literal type
            raise ValueError(f"unknown method {method!r}")

        max_dds[i] = _path_max_drawdown(sample, capital)
        finals[i] = capital + float(sample.sum())

    # p5 = worse/deeper drawdown tail; p5 = lower final-equity tail.
    dd_p5, dd_p50, dd_p95 = np.percentile(max_dds, [5, 50, 95])
    fe_p5, fe_p50, fe_p95 = np.percentile(finals, [5, 50, 95])

    return MonteCarloResult(
        max_dd_p5=float(dd_p5),
        max_dd_p50=float(dd_p50),
        max_dd_p95=float(dd_p95),
        final_equity_p5=float(fe_p5),
        final_equity_p50=float(fe_p50),
        final_equity_p95=float(fe_p95),
        n_paths=n_paths,
        method=method,
    )

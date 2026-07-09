"""Analytics: performance metrics, robustness and significance statistics.

Public entry points re-exported here for convenience; the canonical definitions
live in the submodules (metrics/dsr/montecarlo). Financial math lives ONLY in
this package (CLAUDE.md rule 5).
"""

from __future__ import annotations

from tradingos.analytics.dsr import (
    deflated_sharpe_ratio,
    probabilistic_sharpe_ratio,
)
from tradingos.analytics.metrics import (
    compute_metrics,
    drawdown_series,
    monthly_returns,
    rolling_sharpe,
    top_drawdowns,
    yearly_returns,
)
from tradingos.analytics.montecarlo import (
    MonteCarloResult,
    drawdown_bands,
)
from tradingos.analytics.robustness import (
    PerturbationRow,
    RobustnessResult,
    perturbation_grid,
)
from tradingos.analytics.tearsheet import (
    plotly_report,
    quantstats_tearsheet,
)
from tradingos.analytics.walkforward import (
    WalkForwardResult,
    WalkForwardWindow,
    walk_forward,
)

__all__ = [
    # metrics
    "compute_metrics",
    "monthly_returns",
    "yearly_returns",
    "rolling_sharpe",
    "drawdown_series",
    "top_drawdowns",
    # significance
    "deflated_sharpe_ratio",
    "probabilistic_sharpe_ratio",
    # robustness
    "drawdown_bands",
    "MonteCarloResult",
    "perturbation_grid",
    "PerturbationRow",
    "RobustnessResult",
    # walk-forward
    "walk_forward",
    "WalkForwardResult",
    "WalkForwardWindow",
    # reports
    "plotly_report",
    "quantstats_tearsheet",
]

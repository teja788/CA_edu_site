"""SQLModel tables for the experiments run registry.

Two tables live in ``settings.experiments_db_path``:

* :class:`ExperimentRun` — one row per executed grid variant (train run or
  holdout run). It stores the FULL UNCLAMPED variant config plus the clamp that
  was actually applied (``train_end``), the recorded engine, provenance
  (git hash + data snapshot id), and the scalar metrics needed to sort a
  leaderboard without re-reading artifacts. The full ``compute_metrics`` dict is
  kept in ``metrics_json`` for the comparison report.
* :class:`HoldoutAccess` — the append-only audit log the bias-defense spec
  demands: one row every time a holdout run is scored, so the number of times
  the out-of-sample set has been touched is always auditable.

Reproducibility contract: ``config_json`` is the UNCLAMPED variant config
(``model_dump(mode="json")``); ``train_end`` records the clamp that produced
this particular run. Together they let :func:`experiments.leaderboard.reproduce`
rebuild and re-run any row bit-for-bit.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlmodel import Field, SQLModel


class ExperimentRun(SQLModel, table=True):
    """One executed grid variant — a train run (``is_holdout=False``) or a
    holdout run (``is_holdout=True``)."""

    id: int | None = Field(default=None, primary_key=True)

    # -- identity / provenance -------------------------------------------
    family: str = Field(index=True)  # the grid name
    variant_name: str
    config_hash: str
    config_json: str  # FULL UNCLAMPED variant config (model_dump(mode="json"))
    overrides_json: str  # the sweep overrides that produced this variant
    code_git_hash: str
    snapshot_id: str  # BarStore data fingerprint
    engine: str  # EngineMode value ("event" / "vectorized")

    # -- execution status ------------------------------------------------
    status: str  # "done" | "error"
    error: str | None = None
    started_at: datetime
    finished_at: datetime
    artifacts_path: str

    # -- holdout / clamp -------------------------------------------------
    is_holdout: bool = Field(default=False, index=True)
    train_end: date | None = None  # the clamp actually applied to this run

    # -- scalar metrics (for sorting; full dict in metrics_json) ---------
    sharpe: float | None = None
    cagr: float | None = None
    max_drawdown: float | None = None
    calmar: float | None = None
    vol: float | None = None
    total_costs_pct: float | None = None
    final_equity: float | None = None
    n_trades: float | None = None

    # -- DSR inputs computed at run time ---------------------------------
    n_bars: int | None = None
    ret_skew: float | None = None
    ret_kurt: float | None = None  # NON-EXCESS kurtosis (normal == 3)

    metrics_json: str  # full compute_metrics dict as JSON


class HoldoutAccess(SQLModel, table=True):
    """Audit log: one row per holdout run scored. This is the record the
    lockout consults ("logs every access") — never deleted or updated."""

    id: int | None = Field(default=None, primary_key=True)
    family: str = Field(index=True)
    run_id: int | None = None  # the ExperimentRun (holdout) id, once inserted
    accessed_at: datetime
    note: str


__all__ = ["ExperimentRun", "HoldoutAccess"]

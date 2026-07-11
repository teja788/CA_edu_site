"""Holdout scoring under a hard evaluation lockout — the platform's defense
against data-mining a false positive out of the out-of-sample set.

``score_holdout`` is the ONLY door to the withheld ``holdout_years`` window. It
checks the quota BEFORE touching any data (no partial scoring past the limit),
logs every access to :class:`HoldoutAccess`, and shouts a WARNING per access.
Holdout runs are stored with ``is_holdout=True`` so they never count toward the
DSR trial count and never appear in the default leaderboard.
"""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from sqlmodel import select

from tradingos.config.schemas import EngineMode, StrategyConfig
from tradingos.config.settings import Settings
from tradingos.core.errors import HoldoutLockedError
from tradingos.core.logging import get_logger
from tradingos.core.models import Timeframe
from tradingos.core.timeutils import now_ist
from tradingos.experiments.db import session_scope
from tradingos.experiments.models import ExperimentRun, HoldoutAccess
from tradingos.experiments.runner import (
    _artifacts_path,
    _opt,
    _skew_kurt,
    code_git_hash,
    make_engine,
    make_universe_resolver,
    resolve_symbols,
)

logger = get_logger(__name__)

# Metric columns a caller may sort candidate train runs by (dsr is NOT stored).
_SORTABLE = {
    "sharpe": ExperimentRun.sharpe,
    "cagr": ExperimentRun.cagr,
    "calmar": ExperimentRun.calmar,
    "max_drawdown": ExperimentRun.max_drawdown,
    "vol": ExperimentRun.vol,
    "final_equity": ExperimentRun.final_equity,
    "total_costs_pct": ExperimentRun.total_costs_pct,
}


def _sort_column(sort: str) -> Any:
    col = _SORTABLE.get(sort)
    if col is None:
        raise ValueError(
            f"cannot sort holdout candidates by {sort!r}; choose one of {sorted(_SORTABLE)}"
        )
    return col


def score_holdout(
    family: str,
    settings: Settings,
    *,
    top: int = 1,
    max_evals: int = 3,
    sort: str = "sharpe",
    timeframe: Timeframe = Timeframe.DAY,
    adjusted: bool = True,
) -> list[int]:
    """Score the top-``top`` train runs of ``family`` on the withheld holdout
    window, subject to a lockout of ``max_evals`` total accesses.

    Raises :class:`HoldoutLockedError` (before any scoring) if granting ``top``
    more accesses would exceed ``max_evals``. Returns the ids of the inserted
    holdout ExperimentRun rows.
    """
    sort_col = _sort_column(sort)

    # -- LOCKOUT CHECK FIRST — no data is touched until the quota clears ---
    with session_scope(settings) as session:
        used = len(
            session.exec(select(HoldoutAccess).where(HoldoutAccess.family == family)).all()
        )
    if used + top > max_evals:
        raise HoldoutLockedError(
            f"holdout for family {family!r} is LOCKED: quota={max_evals}, "
            f"already used={used}, requested={top} more -> would be {used + top}. "
            "This guard exists to prevent data-mining the out-of-sample holdout; "
            "every additional evaluation inflates selection bias. Refusing without "
            "partial scoring."
        )

    # -- select the top-N eligible train runs -----------------------------
    with session_scope(settings) as session:
        candidates = session.exec(
            select(ExperimentRun)
            .where(ExperimentRun.family == family)
            .where(ExperimentRun.is_holdout == False)  # noqa: E712 — SQL identity, not `is`
            .where(ExperimentRun.status == "done")
            .where(ExperimentRun.sharpe.is_not(None))  # type: ignore[union-attr]
            .order_by(sort_col.desc())
            .limit(top)
        ).all()
        # Detach plain snapshots so we can use them after the session closes.
        selected = [_snapshot(r) for r in candidates]

    if not selected:
        logger.warning("score_holdout %r: no eligible train runs to score", family)
        return []

    # -- load market data once (union across the selected configs) --------
    from tradingos.data.store import BarStore

    store = BarStore(settings)
    configs = {s["id"]: StrategyConfig.model_validate(json.loads(s["config_json"])) for s in selected}
    symbols: set[str] = set()
    for cfg in configs.values():
        symbols.update(resolve_symbols(cfg, store, timeframe))
    data = store.load_market_data(sorted(symbols), timeframe, adjusted=adjusted)
    snapshot_id = data.snapshot_id
    git_hash = code_git_hash()

    inserted: list[int] = []
    for src in selected:
        run_id = _score_one(
            src,
            config=configs[src["id"]],
            data=data,
            settings=settings,
            family=family,
            sort=sort,
            snapshot_id=snapshot_id,
            git_hash=git_hash,
        )
        inserted.append(run_id)
    return inserted


def _score_one(
    src: dict[str, Any],
    *,
    config: StrategyConfig,
    data: Any,
    settings: Settings,
    family: str,
    sort: str,
    snapshot_id: str,
    git_hash: str,
) -> int:
    """Run one source run on its holdout window, persist the run + audit row."""
    from tradingos.analytics.metrics import compute_metrics

    train_end = src["train_end"]
    holdout_start = train_end + timedelta(days=1)
    holdout_cfg = config.model_copy(update={"start": holdout_start, "end": config.end})

    variant_name = f"{src['variant_name']}__holdout"
    artifacts_path = _artifacts_path(settings, family, variant_name)
    started_at = now_ist()

    logger.warning(
        "HOLDOUT ACCESS: family=%r scoring source run %s (%s) on out-of-sample "
        "window starting %s [sort=%s]",
        family,
        src["id"],
        src["variant_name"],
        holdout_start,
        sort,
    )

    status = "done"
    error: str | None = None
    metrics: dict[str, float] = {}
    n_bars = 0
    ret_skew = ret_kurt = None
    run_warnings: list[str] = []
    try:
        engine = make_engine(EngineMode(src["engine"]))
        result = engine.run(holdout_cfg, data, make_universe_resolver(settings))
        run_warnings = list(result.warnings)
        metrics = compute_metrics(result)
        returns = result.equity.pct_change().dropna()
        n_bars = int(len(returns))
        ret_skew, ret_kurt = _skew_kurt(returns)
        result.save(artifacts_path)
    except Exception as exc:  # noqa: BLE001 — record failure, keep the audit honest
        logger.warning("holdout scoring of run %s failed: %s", src["id"], exc)
        status = "error"
        error = str(exc) or exc.__class__.__name__

    finished_at = now_ist()

    with session_scope(settings) as session:
        run = ExperimentRun(
            family=family,
            variant_name=variant_name,
            config_hash=src["config_hash"],
            config_json=src["config_json"],  # UNCLAMPED, same as the source
            overrides_json=src["overrides_json"],
            code_git_hash=git_hash,
            snapshot_id=snapshot_id,
            engine=src["engine"],
            status=status,
            error=error,
            started_at=started_at,
            finished_at=finished_at,
            artifacts_path=str(artifacts_path),
            is_holdout=True,
            train_end=train_end,  # kept so reproduce() can rebuild start=train_end+1
            sharpe=_opt(metrics.get("sharpe")),
            cagr=_opt(metrics.get("cagr")),
            max_drawdown=_opt(metrics.get("max_drawdown")),
            calmar=_opt(metrics.get("calmar")),
            vol=_opt(metrics.get("vol")),
            total_costs_pct=_opt(metrics.get("total_costs_pct")),
            final_equity=_opt(metrics.get("final_equity")),
            n_trades=_opt(metrics.get("n_trades")),
            n_bars=n_bars,
            ret_skew=_opt(ret_skew),
            ret_kurt=_opt(ret_kurt),
            metrics_json=json.dumps(metrics),
            warnings_json=json.dumps(run_warnings),
        )
        session.add(run)
        session.flush()
        run_id = int(run.id)  # type: ignore[arg-type]
        session.add(
            HoldoutAccess(
                family=family,
                run_id=run_id,
                accessed_at=finished_at,
                note=(
                    f"holdout score of run {src['id']} ({src['variant_name']}) "
                    f"sorted by {sort}"
                ),
            )
        )
    return run_id


def _snapshot(run: ExperimentRun) -> dict[str, Any]:
    """A plain-dict copy of the fields we need after the session closes."""
    return {
        "id": run.id,
        "variant_name": run.variant_name,
        "config_hash": run.config_hash,
        "config_json": run.config_json,
        "overrides_json": run.overrides_json,
        "engine": run.engine,
        "train_end": run.train_end,
        "sharpe": run.sharpe,
    }


__all__ = ["score_holdout"]

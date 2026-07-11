"""Parallel grid runner: expand a GridSpec, run every variant, register results.

Bias-critical design (the TRAIN/HOLDOUT LOCKOUT lives here):

* A single ``data_end`` is established in the PARENT (max bar ts across the
  loaded symbols). ``train_end = (data_end - holdout_years * 365.25 days).date()``
  and, if a variant's own ``config.end`` is earlier, the tighter of the two is
  used. Every TRAIN run is executed on a config CLAMPED to ``end=train_end`` so
  the last ``holdout_years`` of data are never seen during selection. The
  UNCLAMPED config is what gets stored (``config_json``); the ``train_end``
  column records the clamp actually applied.

* Each variant runs in a spawned worker (``_run_variant``, module-level for
  picklability) that receives only PRIMITIVES — a config dump dict, symbol list,
  path strings — and reloads its own ``BarStore``. No pandas frame is ever
  pickled across the process boundary. A failing variant returns a row with
  ``status="error"`` and never kills the grid.

* ALL database writes happen in the parent; workers return plain row dicts.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
from datetime import date, timedelta
from multiprocessing import get_context
from pathlib import Path
from typing import Any

from tradingos.config.gridexpand import GridVariant, expand_gridspec
from tradingos.config.schemas import EngineMode, GridSpec, StrategyConfig
from tradingos.config.settings import Settings
from tradingos.core.errors import DataError
from tradingos.core.logging import get_logger
from tradingos.core.models import Timeframe
from tradingos.core.timeutils import now_ist

logger = get_logger(__name__)

_DAYS_PER_YEAR = 365.25


# --------------------------------------------------------------------------- #
# Shared helpers (used by runner, holdout and reproduce)                       #
# --------------------------------------------------------------------------- #
def project_root() -> Path:
    """Repo root (…/trading_os), used as the cwd for ``git rev-parse``."""
    return Path(__file__).resolve().parents[3]


def code_git_hash() -> str:
    """Current ``git rev-parse HEAD`` (short-circuits to ``"unknown"``)."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root(),
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        return out.stdout.strip() or "unknown"
    except Exception:  # noqa: BLE001 — provenance is best-effort, never fatal
        return "unknown"


def make_engine(mode: EngineMode) -> Any:
    """Instantiate the engine for ``mode``. Heavy imports (vectorbt) stay lazy."""
    if mode == EngineMode.VECTORIZED:
        from tradingos.engine.vectorized.engine import VectorizedEngine

        return VectorizedEngine()
    from tradingos.engine.event.engine import EventEngine

    return EventEngine()


def make_universe_resolver(settings: Settings) -> Any:
    """Universe resolver for EVERY experiments run path (train, holdout,
    reproduce): the point-in-time resolver backed by the membership table
    (hard rule 4 — survivorship bias defense).

    Gating happens inside the resolver on the existing config shape and on
    data availability, so no schema change is needed:

    * ``universe.symbols`` set -> the explicit list is used as-is (tests /
      small runs; no membership lookup, no warning).
    * ``universe.point_in_time`` and no explicit symbols -> membership is
      resolved AS OF each rebalance date. If the membership table has no data
      for the index (or the date is outside coverage) the resolver falls back
      to all available symbols and LOUDLY warns — the warning is persisted on
      the run row and flags it as tainted on the leaderboard.
    * delisted/suspended symbols are dropped from candidacy as of their
      corporate-action date, and the liquidity filter only ever sees bars
      dated on/before the rebalance date.
    """
    from tradingos.data.universe import PITUniverseResolver

    return PITUniverseResolver(settings)


def resolve_symbols(config: StrategyConfig, store: Any, timeframe: Timeframe) -> list[str]:
    """Symbols to load for ``config``: its explicit universe (else every symbol
    in the store for the timeframe) plus any symbol-routed regime-filter targets
    — the same convention as ``cli/backtest_cmds.py``."""
    load: set[str] = set(config.universe.symbols or [])
    if not load:
        load = set(store.symbols(timeframe))
    for fspec in config.filters:
        routed = fspec.params.get("symbol")
        if routed:
            load.add(str(routed))
    return sorted(load)


def _artifacts_path(settings: Settings, family: str, variant_name: str) -> Path:
    return Path(settings.artifacts_dir) / "experiments" / family / variant_name


def _skew_kurt(returns: Any) -> tuple[float, float]:
    """(skew, NON-EXCESS kurtosis) of a returns series; NaN if < 2 observations."""
    if returns is None or len(returns) < 2:
        return math.nan, math.nan
    from scipy.stats import kurtosis, skew

    return float(skew(returns)), float(kurtosis(returns, fisher=False))


# --------------------------------------------------------------------------- #
# Worker (module-level for spawn picklability)                                 #
# --------------------------------------------------------------------------- #
def _run_variant(payload: dict[str, Any]) -> dict[str, Any]:
    """Execute one variant in a worker process and return a row dict.

    Receives PRIMITIVES only. Rebuilds Settings, reloads market data, runs the
    recorded engine on the CLAMPED config, computes metrics + higher moments,
    saves the artifacts bundle, and returns the row the parent will insert. A
    failure is captured as ``status="error"`` so the grid survives.
    """
    started_at = now_ist()

    # Deterministic fields the parent already computed travel through unchanged.
    row: dict[str, Any] = {
        "family": payload["family"],
        "variant_name": payload["variant_name"],
        "config_hash": payload["config_hash"],
        "config_json": payload["config_json"],  # UNCLAMPED, JSON string
        "overrides_json": payload["overrides_json"],
        "code_git_hash": payload["code_git_hash"],
        "snapshot_id": payload["snapshot_id"],
        "engine": payload["engine"],
        "is_holdout": payload["is_holdout"],
        "train_end": date.fromisoformat(payload["train_end"]) if payload["train_end"] else None,
        "artifacts_path": payload["artifacts_path"],
        "warnings_json": "[]",  # overwritten with the engine's warnings on success
    }

    try:
        from tradingos.analytics.metrics import compute_metrics
        from tradingos.data.store import BarStore

        settings = Settings(
            data_dir=Path(payload["data_dir"]),
            artifacts_dir=Path(payload["artifacts_dir"]),
            _env_file=None,
        )
        store = BarStore(settings)
        timeframe = Timeframe(payload["timeframe"])
        config = StrategyConfig.model_validate(payload["config_run"])  # CLAMPED

        data = store.load_market_data(
            payload["symbols"], timeframe, adjusted=payload["adjusted"]
        )
        if not data.symbols:
            raise DataError(
                f"no {timeframe.value} data for symbols {payload['symbols']} "
                f"(adjusted={payload['adjusted']})"
            )

        engine = make_engine(EngineMode(payload["engine"]))
        result = engine.run(config, data, make_universe_resolver(settings))

        metrics = compute_metrics(result)
        returns = result.equity.pct_change().dropna()
        n_bars = int(len(returns))
        ret_skew, ret_kurt = _skew_kurt(returns)

        result.save(Path(payload["artifacts_path"]))

        row.update(
            {
                "status": "done",
                "error": None,
                "sharpe": _opt(metrics.get("sharpe")),
                "cagr": _opt(metrics.get("cagr")),
                "max_drawdown": _opt(metrics.get("max_drawdown")),
                "calmar": _opt(metrics.get("calmar")),
                "vol": _opt(metrics.get("vol")),
                "total_costs_pct": _opt(metrics.get("total_costs_pct")),
                "final_equity": _opt(metrics.get("final_equity")),
                "n_trades": _opt(metrics.get("n_trades")),
                "n_bars": n_bars,
                "ret_skew": _opt(ret_skew),
                "ret_kurt": _opt(ret_kurt),
                "metrics_json": json.dumps(metrics),
                # Bias audit trail: survivorship/coverage/look-ahead warnings
                # must reach the DB, not just the console (leaderboard flags
                # tainted runs from this field).
                "warnings_json": json.dumps(result.warnings),
            }
        )
    except Exception as exc:  # noqa: BLE001 — a failing combo must not kill the grid
        logger.warning("variant %s failed: %s", payload["variant_name"], exc)
        row.update(
            {
                "status": "error",
                "error": str(exc) or exc.__class__.__name__,
                "sharpe": None,
                "cagr": None,
                "max_drawdown": None,
                "calmar": None,
                "vol": None,
                "total_costs_pct": None,
                "final_equity": None,
                "n_trades": None,
                "n_bars": None,
                "ret_skew": None,
                "ret_kurt": None,
                "metrics_json": "{}",
            }
        )

    row["started_at"] = started_at
    row["finished_at"] = now_ist()
    return row


def _opt(value: Any) -> float | None:
    """NaN/inf/None -> None (a clean SQL NULL); otherwise a float."""
    if value is None:
        return None
    f = float(value)
    return f if math.isfinite(f) else None


# --------------------------------------------------------------------------- #
# Parent orchestration                                                         #
# --------------------------------------------------------------------------- #
def _build_payload(
    variant: GridVariant,
    *,
    family: str,
    settings: Settings,
    timeframe: Timeframe,
    adjusted: bool,
    train_end: date,
    git_hash: str,
    snapshot_id: str,
    symbols: list[str],
) -> dict[str, Any]:
    """Assemble the primitives-only payload for one train variant."""
    config = variant.config
    variant_name = config.name
    unclamped_dump = config.model_dump(mode="json")

    # Per-variant clamp: tighter of the family train_end and the variant's own end.
    variant_train_end = train_end
    if config.end is not None and config.end < variant_train_end:
        variant_train_end = config.end
    clamped = config.model_copy(update={"end": variant_train_end})

    return {
        "family": family,
        "variant_name": variant_name,
        "config_hash": config.config_hash(),  # hash of the UNCLAMPED variant config
        "config_json": json.dumps(unclamped_dump),
        "config_run": clamped.model_dump(mode="json"),
        "overrides_json": json.dumps(variant.overrides, default=str),
        "code_git_hash": git_hash,
        "snapshot_id": snapshot_id,
        "engine": config.engine.value,
        "is_holdout": False,
        "train_end": variant_train_end.isoformat(),
        "artifacts_path": str(_artifacts_path(settings, family, variant_name)),
        "data_dir": str(Path(settings.data_dir).resolve()),
        "artifacts_dir": str(Path(settings.artifacts_dir).resolve()),
        "symbols": symbols,
        "timeframe": timeframe.value,
        "adjusted": adjusted,
    }


def run_grid(
    grid: GridSpec,
    settings: Settings,
    *,
    holdout_years: float = 2.0,
    parallel: int | None = None,
    timeframe: Timeframe = Timeframe.DAY,
    adjusted: bool = True,
) -> list[int]:
    """Expand ``grid``, run every variant clamped to a train window, and register
    each result in the experiments DB. Returns the inserted run ids in order.

    The last ``holdout_years`` of data are withheld from every train run (the
    lockout's train side); :func:`experiments.holdout.score_holdout` is the only
    door to that out-of-sample window.

    MULTIPLE-TESTING BOUNDARY — ``family = grid.name`` is defined HERE, and it
    is the unit the Deflated Sharpe Ratio deflates over: every non-holdout
    variant ever registered under the same family name counts toward the
    family's ``n_trials``, INCLUDING errored variants (an attempt that crashed
    was still a draw from the search process). Re-running or extending a grid
    under the same name therefore correctly accumulates the burden; registering
    related sweeps under a NEW name resets the deflation, so never rename a
    family to make its DSR look better — group every variant of one research
    question under one family name.
    """
    variants = expand_gridspec(grid)
    family = grid.name
    logger.info("run_grid %r: %d variant(s)", family, len(variants))

    # -- resolve symbols (union across variants) --------------------------
    from tradingos.data.store import BarStore

    store = BarStore(settings)
    symbols: set[str] = set()
    for v in variants:
        symbols.update(resolve_symbols(v.config, store, timeframe))
    load_symbols = sorted(symbols)
    if not load_symbols:
        raise DataError(
            "run_grid: no symbols to load — give an explicit universe or sync data first"
        )

    # -- establish data_end once in the parent ----------------------------
    data = store.load_market_data(load_symbols, timeframe, adjusted=adjusted)
    if not data.symbols:
        raise DataError(
            f"run_grid: no {timeframe.value} data for {load_symbols} (adjusted={adjusted})"
        )
    data_end = max(df.index.max() for df in (data.full_frame(s) for s in data.symbols))
    train_end = (data_end - timedelta(days=holdout_years * _DAYS_PER_YEAR)).date()
    snapshot_id = data.snapshot_id
    git_hash = code_git_hash()
    logger.info(
        "run_grid %r: data_end=%s holdout_years=%.3f -> train_end=%s",
        family,
        data_end.date(),
        holdout_years,
        train_end,
    )

    payloads = [
        _build_payload(
            v,
            family=family,
            settings=settings,
            timeframe=timeframe,
            adjusted=adjusted,
            train_end=train_end,
            git_hash=git_hash,
            snapshot_id=snapshot_id,
            symbols=load_symbols,
        )
        for v in variants
    ]

    # -- execute ----------------------------------------------------------
    if parallel is None:
        parallel = grid.max_parallel or os.cpu_count() or 1
    if parallel <= 1:
        logger.info("run_grid %r: sequential (in-process)", family)
        rows = [_run_variant(p) for p in payloads]
    else:
        n_proc = min(parallel, len(payloads)) or 1
        logger.info("run_grid %r: spawn pool with %d worker(s)", family, n_proc)
        ctx = get_context("spawn")
        with ctx.Pool(processes=n_proc) as pool:
            rows = pool.map(_run_variant, payloads)

    return _write_rows(rows, settings)


def _write_rows(rows: list[dict[str, Any]], settings: Settings) -> list[int]:
    """Persist worker row dicts as ExperimentRun records (parent only)."""
    from tradingos.experiments.db import session_scope
    from tradingos.experiments.models import ExperimentRun

    ids: list[int] = []
    with session_scope(settings) as session:
        run_rows = [ExperimentRun(**row) for row in rows]
        for r in run_rows:
            session.add(r)
        session.flush()  # assign primary keys before the context commits
        ids = [int(r.id) for r in run_rows]  # type: ignore[arg-type]

    n_done = sum(1 for r in rows if r["status"] == "done")
    n_err = len(rows) - n_done
    logger.info("run_grid: registered %d run(s) — %d done, %d error", len(ids), n_done, n_err)
    return ids


__all__ = [
    "run_grid",
    "resolve_symbols",
    "make_engine",
    "make_universe_resolver",
    "code_git_hash",
    "project_root",
]

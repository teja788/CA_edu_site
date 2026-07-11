"""Leaderboard, pairwise comparison, and exact-reproduction checks.

The Deflated Sharpe Ratio is computed AT QUERY TIME per family (never stored):
its value depends on ``N`` — the number of trials in the family — which grows as
more variants are registered, so a stored column would go stale. See
:func:`_family_dsr` for exactly how the DSR inputs are assembled.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import func
from sqlmodel import Session, select

from tradingos.config.schemas import EngineMode, StrategyConfig
from tradingos.config.settings import Settings
from tradingos.core.errors import DataError
from tradingos.core.logging import get_logger
from tradingos.core.models import Timeframe
from tradingos.experiments.db import get_engine
from tradingos.experiments.models import ExperimentRun, is_bias_tainted, parse_warnings

logger = get_logger(__name__)

# Per-period conversion: annualized Sharpe / sqrt(252) (platform annualization).
_SQRT_TRADING_DAYS = math.sqrt(252)

_LEADERBOARD_COLUMNS = [
    "id",
    "family",
    "variant_name",
    "engine",
    "sharpe",
    "dsr",
    "cagr",
    "max_drawdown",
    "calmar",
    "total_costs_pct",
    "n_trades",
    "tainted",
    "n_warnings",
    "overrides",
]


# --------------------------------------------------------------------------- #
# DSR assembly (per family, at query time)                                     #
# --------------------------------------------------------------------------- #
def _family_dsr(rows: list[ExperimentRun], n_trials: int | None = None) -> dict[int, float]:
    """Map each row id -> its Deflated Sharpe Ratio within this family.

    MULTIPLE-TESTING BOUNDARY: the FAMILY NAME (``grid.name``, assigned in
    :func:`experiments.runner.run_grid`) is the unit the DSR deflates over.
    ``n_trials`` must therefore count EVERY non-holdout variant ever registered
    under the family — including ``status="error"`` rows: an errored variant was
    still a trial of the search process, and dropping it would understate the
    selection burden. Callers pass that full count via ``n_trials``; when it is
    omitted (or smaller than the rows provided) the length of ``rows`` is used
    as a floor.

    The per-period trial Sharpes are ``sharpe / sqrt(252)``; their sample
    variance (ddof=1) over the finite ones is ``sr_var_across_trials`` (errored
    trials carry no Sharpe, so they widen ``n_trials`` without entering the
    variance). With fewer than 2 finite trial Sharpes the variance is undefined
    and every DSR is NaN.
    """
    from tradingos.analytics.dsr import deflated_sharpe_ratio

    n_trials = max(n_trials or 0, len(rows))
    periodic = [
        r.sharpe / _SQRT_TRADING_DAYS
        for r in rows
        if r.sharpe is not None and math.isfinite(r.sharpe)
    ]
    if len(periodic) >= 2:
        mean = sum(periodic) / len(periodic)
        sr_var = sum((x - mean) ** 2 for x in periodic) / (len(periodic) - 1)  # ddof=1
    else:
        sr_var = math.nan

    out: dict[int, float] = {}
    for r in rows:
        sr = (
            r.sharpe / _SQRT_TRADING_DAYS
            if r.sharpe is not None and math.isfinite(r.sharpe)
            else math.nan
        )
        out[int(r.id)] = deflated_sharpe_ratio(  # type: ignore[arg-type]
            sr=sr,
            n_trials=n_trials,
            t=int(r.n_bars) if r.n_bars is not None else 0,
            skew=r.ret_skew if r.ret_skew is not None else math.nan,
            kurt=r.ret_kurt if r.ret_kurt is not None else math.nan,
            sr_var_across_trials=sr_var,
        )
    return out


def _compact_overrides(overrides_json: str) -> str:
    """Render the sweep overrides as a compact ``k=v, k2=v2`` string."""
    try:
        data = json.loads(overrides_json)
    except (json.JSONDecodeError, TypeError):
        return ""
    return ", ".join(f"{k}={v}" for k, v in sorted(data.items()))


def leaderboard(
    settings: Settings,
    family: str | None = None,
    top: int = 20,
    sort: str = "sharpe",
) -> pd.DataFrame:
    """Leaderboard over non-holdout, done runs (optionally one ``family``).

    DSR is computed per family at query time; its ``n_trials`` counts EVERY
    non-holdout run registered for the family — errored variants included —
    because an errored variant was still a trial (see :func:`_family_dsr` for
    the family-name multiple-testing boundary). Sorted by ``sort`` descending
    with NaNs last; the top ``top`` rows are returned. Columns are fixed (both
    ``sharpe`` and ``dsr`` always present). ``tainted`` is True when the run
    carries a bias-critical warning (survivorship fallback, universe coverage
    gap, look-ahead) persisted at run time; ``n_warnings`` counts all persisted
    engine/universe warnings."""
    with Session(get_engine(settings)) as session:
        stmt = (
            select(ExperimentRun)
            .where(ExperimentRun.is_holdout == False)  # noqa: E712 — SQL identity
            .where(ExperimentRun.status == "done")
        )
        if family is not None:
            stmt = stmt.where(ExperimentRun.family == family)
        rows = list(session.exec(stmt).all())

        # n_trials per family: ALL non-holdout attempts, errored included.
        trials_stmt = (
            select(ExperimentRun.family, func.count())  # type: ignore[call-overload]
            .where(ExperimentRun.is_holdout == False)  # noqa: E712 — SQL identity
            .group_by(ExperimentRun.family)
        )
        if family is not None:
            trials_stmt = trials_stmt.where(ExperimentRun.family == family)
        n_trials_by_family = {fam: int(n) for fam, n in session.exec(trials_stmt).all()}

    if not rows:
        return pd.DataFrame(columns=_LEADERBOARD_COLUMNS)

    # DSR is per-family: group, compute, then flatten back to a row->dsr map.
    dsr_by_id: dict[int, float] = {}
    families = {r.family for r in rows}
    for fam in families:
        fam_rows = [r for r in rows if r.family == fam]
        dsr_by_id.update(_family_dsr(fam_rows, n_trials=n_trials_by_family.get(fam)))

    def _record(r: ExperimentRun) -> dict[str, Any]:
        warnings = parse_warnings(r.warnings_json)
        return {
            "id": int(r.id),  # type: ignore[arg-type]
            "family": r.family,
            "variant_name": r.variant_name,
            "engine": r.engine,
            "sharpe": r.sharpe,
            "dsr": dsr_by_id.get(int(r.id), math.nan),  # type: ignore[arg-type]
            "cagr": r.cagr,
            "max_drawdown": r.max_drawdown,
            "calmar": r.calmar,
            "total_costs_pct": r.total_costs_pct,
            "n_trades": r.n_trades,
            "tainted": is_bias_tainted(warnings),
            "n_warnings": len(warnings),
            "overrides": _compact_overrides(r.overrides_json),
        }

    records = [_record(r) for r in rows]
    frame = pd.DataFrame.from_records(records, columns=_LEADERBOARD_COLUMNS)

    if sort not in frame.columns:
        raise ValueError(f"cannot sort leaderboard by {sort!r}; columns: {_LEADERBOARD_COLUMNS}")
    frame = frame.sort_values(sort, ascending=False, na_position="last").reset_index(drop=True)
    return frame.head(top)


# --------------------------------------------------------------------------- #
# Pairwise comparison                                                          #
# --------------------------------------------------------------------------- #
def get_run(run_id: int, settings: Settings) -> ExperimentRun:
    """Fetch one run row (detached, safe to read after the session closes)."""
    with Session(get_engine(settings)) as session:
        run = session.get(ExperimentRun, run_id)
        if run is None:
            raise DataError(f"no experiment run with id {run_id}")
        session.expunge(run)  # no commit occurred, so loaded state stays intact
        return run


def compare(
    run_id_a: int,
    run_id_b: int,
    settings: Settings,
    out_path: Path | None = None,
) -> pd.DataFrame:
    """Two-column metric table for two runs. When ``out_path`` is given, also
    write a self-contained plotly HTML overlaying the two equity curves."""
    run_a = get_run(run_id_a, settings)
    run_b = get_run(run_id_b, settings)

    metrics_a: dict[str, Any] = json.loads(run_a.metrics_json or "{}")
    metrics_b: dict[str, Any] = json.loads(run_b.metrics_json or "{}")
    col_a = f"{run_a.variant_name} (#{run_id_a})"
    col_b = f"{run_b.variant_name} (#{run_id_b})"

    keys = list(dict.fromkeys([*metrics_a.keys(), *metrics_b.keys()]))
    table = pd.DataFrame(
        {
            col_a: [metrics_a.get(k, math.nan) for k in keys],
            col_b: [metrics_b.get(k, math.nan) for k in keys],
        },
        index=keys,
    )
    table.index.name = "metric"

    if out_path is not None:
        _write_compare_html(run_a, run_b, col_a, col_b, Path(out_path))
    return table


def _write_compare_html(
    run_a: ExperimentRun,
    run_b: ExperimentRun,
    label_a: str,
    label_b: str,
    out_path: Path,
) -> None:
    """Overlay two runs' equity curves in a self-contained plotly HTML."""
    import plotly.graph_objects as go
    import plotly.io as pio

    from tradingos.engine.result import BacktestResult

    eq_a = BacktestResult.load(Path(run_a.artifacts_path)).equity
    eq_b = BacktestResult.load(Path(run_b.artifacts_path)).equity

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=eq_a.index, y=eq_a, name=label_a, mode="lines"))
    fig.add_trace(go.Scatter(x=eq_b.index, y=eq_b, name=label_b, mode="lines"))
    fig.update_layout(
        title=f"Equity comparison: {label_a} vs {label_b}",
        xaxis_title="Date",
        yaxis_title="Equity (₹)",
        template="plotly_white",
        legend={"orientation": "h"},
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = pio.to_html(
        fig,
        include_plotlyjs="inline",
        full_html=True,
        div_id="tos-compare-equity",  # deterministic id (matches tearsheet.py)
        config={"displayModeBar": False},
        auto_play=False,
    )
    out_path.write_text(html, encoding="utf-8")


# --------------------------------------------------------------------------- #
# Exact reproduction                                                           #
# --------------------------------------------------------------------------- #
def reproduce(
    run_id: int,
    settings: Settings,
    timeframe: Timeframe = Timeframe.DAY,
    adjusted: bool = True,
) -> bool:
    """Re-run ``run_id`` from its stored config and compare the equity curve to
    the saved artifacts copy exactly. Returns True on a bit-for-bit match, False
    otherwise (differences are logged). This is the spec's "every run exactly
    reproducible" check."""
    from datetime import timedelta

    from tradingos.data.store import BarStore
    from tradingos.engine.result import BacktestResult
    from tradingos.experiments.runner import make_engine, make_universe_resolver, resolve_symbols

    run = get_run(run_id, settings)
    config = StrategyConfig.model_validate(json.loads(run.config_json))

    # Reconstruct the exact window this run executed on.
    if run.is_holdout:
        start = (run.train_end + timedelta(days=1)) if run.train_end else config.start
        config = config.model_copy(update={"start": start, "end": config.end})
    else:
        config = config.model_copy(update={"end": run.train_end})

    store = BarStore(settings)
    symbols = resolve_symbols(config, store, timeframe)
    data = store.load_market_data(symbols, timeframe, adjusted=adjusted)
    if not data.symbols:
        logger.warning("reproduce(%s): no data loaded for %s", run_id, symbols)
        return False

    engine = make_engine(EngineMode(run.engine))
    fresh = engine.run(config, data, make_universe_resolver(settings))
    saved = BacktestResult.load(Path(run.artifacts_path)).equity

    try:
        pd.testing.assert_series_equal(
            fresh.equity, saved, check_freq=False, check_names=False
        )
    except AssertionError as exc:
        logger.warning("reproduce(%s): equity mismatch:\n%s", run_id, exc)
        return False
    return True


__all__ = ["leaderboard", "compare", "get_run", "reproduce"]

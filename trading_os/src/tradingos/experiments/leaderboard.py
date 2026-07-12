"""Leaderboard, pairwise comparison, and exact-reproduction checks.

The Deflated Sharpe Ratio is computed AT QUERY TIME per family (never stored):
its value depends on ``N`` — the number of trials in the family — which grows as
more variants are registered, so a stored column would go stale. See
:func:`_family_dsr` for exactly how the DSR inputs are assembled.
"""

from __future__ import annotations

import fnmatch
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


# --------------------------------------------------------------------------- #
# Marking (owner curation) — a marked run is the default baseline for          #
# ``compare_runs`` / ``platform experiments compare --markdown``.              #
# --------------------------------------------------------------------------- #
def mark_run(run_id: int, settings: Settings, marked: bool = True) -> ExperimentRun:
    """Set (``marked=True``) or clear (``marked=False``) ``is_marked`` on a run.

    Returns the updated, detached row. Raises :class:`DataError` if the run
    does not exist (mirrors :func:`get_run`)."""
    with Session(get_engine(settings)) as session:
        run = session.get(ExperimentRun, run_id)
        if run is None:
            raise DataError(f"no experiment run with id {run_id}")
        run.is_marked = marked
        session.add(run)
        session.commit()
        session.refresh(run)
        session.expunge(run)
        return run


def latest_marked_run(settings: Settings) -> ExperimentRun | None:
    """The most recently marked run (highest id among ``is_marked`` rows), or
    ``None`` if nothing is marked. This is the implicit ``compare --baseline``
    default."""
    with Session(get_engine(settings)) as session:
        stmt = (
            select(ExperimentRun)
            .where(ExperimentRun.is_marked == True)  # noqa: E712 — SQL identity
            .order_by(ExperimentRun.id.desc())  # type: ignore[union-attr]
        )
        row = session.exec(stmt).first()
        if row is not None:
            session.expunge(row)
        return row


# --------------------------------------------------------------------------- #
# Family / baseline comparison (markdown-friendly multi-run report)           #
# --------------------------------------------------------------------------- #
_COMPARE_COLUMNS = [
    "id",
    "family",
    "variant_name",
    "is_baseline",
    "net_return_pct",
    "max_drawdown_pct",
    "sharpe",
    "n_trades",
    "total_costs_pct",
    "delta_net_pp",
    "delta_dd_pp",
    "delta_sharpe",
]


def _pct(x: float | None) -> float:
    """Fraction -> percentage points, tolerant of ``None``/NaN/non-finite."""
    if x is None:
        return math.nan
    xf = float(x)
    return xf * 100.0 if math.isfinite(xf) else math.nan


def _metric_record(r: ExperimentRun) -> dict[str, float]:
    """Derive the compare-table metric columns for one run.

    ``net_return_pct`` prefers the stored ``metrics_json["total_return"]``
    (computed once, net-of-cost, in :func:`analytics.metrics.compute_metrics`);
    when that is missing/NaN it falls back to ``final_equity / capital - 1``
    using the capital recorded in this run's own ``config_json`` (the
    unclamped variant config), never a caller-supplied default.
    """
    try:
        metrics: dict[str, Any] = json.loads(r.metrics_json or "{}")
    except (json.JSONDecodeError, TypeError):
        metrics = {}

    total_return = metrics.get("total_return")
    if not isinstance(total_return, (int, float)) or not math.isfinite(float(total_return)):
        capital: float | None = None
        try:
            capital = json.loads(r.config_json or "{}").get("capital")
        except (json.JSONDecodeError, TypeError):
            capital = None
        if capital and r.final_equity is not None:
            total_return = r.final_equity / capital - 1.0
        else:
            total_return = math.nan

    max_dd = r.max_drawdown if r.max_drawdown is not None else metrics.get("max_drawdown")
    costs_pct = r.total_costs_pct if r.total_costs_pct is not None else metrics.get(
        "total_costs_pct"
    )

    return {
        "net_return_pct": _pct(float(total_return)),
        "max_drawdown_pct": _pct(max_dd),
        "sharpe": float(r.sharpe) if r.sharpe is not None else math.nan,
        "n_trades": float(r.n_trades) if r.n_trades is not None else math.nan,
        "total_costs_pct": _pct(costs_pct),
    }


def compare_runs(
    settings: Settings,
    families: str | None = None,
    baseline: int | None = None,
    all_runs: bool = False,
) -> pd.DataFrame:
    """Multi-run comparison table: one row per selected run plus Δ-vs-baseline
    columns, for ``platform experiments compare --families/--baseline/--markdown``.

    Selection
    ---------
    * ``families`` is an ``fnmatch`` glob against ``ExperimentRun.family``
      (e.g. ``"adhoc_b2*"``); ``None`` matches every family.
    * Only ``status == "done"`` runs are considered (errored runs carry no
      metrics).
    * Unless ``all_runs`` is True, only the latest run (by ``finished_at``,
      ties broken by id) per family is kept.
    * The baseline run — explicit ``baseline`` id, else :func:`latest_marked_run`
      — is always included and labeled, even if it does not match ``families``
      or would otherwise be excluded by the latest-per-family rule.

    Columns: see ``_COMPARE_COLUMNS``. ``net_return_pct``/``max_drawdown_pct``/
    ``total_costs_pct`` are percentage points; ``delta_*`` columns are the
    row's value minus the baseline's (0.0 on the baseline's own row; NaN
    throughout when there is no baseline).
    """
    with Session(get_engine(settings)) as session:
        rows = list(session.exec(select(ExperimentRun).where(ExperimentRun.status == "done")).all())
        session.expunge_all()

    selected = (
        [r for r in rows if fnmatch.fnmatch(r.family, families)] if families is not None else rows
    )

    if not all_runs:
        latest_by_family: dict[str, ExperimentRun] = {}
        for r in selected:
            cur = latest_by_family.get(r.family)
            if cur is None or (r.finished_at, r.id) > (cur.finished_at, cur.id):
                latest_by_family[r.family] = r
        selected = list(latest_by_family.values())

    baseline_run: ExperimentRun | None
    if baseline is not None:
        baseline_run = get_run(baseline, settings)
    else:
        baseline_run = latest_marked_run(settings)

    if baseline_run is not None and all(r.id != baseline_run.id for r in selected):
        selected = [baseline_run, *selected]

    selected.sort(key=lambda r: (r.family, r.variant_name))

    baseline_metrics = _metric_record(baseline_run) if baseline_run is not None else None

    records: list[dict[str, Any]] = []
    for r in selected:
        m = _metric_record(r)
        is_base = baseline_run is not None and r.id == baseline_run.id
        if baseline_metrics is None:
            delta_net = delta_dd = delta_sharpe = math.nan
        elif is_base:
            delta_net = delta_dd = delta_sharpe = 0.0
        else:
            delta_net = m["net_return_pct"] - baseline_metrics["net_return_pct"]
            delta_dd = m["max_drawdown_pct"] - baseline_metrics["max_drawdown_pct"]
            delta_sharpe = m["sharpe"] - baseline_metrics["sharpe"]
        records.append(
            {
                "id": int(r.id),  # type: ignore[arg-type]
                "family": r.family,
                "variant_name": r.variant_name + (" (baseline)" if is_base else ""),
                "is_baseline": is_base,
                **m,
                "delta_net_pp": delta_net,
                "delta_dd_pp": delta_dd,
                "delta_sharpe": delta_sharpe,
            }
        )

    return pd.DataFrame.from_records(records, columns=_COMPARE_COLUMNS)


def to_markdown_table(frame: pd.DataFrame) -> str:
    """Render a compare/leaderboard-style DataFrame as a GitHub-flavored
    markdown table (no external markdown dependency)."""
    if frame.empty:
        return "(no runs to compare)"

    def _cell(v: Any) -> str:
        if isinstance(v, float):
            return "nan" if math.isnan(v) else f"{v:.2f}"
        return str(v)

    headers = list(frame.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(_cell(row[h]) for h in headers) + " |")
    return "\n".join(lines)


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


__all__ = [
    "leaderboard",
    "compare",
    "compare_runs",
    "get_run",
    "latest_marked_run",
    "mark_run",
    "reproduce",
    "to_markdown_table",
]

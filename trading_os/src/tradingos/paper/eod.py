"""EOD divergence report: paper session vs a reference backtest.

Renders a self-contained, offline HTML report (equity overlay, cumulative
divergence, side-by-side metrics, open positions) plus a machine-readable
JSON summary for one trading day of a paper session. No new financial math
lives here — all metric arithmetic is delegated to
:func:`tradingos.analytics.metrics.compute_metrics`; the only computation
this module owns is pandas index alignment (gross-equity reconstruction,
the paper/reference join). See CLAUDE.md rule 5.

Heavy imports (plotly) are deferred into the functions that need them, per
the pattern in ``analytics/tearsheet.py``, whose CSS/plotly-html helpers are
reused directly so the report matches the rest of the platform's look.
"""

from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from tradingos.analytics.metrics import compute_metrics
from tradingos.analytics.tearsheet import _CSS, _esc, _fig_html, _money
from tradingos.config.schemas import EngineMode, StrategyConfig
from tradingos.config.settings import Settings
from tradingos.core.logging import get_logger
from tradingos.core.models import Fill, Position
from tradingos.engine.event.portfolio import Ledger
from tradingos.engine.result import BacktestResult
from tradingos.paper.ledgerdb import PaperStore

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# BacktestResult reconstruction from a paper session
# ---------------------------------------------------------------------------


def _daily_last(equity: pd.Series) -> pd.Series:
    """Collapse an intraday snapshot curve to ONE point per calendar day (each
    day's LAST snapshot, keeping its original timestamp).

    The paper store holds ~2 snapshots per trading day (the 09:15 day-start
    risk baseline and the 15:30 close), but ``BacktestResult`` /
    ``compute_metrics`` treat every equity point as one trading day (252/yr
    annualization) -- handing them the raw snapshot pairs would double the
    period count and distort every annualized metric (Sharpe, vol, CAGR).
    """
    if equity.empty:
        return equity
    day_index = pd.Index([pd.Timestamp(ts).date() for ts in equity.index])
    return equity[~day_index.duplicated(keep="last")]


def _gross_equity(equity: pd.Series, fills: list[Fill]) -> pd.Series:
    """``gross[t] = equity[t] + cumulative charges of fills with ts <= t``,
    aligned onto the snapshot index ``equity.index`` (mirrors the event
    engine's ``gross_equity == net_equity + cumulative_costs`` identity)."""
    if not fills:
        gross = equity.copy()
        gross.name = "gross_equity"
        return gross

    fill_ts = pd.DatetimeIndex([f.ts for f in fills])
    charges = pd.Series([f.charges for f in fills], index=fill_ts, dtype=float)
    cum = charges.cumsum()
    # Multiple fills can share a timestamp; keep the final (largest) cumulative
    # value for each distinct ts so the as-of alignment below is unambiguous.
    cum = cum[~cum.index.duplicated(keep="last")]

    combined = cum.index.union(equity.index)
    cum_aligned = cum.reindex(combined).sort_index().ffill().reindex(equity.index).fillna(0.0)

    gross = equity + cum_aligned
    gross.name = "gross_equity"
    return gross


def build_paper_result(store: PaperStore, config: StrategyConfig) -> BacktestResult:
    """Reconstruct a paper trading session as a :class:`BacktestResult`.

    ``equity`` is ``store.equity_curve()`` collapsed to one point per day (the
    day's last snapshot -- see :func:`_daily_last`; raises ``ValueError`` if
    there are no snapshots yet — a report needs at least one). ``trades`` is
    obtained by replaying ``store.all_fills()`` through a fresh :class:`Ledger`
    and keeping the non-``None`` returns of ``apply_fill`` — charges are never
    recomputed, only read off the stored fills.
    """
    equity = _daily_last(store.equity_curve())
    if equity.empty:
        raise ValueError(
            f"paper store for strategy {store.strategy_id!r} has no equity snapshots yet"
        )

    fills = store.all_fills()
    gross_equity = _gross_equity(equity, fills)

    # Contract-specified precedence (paper/eod.py contract, section G): the
    # stored run capital wins whenever truthy, else the strategy's declared
    # capital. Note this is an `or`, not an `is None` check, so a (nonsensical
    # but representable) stored capital of exactly 0.0 would also fall back to
    # config.capital — flagged in the implementation summary.
    capital = store.capital() or config.capital

    ledger = Ledger(capital, strategy_id=config.name)
    trades = [t for f in fills if (t := ledger.apply_fill(f)) is not None]

    total_costs = sum(f.charges for f in fills)

    return BacktestResult(
        config=config,
        engine=EngineMode.EVENT,
        start=equity.index[0].date(),
        end=equity.index[-1].date(),
        capital=capital,
        equity=equity,
        gross_equity=gross_equity,
        trades=trades,
        total_costs=total_costs,
        warnings=[],
        meta={"source": "paper"},
    )


# ---------------------------------------------------------------------------
# Reference backtest
# ---------------------------------------------------------------------------


def load_reference(
    config: StrategyConfig, settings: Settings, *, run_dir: Path | None = None
) -> BacktestResult | None:
    """Load the backtest run this paper session should track.

    ``run_dir`` given -> load it directly. Else look for the conventional
    artifacts location ``<artifacts_dir>/runs/<name>-<config_hash>`` (the same
    layout ``cli/backtest_cmds.py`` writes to); if it isn't there, return
    ``None`` so the report degrades to a paper-only view.
    """
    if run_dir is not None:
        return BacktestResult.load(run_dir)

    conventional = Path(settings.artifacts_dir) / "runs" / f"{config.name}-{config.config_hash()}"
    if (conventional / "meta.json").exists():
        return BacktestResult.load(conventional)

    logger.info(
        "no reference backtest found for %r at %s; EOD report will be paper-only",
        config.name,
        conventional,
    )
    return None


# ---------------------------------------------------------------------------
# Divergence
# ---------------------------------------------------------------------------

_DIVERGENCE_COLUMNS = ("paper_equity", "ref_equity", "paper_ret", "ref_ret", "cum_diff_pct")


def _date_series(equity: pd.Series) -> pd.Series:
    """Normalize an equity curve's index to plain ``date`` objects, keeping
    the last value for any timestamps that collapse onto the same date."""
    idx = pd.Index([pd.Timestamp(ts).date() for ts in equity.index], name="date")
    out = pd.Series(equity.to_numpy(dtype=float), index=idx)
    return out[~out.index.duplicated(keep="last")]


def divergence_frame(paper: BacktestResult, reference: BacktestResult) -> pd.DataFrame:
    """Inner-join the paper and reference equity curves on common dates.

    Columns: ``paper_equity``, ``ref_equity``, ``paper_ret``/``ref_ret``
    (``pct_change`` of the JOINED series, first row forced to 0.0),
    ``cum_diff_pct = paper_equity / paper_equity[0] - ref_equity / ref_equity[0]``.
    An empty overlap returns an empty frame with these columns.
    """
    paper_s = _date_series(paper.equity).rename("paper_equity")
    ref_s = _date_series(reference.equity).rename("ref_equity")

    joined = pd.concat([paper_s, ref_s], axis=1, join="inner").sort_index()
    if joined.empty:
        return pd.DataFrame(columns=list(_DIVERGENCE_COLUMNS))

    paper_ret = joined["paper_equity"].pct_change().fillna(0.0)
    ref_ret = joined["ref_equity"].pct_change().fillna(0.0)
    cum_diff_pct = (
        joined["paper_equity"] / joined["paper_equity"].iloc[0]
        - joined["ref_equity"] / joined["ref_equity"].iloc[0]
    )

    return pd.DataFrame(
        {
            "paper_equity": joined["paper_equity"],
            "ref_equity": joined["ref_equity"],
            "paper_ret": paper_ret,
            "ref_ret": ref_ret,
            "cum_diff_pct": cum_diff_pct,
        }
    )


# ---------------------------------------------------------------------------
# HTML / JSON report rendering
# ---------------------------------------------------------------------------


def _fmt_metric(value: float) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"  # em dash
    return f"{value:.4f}"


def _equity_overlay_figure(
    paper: BacktestResult, reference: BacktestResult | None, include_js: bool
) -> str:
    import plotly.graph_objects as go

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=paper.equity.index, y=paper.equity, name="Paper equity", mode="lines")
    )
    if reference is not None:
        fig.add_trace(
            go.Scatter(
                x=reference.equity.index,
                y=reference.equity,
                name="Reference equity",
                mode="lines",
                line={"dash": "dash"},
            )
        )
    fig.update_layout(
        title="Equity: paper vs reference",
        xaxis_title="Date",
        yaxis_title="Equity (₹)",
        template="plotly_white",
        legend={"orientation": "h"},
    )
    return _fig_html(fig, "eod-equity", include_js)


def _divergence_figure(frame: pd.DataFrame, include_js: bool) -> str:
    import plotly.graph_objects as go

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=list(frame.index),
            y=frame["cum_diff_pct"] * 100.0,
            name="Cumulative divergence",
            mode="lines",
            fill="tozeroy",
            line={"color": "crimson"},
        )
    )
    fig.update_layout(
        title="Paper vs reference cumulative divergence",
        xaxis_title="Date",
        yaxis_title="Divergence (%)",
        template="plotly_white",
    )
    return _fig_html(fig, "eod-divergence", include_js)


def _metrics_table_html(
    paper_metrics: dict[str, float], ref_metrics: dict[str, float] | None
) -> str:
    header = "<tr><th>Metric</th><th>Paper</th>"
    if ref_metrics is not None:
        header += "<th>Reference</th>"
    header += "</tr>"

    rows = []
    for key, pv in paper_metrics.items():
        row = f"<tr><td>{_esc(key)}</td><td>{_fmt_metric(pv)}</td>"
        if ref_metrics is not None:
            row += f"<td>{_fmt_metric(ref_metrics.get(key, math.nan))}</td>"
        row += "</tr>"
        rows.append(row)

    return f"""
    <section>
      <h2>Metrics</h2>
      <table class="meta-table">{header}{"".join(rows)}</table>
    </section>
    """


def _positions_table_html(positions: list[Position]) -> str:
    if not positions:
        return """
        <section>
          <h2>Open positions</h2>
          <p><em>No open positions.</em></p>
        </section>
        """
    header = (
        "<tr><th>Symbol</th><th>Qty</th><th>Avg price</th><th>Last price</th>"
        "<th>Unrealized P&amp;L</th></tr>"
    )
    body = "".join(
        f"<tr><td>{_esc(p.symbol)}</td><td>{p.qty}</td><td>{_money(p.avg_price)}</td>"
        f"<td>{_money(p.last_price) if p.last_price is not None else '—'}</td>"
        f"<td>{_money(p.unrealized_pnl)}</td></tr>"
        for p in positions
    )
    return f"""
    <section>
      <h2>Open positions</h2>
      <table class="trades-table">{header}{body}</table>
    </section>
    """


def write_eod_report(
    paper: BacktestResult,
    reference: BacktestResult | None,
    positions: list[Position],
    out_dir: Path,
    day: date,
) -> Path:
    """Write ``out_dir/eod-<day>.html`` (self-contained plotly report) and
    ``out_dir/eod-<day>.json`` (machine summary). Returns the HTML path."""
    out_dir.mkdir(parents=True, exist_ok=True)

    paper_metrics = compute_metrics(paper)
    ref_metrics = compute_metrics(reference) if reference is not None else None
    frame = divergence_frame(paper, reference) if reference is not None else pd.DataFrame()

    paper_equity_final = float(paper.equity.iloc[-1])
    ref_equity_final = float(reference.equity.iloc[-1]) if reference is not None else None
    cum_diff_pct_final = float(frame["cum_diff_pct"].iloc[-1]) if not frame.empty else None

    equity_html = _equity_overlay_figure(paper, reference, include_js=True)
    if not frame.empty:
        divergence_html = _divergence_figure(frame, include_js=False)
    else:
        divergence_html = "<p><em>No reference run overlap available for divergence.</em></p>"

    title = f"{paper.config.name} — EOD report {day.isoformat()}"
    ref_equity_html = (
        _money(ref_equity_final) if ref_equity_final is not None else "n/a (no reference run)"
    )
    cum_diff_html = (
        f"{cum_diff_pct_final * 100:.3f}%" if cum_diff_pct_final is not None else "n/a"
    )

    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{_esc(title)}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="header">
  <h1>{_esc(title)}</h1>
  <table class="meta-table">
    <tr><th>Strategy</th><td>{_esc(paper.config.name)}</td></tr>
    <tr><th>Date</th><td>{_esc(day.isoformat())}</td></tr>
    <tr><th>Paper equity</th><td>{_money(paper_equity_final)}</td></tr>
    <tr><th>Reference equity</th><td>{ref_equity_html}</td></tr>
    <tr><th>Cumulative divergence</th><td>{cum_diff_html}</td></tr>
    <tr><th>Open positions</th><td>{len(positions)}</td></tr>
  </table>
</div>
<section><h2>Equity: paper vs reference</h2>{equity_html}</section>
<section><h2>Divergence</h2>{divergence_html}</section>
{_metrics_table_html(paper_metrics, ref_metrics)}
{_positions_table_html(positions)}
</body>
</html>
"""
    html_path = out_dir / f"eod-{day.isoformat()}.html"
    html_path.write_text(doc, encoding="utf-8")

    summary: dict[str, Any] = {
        "date": day.isoformat(),
        "paper_equity_final": paper_equity_final,
        "ref_equity_final": ref_equity_final,
        "cum_diff_pct_final": cum_diff_pct_final,
        "n_open_positions": len(positions),
        "paper_metrics": paper_metrics,
        "ref_metrics": ref_metrics,
    }
    json_path = out_dir / f"eod-{day.isoformat()}.json"
    json_path.write_text(json.dumps(summary, indent=1, default=str))

    return html_path


# ---------------------------------------------------------------------------
# Glue
# ---------------------------------------------------------------------------


def run_eod(
    settings: Settings,
    config: StrategyConfig,
    store: PaperStore,
    positions: list[Position],
    *,
    reference_run_dir: Path | None = None,
    day: date | None = None,
) -> Path:
    """Build the paper result, load the (optional) reference backtest, and
    write the EOD report under ``<artifacts_dir>/paper/<config.name>/``."""
    paper = build_paper_result(store, config)
    if day is None:
        day = paper.equity.index[-1].date()

    reference = load_reference(config, settings, run_dir=reference_run_dir)

    out_dir = Path(settings.artifacts_dir) / "paper" / config.name
    return write_eod_report(paper, reference, positions, out_dir, day)


__all__ = [
    "build_paper_result",
    "load_reference",
    "divergence_frame",
    "write_eod_report",
    "run_eod",
]

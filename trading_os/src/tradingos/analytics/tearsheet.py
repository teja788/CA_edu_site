"""Backtest report outputs: quantstats HTML tearsheet + the platform's own
self-contained plotly HTML report.

``quantstats`` compatibility note (installed ``quantstats==0.0.81`` against
``pandas==3.0.3``, the versions pinned in ``pyproject.toml``, verified
empirically): ``quantstats.reports.html`` runs cleanly against pandas 3 as of
this writing — no monkeypatch is required today. ``quantstats`` has a
documented history of lagging pandas API changes, so :func:`quantstats_tearsheet`
still wraps the whole call in a broad try/except and degrades to ``None`` on
any failure (import or generation) rather than ever crashing a report run.
:func:`plotly_report` is the platform's own, always-available report and is
the primary artifact; treat the quantstats tearsheet as a bonus.

Heavy imports (plotly, quantstats, matplotlib) are deferred into the
functions that need them so importing this module stays cheap.
"""

from __future__ import annotations

import html as html_lib
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

from tradingos.analytics.metrics import (
    TRADING_DAYS,
    compute_metrics,
    drawdown_series,
    monthly_returns,
    rolling_sharpe,
)
from tradingos.core.logging import get_logger

if TYPE_CHECKING:
    from tradingos.core.models import Trade
    from tradingos.engine.result import BacktestResult

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# quantstats tearsheet
# ---------------------------------------------------------------------------


def quantstats_tearsheet(
    result: BacktestResult,
    out_path: Path,
    benchmark: pd.Series | None = None,
    title: str | None = None,
) -> Path | None:
    """Generate a quantstats HTML tearsheet for ``result``.

    Graceful-degrade contract: if quantstats raises ANYWHERE (import or
    report generation), this logs a warning via ``tradingos.core.logging``
    and returns ``None`` — it never propagates the exception. Callers must
    treat this as a best-effort bonus artifact, not a required one; use
    :func:`plotly_report` for the platform's guaranteed report.

    ``benchmark``, if given, is passed straight through to quantstats as a
    price/level series (quantstats auto-detects prices vs. returns and calls
    ``pct_change`` internally when values look like a price level).
    """
    try:
        import matplotlib

        matplotlib.use("Agg")  # headless: never touch a display backend
        import quantstats as qs
    except Exception:
        logger.warning(
            "quantstats_tearsheet: quantstats import failed, skipping tearsheet", exc_info=True
        )
        return None

    try:
        returns = result.returns.copy()
        returns.index.name = None
        report_title = title or f"{result.config.name} — quantstats tearsheet"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        qs.reports.html(
            returns,
            benchmark=benchmark,
            title=report_title,
            output=str(out_path),
        )
    except Exception:
        logger.warning(
            "quantstats_tearsheet: report generation failed for %r, skipping",
            result.config.name,
            exc_info=True,
        )
        return None
    return out_path


def _trade_stats(trades: list[Trade]) -> dict[str, Any] | None:
    if not trades:
        return None
    n = len(trades)
    wins = [t for t in trades if t.net_pnl > 0]
    hit_rate = len(wins) / n
    avg_holding = sum(t.holding_days for t in trades) / n
    winners = sorted(trades, key=lambda t: t.net_pnl, reverse=True)[:10]
    losers = sorted(trades, key=lambda t: t.net_pnl)[:10]
    return {
        "count": n,
        "hit_rate": hit_rate,
        "avg_holding_days": avg_holding,
        "winners": winners,
        "losers": losers,
    }


# ---------------------------------------------------------------------------
# plotly figures (each returns an (html_snippet) via _fig_html)
# ---------------------------------------------------------------------------


def _fig_html(fig: Any, div_id: str, include_js: bool) -> str:
    import plotly.io as pio

    return pio.to_html(
        fig,
        include_plotlyjs="inline" if include_js else False,
        full_html=False,
        div_id=div_id,
        config={"displayModeBar": False},
        auto_play=False,
    )


def _equity_figure(
    result: BacktestResult, benchmark: pd.Series | None, include_js: bool
) -> str:
    import plotly.graph_objects as go

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=result.equity.index, y=result.equity, name="Net equity", mode="lines")
    )
    fig.add_trace(
        go.Scatter(
            x=result.gross_equity.index,
            y=result.gross_equity,
            name="Gross equity",
            mode="lines",
            line={"dash": "dot"},
        )
    )
    if benchmark is not None:
        bench = benchmark.reindex(result.equity.index).ffill().dropna()
        if not bench.empty:
            bench_rebased = bench / bench.iloc[0] * result.capital
            fig.add_trace(
                go.Scatter(
                    x=bench_rebased.index,
                    y=bench_rebased,
                    name="Benchmark (rebased)",
                    mode="lines",
                    line={"dash": "dash"},
                )
            )
    fig.update_layout(
        title="Equity curve",
        xaxis_title="Date",
        yaxis_title="Equity (₹)",
        template="plotly_white",
        legend={"orientation": "h"},
    )
    return _fig_html(fig, "tos-equity", include_js)


def _drawdown_figure(result: BacktestResult, include_js: bool) -> str:
    import plotly.graph_objects as go

    dd = drawdown_series(result.equity)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dd.index,
            y=dd * 100.0,
            name="Drawdown",
            mode="lines",
            fill="tozeroy",
            line={"color": "crimson"},
        )
    )
    fig.update_layout(
        title="Underwater plot (drawdown from running peak)",
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        template="plotly_white",
    )
    return _fig_html(fig, "tos-drawdown", include_js)


def _costs_figure(result: BacktestResult, include_js: bool) -> str:
    import plotly.graph_objects as go

    cum_costs = (result.gross_equity - result.equity).clip(lower=0.0)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=cum_costs.index,
            y=cum_costs,
            name="Cumulative costs",
            mode="lines",
            fill="tozeroy",
            line={"color": "darkorange"},
        )
    )
    fig.update_layout(
        title="Gross vs net: cumulative transaction costs",
        xaxis_title="Date",
        yaxis_title="Cumulative costs (₹)",
        template="plotly_white",
    )
    return _fig_html(fig, "tos-costs", include_js)


def _monthly_heatmap_figure(result: BacktestResult, include_js: bool) -> str:
    import plotly.graph_objects as go

    table = monthly_returns(result.equity)
    if table.empty:
        fig = go.Figure()
        fig.update_layout(title="Monthly returns (insufficient data)", template="plotly_white")
        return _fig_html(fig, "tos-monthly", include_js)
    z = (table * 100.0).to_numpy()
    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=list(table.columns),
            y=[str(y) for y in table.index],
            colorscale="RdYlGn",
            zmid=0.0,
            text=[[("" if pd.isna(v) else f"{v:.1f}%") for v in row] for row in z],
            texttemplate="%{text}",
            colorbar={"title": "%"},
        )
    )
    fig.update_layout(
        title="Monthly returns (%)",
        xaxis_title="Month",
        yaxis_title="Year",
        template="plotly_white",
    )
    return _fig_html(fig, "tos-monthly", include_js)


def _rolling_sharpe_figure(result: BacktestResult, include_js: bool) -> str:
    import plotly.graph_objects as go

    rs = rolling_sharpe(result.equity, window=TRADING_DAYS)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=rs.index, y=rs, name="Rolling Sharpe", mode="lines"))
    fig.update_layout(
        title=f"Rolling {TRADING_DAYS}-bar Sharpe",
        xaxis_title="Date",
        yaxis_title="Sharpe (annualized)",
        template="plotly_white",
    )
    return _fig_html(fig, "tos-rolling-sharpe", include_js)


def _trades_histogram_figure(trades: list[Trade], include_js: bool) -> str:
    import plotly.graph_objects as go

    fig = go.Figure()
    fig.add_trace(go.Histogram(x=[t.net_pnl for t in trades], name="Net P&L per trade"))
    fig.update_layout(
        title="Per-trade net P&L distribution",
        xaxis_title="Net P&L (₹)",
        yaxis_title="Count",
        template="plotly_white",
    )
    return _fig_html(fig, "tos-trades-hist", include_js)


# ---------------------------------------------------------------------------
# HTML assembly
# ---------------------------------------------------------------------------


def _esc(value: Any) -> str:
    # quote=False: these strings are only ever placed in text nodes, never in
    # HTML attributes, so preserving literal quote characters (e.g. inside
    # warning messages) keeps rendered text byte-identical to the source.
    return html_lib.escape(str(value), quote=False)


def _money(value: float) -> str:
    return f"₹{value:,.2f}"


def _header_html(result: BacktestResult, title: str | None) -> str:
    report_title = title or f"{result.config.name} — tearsheet"
    warnings_html = ""
    if result.warnings:
        items = "".join(f"<li>{_esc(w)}</li>" for w in result.warnings)
        warnings_html = f"""
        <div class="warning-banner">
          <strong>WARNINGS — read before trusting this report</strong>
          <ul>{items}</ul>
        </div>
        """
    return f"""
    <div class="header">
      <h1>{_esc(report_title)}</h1>
      <table class="meta-table">
        <tr><th>Strategy</th><td>{_esc(result.config.name)}</td></tr>
        <tr><th>Engine</th><td>{_esc(result.engine.value)}</td></tr>
        <tr><th>Window</th><td>{_esc(result.start)} → {_esc(result.end)}</td></tr>
        <tr><th>Capital</th><td>{_money(result.capital)}</td></tr>
        <tr><th>Config hash</th><td><code>{_esc(result.config.config_hash())}</code></td></tr>
      </table>
    </div>
    {warnings_html}
    """


def _stats_html(stats: dict[str, float]) -> str:
    rows = [
        ("Total return", f"{stats['total_return'] * 100:.2f}%"),
        ("CAGR", f"{stats['cagr'] * 100:.2f}%"),
        ("Volatility (annualized)", f"{stats['vol'] * 100:.2f}%"),
        ("Sharpe", f"{stats['sharpe']:.2f}"),
        ("Max drawdown", f"{stats['max_drawdown'] * 100:.2f}%"),
        ("Calmar", f"{stats['calmar']:.2f}"),
    ]
    body = "".join(f"<tr><th>{_esc(k)}</th><td>{_esc(v)}</td></tr>" for k, v in rows)
    return f"""
    <section>
      <h2>Summary statistics</h2>
      <table class="meta-table">{body}</table>
    </section>
    """


def _costs_stats_html(result: BacktestResult) -> str:
    net_profit = max(result.equity.iloc[-1] - result.capital, 0.0)
    stcg_rate = result.config.costs.stcg_tax_rate
    stcg_amount = stcg_rate * net_profit
    return f"""
    <section>
      <h2>Costs</h2>
      <table class="meta-table">
        <tr><th>Total costs</th><td>{_money(result.total_costs)}</td></tr>
        <tr><th>Costs as % of capital</th><td>{result.costs_pct_of_capital * 100:.2f}%</td></tr>
        <tr>
          <th>Informational STCG ({stcg_rate * 100:.0f}% of net profit)</th>
          <td>{_money(stcg_amount)} <em>(informational only — no holding-period
          classification is modeled; see docs/assumptions.md)</em></td>
        </tr>
      </table>
    </section>
    """


def _trades_section_html(trades: list[Trade], include_js: bool) -> str:
    stats = _trade_stats(trades)
    if stats is None:
        return """
        <section>
          <h2>Trades</h2>
          <p><em>No per-trade log for this run (e.g. a fast/vectorized-engine run,
          which reports portfolio-level results only). Trades: 0.</em></p>
        </section>
        """

    def _trade_row(t: Trade) -> str:
        return (
            f"<tr><td>{_esc(t.symbol)}</td><td>{t.qty}</td>"
            f"<td>{_esc(t.entry_ts.date())}</td><td>{_esc(t.exit_ts.date())}</td>"
            f"<td>{_money(t.entry_price)}</td><td>{_money(t.exit_price)}</td>"
            f"<td>{_money(t.net_pnl)}</td><td>{t.holding_days:.1f}</td>"
            f"<td>{_esc(t.exit_reason)}</td></tr>"
        )

    cols = (
        "<tr><th>Symbol</th><th>Qty</th><th>Entry</th><th>Exit</th><th>Entry px</th>"
        "<th>Exit px</th><th>Net P&L</th><th>Holding days</th><th>Exit reason</th></tr>"
    )
    winners_rows = "".join(_trade_row(t) for t in stats["winners"])
    losers_rows = "".join(_trade_row(t) for t in stats["losers"])
    hist_html = _trades_histogram_figure(trades, include_js)
    return f"""
    <section>
      <h2>Trades</h2>
      <table class="meta-table">
        <tr><th>Trades: {stats['count']}</th><td></td></tr>
        <tr><th>Hit rate</th><td>{stats['hit_rate'] * 100:.1f}%</td></tr>
        <tr><th>Avg holding days</th><td>{stats['avg_holding_days']:.1f}</td></tr>
      </table>
      <h3>Top 10 winners</h3>
      <table class="trades-table">{cols}{winners_rows}</table>
      <h3>Top 10 losers</h3>
      <table class="trades-table">{cols}{losers_rows}</table>
      {hist_html}
    </section>
    """


_CSS = """
body { font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 0;
       padding: 0 1.5rem 3rem; background: #ffffff; color: #1a1a1a; }
h1 { margin-bottom: 0.25rem; }
h2 { border-bottom: 2px solid #e0e0e0; padding-bottom: 0.25rem; margin-top: 2.5rem; }
.header { padding-top: 1.5rem; }
.warning-banner { background: #b00020; color: #ffffff; padding: 1rem 1.25rem;
  border-radius: 6px; margin: 1rem 0 2rem; font-size: 1.05rem; }
.warning-banner ul { margin: 0.5rem 0 0; padding-left: 1.25rem; }
table.meta-table { border-collapse: collapse; margin: 0.5rem 0 1rem; }
table.meta-table th, table.meta-table td { text-align: left; padding: 0.3rem 1rem 0.3rem 0; }
table.meta-table th { color: #555; font-weight: 600; white-space: nowrap; }
table.trades-table { border-collapse: collapse; width: 100%; margin-bottom: 1.5rem;
  font-size: 0.9rem; }
table.trades-table th, table.trades-table td { border: 1px solid #e0e0e0; padding: 0.3rem 0.6rem;
  text-align: right; }
table.trades-table th:first-child, table.trades-table td:first-child { text-align: left; }
section { margin-bottom: 1rem; }
code { background: #f2f2f2; padding: 0.1rem 0.35rem; border-radius: 3px; }
"""


def plotly_report(
    result: BacktestResult,
    out_path: Path,
    benchmark: pd.Series | None = None,
    title: str | None = None,
) -> Path:
    """Render the platform's self-contained plotly HTML tearsheet for
    ``result``. Fully offline (plotly.js is inlined) and deterministic for
    identical inputs: figures use explicit ``div_id``s and no timestamps or
    random ids are written into the body, so byte-identical output is
    produced across repeated calls on the same ``result``.
    """
    stats = compute_metrics(result, benchmark=benchmark)

    header_html = _header_html(result, title)
    stats_html = _stats_html(stats)
    equity_html = _equity_figure(result, benchmark, include_js=True)
    drawdown_html = _drawdown_figure(result, include_js=False)
    costs_stats_html = _costs_stats_html(result)
    costs_fig_html = _costs_figure(result, include_js=False)
    monthly_html = _monthly_heatmap_figure(result, include_js=False)
    rolling_sharpe_html = _rolling_sharpe_figure(result, include_js=False)
    trades_html = _trades_section_html(result.trades, include_js=False)

    report_title = title or f"{result.config.name} — tearsheet"
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{_esc(report_title)}</title>
<style>{_CSS}</style>
</head>
<body>
{header_html}
{stats_html}
<section><h2>Equity</h2>{equity_html}</section>
<section><h2>Drawdown</h2>{drawdown_html}</section>
{costs_stats_html}
<section>{costs_fig_html}</section>
<section><h2>Monthly returns</h2>{monthly_html}</section>
<section><h2>Rolling Sharpe</h2>{rolling_sharpe_html}</section>
{trades_html}
</body>
</html>
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(doc, encoding="utf-8")
    return out_path

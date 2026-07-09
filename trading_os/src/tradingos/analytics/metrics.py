"""Performance metrics — the ONE place returns/risk statistics are computed.

Per CLAUDE.md rule 5, returns/metrics math lives here and nowhere else; every
downstream consumer (tearsheets, experiment leaderboards, reports) reads the
flat scalar dict produced by :func:`compute_metrics` rather than recomputing.

Conventions (also recorded in ``docs/assumptions.md``):

* Daily bar frequency is assumed — there are **252 trading days per year** and
  volatility / Sharpe are annualized with ``sqrt(252)`` (platform-wide
  convention, matching ``strategies/signals/factors.py``).
* The risk-free rate is **0 by design** (single-user INR cash-equity research;
  short-rate carry is out of scope). Sharpe/Sortino are therefore excess-of-zero.
* Per-bar returns are ``equity.pct_change().dropna()`` — the first (NaN) bar is
  dropped, giving ``T = len(equity) - 1`` return observations. (Note this
  differs from ``BacktestResult.returns`` which *fills* the first bar with 0 for
  plotting; metrics use the dropped series so the sample size is honest.)
* Every value returned is a plain ``float``; quantities that are undefined for
  the given input are ``math.nan`` (never ``None``, never ``±inf``).
* Degenerate inputs (empty equity, or a single bar) return a dict with the full
  key set, every value NaN — never an exception.
"""

from __future__ import annotations

import calendar
import math

import numpy as np
import pandas as pd

from tradingos.core.models import Trade
from tradingos.engine.result import BacktestResult

# Platform-wide annualization factor: 252 trading days / year (docs/assumptions.md).
TRADING_DAYS = 252
ANNUALIZATION = math.sqrt(TRADING_DAYS)

# The exact key set every metrics dict carries, in a stable order. Downstream
# consumers (experiments leaderboard, tearsheet) rely on these names verbatim.
_METRIC_KEYS: tuple[str, ...] = (
    "cagr",
    "vol",
    "sharpe",
    "sortino",
    "calmar",
    "max_drawdown",
    "max_dd_duration_days",
    "hit_rate",
    "turnover",
    "avg_holding_days",
    "exposure",
    "alpha",
    "beta",
    "n_trades",
    "total_costs_pct",
    "final_equity",
    "total_return",
)

# English month abbreviations for the monthly-returns table columns.
_MONTHS = [calendar.month_abbr[m] for m in range(1, 13)]  # ["Jan", ..., "Dec"]


def _f(x: float | np.floating) -> float:
    """Coerce to a finite float, mapping ``±inf``/``None``/NaN to ``math.nan``.

    Metrics must never leak ``inf`` (it poisons downstream sorting/serialization),
    so every scalar leaves this module through this guard.
    """
    if x is None:
        return math.nan
    xf = float(x)
    return xf if math.isfinite(xf) else math.nan


def _nan_dict() -> dict[str, float]:
    """A metrics dict with the full key set, all NaN (degenerate-input result)."""
    return {k: math.nan for k in _METRIC_KEYS}


def compute_metrics(
    result: BacktestResult, benchmark: pd.Series | None = None
) -> dict[str, float]:
    """Compute the full flat metric dict for a backtest.

    Parameters
    ----------
    result
        The backtest output. Uses ``result.equity`` (net-of-cost curve),
        ``result.trades``, ``result.total_costs`` and ``result.capital``.
    benchmark
        Optional benchmark **price/level** series (e.g. NIFTY closes) — NOT a
        return series. It is aligned to the equity index and differenced
        internally. When ``None`` (or when fewer than 3 bars overlap) the
        ``alpha``/``beta`` keys are NaN.

    Returns
    -------
    dict[str, float]
        Keys: see ``_METRIC_KEYS``. Every value is a float; undefined
        quantities are ``math.nan``.
    """
    equity = result.equity

    # --- Degenerate guard: need >= 2 equity points for a single return -------
    if equity is None or len(equity) < 2:
        return _nan_dict()

    # Per-bar returns: drop the leading NaN so T is the true observation count.
    returns = equity.pct_change().dropna()
    T = len(returns)
    if T == 0:  # equity had only equal/duplicate index edge — treat as degenerate
        return _nan_dict()

    initial = float(equity.iloc[0])
    final = float(equity.iloc[-1])
    r = returns.to_numpy(dtype=float)

    # --- Return / growth ----------------------------------------------------
    total_return = _f(final / initial - 1.0) if initial > 0 else math.nan
    # CAGR compounds the realized growth over T bars up to a 252-day year.
    if initial > 0 and final > 0 and T > 0:
        cagr = _f((final / initial) ** (TRADING_DAYS / T) - 1.0)
    else:
        cagr = math.nan

    # --- Volatility & risk-adjusted return ----------------------------------
    # Sample std (ddof=1); a single return or a flat curve gives std 0/NaN.
    std = float(np.std(r, ddof=1)) if T >= 2 else math.nan
    mean = float(np.mean(r))
    vol = _f(std * ANNUALIZATION) if math.isfinite(std) else math.nan
    sharpe = _f(mean / std * ANNUALIZATION) if (math.isfinite(std) and std > 0) else math.nan

    # Sortino: downside deviation is the RMS of below-target returns over the
    # FULL sample (target 0), NOT the std over losing days only.
    downside = np.minimum(r, 0.0)
    downside_dev = math.sqrt(float(np.mean(downside**2)))
    sortino = _f(mean / downside_dev * ANNUALIZATION) if downside_dev > 0 else math.nan

    # --- Drawdown -----------------------------------------------------------
    max_dd = _max_drawdown(equity)
    max_dd_dur = _max_dd_duration_days(equity)
    # Calmar ties annual growth to the worst peak-to-trough loss.
    calmar = _f(cagr / abs(max_dd)) if (math.isfinite(max_dd) and max_dd < 0) else math.nan

    # --- Trade-derived stats ------------------------------------------------
    trades = result.trades
    n_trades = float(len(trades))
    hit_rate = _hit_rate(trades)
    avg_holding_days = _avg_holding_days(trades)
    turnover = _turnover(trades, equity, T)
    exposure = _exposure(trades, equity)

    # --- Benchmark regression (alpha / beta) --------------------------------
    alpha, beta = _alpha_beta(equity, benchmark)

    # --- Costs / final level ------------------------------------------------
    total_costs_pct = (
        _f(result.total_costs / result.capital) if result.capital else math.nan
    )

    return {
        "cagr": cagr,
        "vol": vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "calmar": calmar,
        "max_drawdown": max_dd,
        "max_dd_duration_days": max_dd_dur,
        "hit_rate": hit_rate,
        "turnover": turnover,
        "avg_holding_days": avg_holding_days,
        "exposure": exposure,
        "alpha": alpha,
        "beta": beta,
        "n_trades": n_trades,
        "total_costs_pct": total_costs_pct,
        "final_equity": _f(final),
        "total_return": total_return,
    }


# --------------------------------------------------------------------------- #
# Drawdown helpers                                                            #
# --------------------------------------------------------------------------- #
def _max_drawdown(equity: pd.Series) -> float:
    """Deepest peak-to-trough decline, as a NEGATIVE fraction (e.g. -0.23)."""
    eq = equity.to_numpy(dtype=float)
    if eq.size == 0:
        return math.nan
    peak = np.maximum.accumulate(eq)
    dd = eq / peak - 1.0
    return _f(float(dd.min()))


def _max_dd_duration_days(equity: pd.Series) -> float:
    """Longest peak-to-recovery underwater stretch, in CALENDAR days.

    Measured as the largest calendar gap between two *non-adjacent* running
    highs (adjacent highs bracket no underwater bar, so a monotonically rising
    curve reports 0). If the series ends below its last high (never recovered),
    the trailing gap from that high to the final bar is counted.
    """
    eq = equity.to_numpy(dtype=float)
    idx = equity.index
    if eq.size == 0:
        return math.nan
    peak = np.maximum.accumulate(eq)
    # Positions that sit at a running high (drawdown == 0 at that bar).
    high_pos = np.flatnonzero(eq >= peak)

    durations: list[float] = []
    # Gap between successive highs that actually bracket underwater bars
    # (position difference > 1 means at least one lower bar sat between them).
    for a, b in zip(high_pos[:-1], high_pos[1:], strict=False):
        if b - a > 1:
            durations.append((idx[b] - idx[a]).days)
    # Trailing underwater: last high is not the final bar -> count to the end.
    last_high = int(high_pos[-1])
    if last_high != len(eq) - 1:
        durations.append((idx[-1] - idx[last_high]).days)

    return float(max(durations)) if durations else 0.0


def drawdown_series(equity: pd.Series) -> pd.Series:
    """Running drawdown ``equity / cummax(equity) - 1`` (<= 0), same index."""
    return equity / equity.cummax() - 1.0


def top_drawdowns(equity: pd.Series, n: int = 10) -> pd.DataFrame:
    """The ``n`` deepest drawdown episodes.

    Columns: ``peak`` (timestamp of the high the drawdown fell from),
    ``trough`` (timestamp of the lowest point), ``recovery`` (timestamp the
    equity first regained the peak — ``NaT`` if never recovered by the last
    bar), ``depth`` (negative fraction), ``days`` (calendar days peak ->
    recovery, or peak -> last bar if unrecovered). Sorted deepest first.
    """
    cols = ["peak", "trough", "recovery", "depth", "days"]
    if equity is None or len(equity) < 2:
        return pd.DataFrame(columns=cols)

    eq = equity.to_numpy(dtype=float)
    idx = equity.index
    peak_level = np.maximum.accumulate(eq)
    dd = eq / peak_level - 1.0
    underwater = dd < 0.0

    episodes: list[dict[str, object]] = []
    i = 0
    n_bars = len(eq)
    while i < n_bars:
        if not underwater[i]:
            i += 1
            continue
        # Episode runs [start, end] inclusive; the peak is the bar just before.
        start = i
        peak_idx = start - 1  # dd[0] is always 0, so start >= 1 -> peak_idx >= 0
        while i < n_bars and underwater[i]:
            i += 1
        end = i - 1
        seg = dd[start : end + 1]
        trough_idx = start + int(np.argmin(seg))
        recovered = end + 1 < n_bars  # the bar after the run is back at the high
        recovery_ts = idx[end + 1] if recovered else pd.NaT
        far_ts = idx[end + 1] if recovered else idx[-1]
        episodes.append(
            {
                "peak": idx[peak_idx],
                "trough": idx[trough_idx],
                "recovery": recovery_ts,
                "depth": _f(float(dd[trough_idx])),
                "days": float((far_ts - idx[peak_idx]).days),
            }
        )

    if not episodes:
        return pd.DataFrame(columns=cols)
    frame = pd.DataFrame(episodes, columns=cols)
    frame = frame.sort_values("depth").head(n).reset_index(drop=True)
    return frame


# --------------------------------------------------------------------------- #
# Trade-derived helpers                                                        #
# --------------------------------------------------------------------------- #
def _hit_rate(trades: list[Trade]) -> float:
    """Fraction of trades with net PnL > 0 (NaN if there are no trades)."""
    if not trades:
        return math.nan
    wins = sum(1 for t in trades if t.net_pnl > 0)
    return _f(wins / len(trades))


def _avg_holding_days(trades: list[Trade]) -> float:
    """Mean holding period in (fractional) days across trades (NaN if none)."""
    if not trades:
        return math.nan
    return _f(float(np.mean([t.holding_days for t in trades])))


def _turnover(trades: list[Trade], equity: pd.Series, T: int) -> float:
    """Annualized one-sided turnover.

    ``(Σ entry_notional + Σ exit_notional) / 2 / mean(equity) / years`` where
    ``years = T / 252``. The ``/ 2`` converts round-trip (buy+sell) traded value
    into a one-sided figure, so a portfolio that fully turns over once a year
    scores ~1.0. Notionals use ``qty * price`` (trade quantities are the
    positive round-trip size). NaN when there are no trades or years == 0.
    """
    if not trades or T <= 0:
        return math.nan
    entry_notional = sum(t.qty * t.entry_price for t in trades)
    exit_notional = sum(t.qty * t.exit_price for t in trades)
    traded_one_sided = (entry_notional + exit_notional) / 2.0
    mean_equity = float(equity.mean())
    years = T / TRADING_DAYS
    if mean_equity <= 0 or years <= 0:
        return math.nan
    return _f(traded_one_sided / mean_equity / years)


def _exposure(trades: list[Trade], equity: pd.Series) -> float:
    """Average gross exposure across bars.

    For each bar, sum the ENTRY notional (``qty * entry_price``) of trades open
    on that bar (``entry_ts <= bar < exit_ts``), divide by that bar's equity,
    and average over all bars. This is an entry-notional approximation: it holds
    the position value at its cost basis rather than marking it to each bar's
    price (avoids needing per-bar per-symbol prices here). NaN if no trades.
    """
    if not trades:
        return math.nan
    idx = equity.index
    open_notional = pd.Series(0.0, index=idx)
    for t in trades:
        entry = pd.Timestamp(t.entry_ts)
        exit_ = pd.Timestamp(t.exit_ts)
        mask = (idx >= entry) & (idx < exit_)
        open_notional.loc[mask] += t.qty * t.entry_price
    ratio = open_notional / equity
    return _f(float(ratio.mean()))


# --------------------------------------------------------------------------- #
# Benchmark regression                                                         #
# --------------------------------------------------------------------------- #
def _alpha_beta(equity: pd.Series, benchmark: pd.Series | None) -> tuple[float, float]:
    """OLS ``beta = cov(r, rb) / var(rb)`` and annualized Jensen ``alpha``.

    ``benchmark`` is a price/level series; it is reindexed onto the equity index
    and differenced to returns. Requires >= 3 overlapping return observations,
    else ``(nan, nan)``. When ``benchmark is equity`` the regression is exact:
    beta == 1, alpha == 0.
    """
    if benchmark is None:
        return math.nan, math.nan
    # Align the benchmark levels to the equity calendar, then difference both.
    r = equity.pct_change()
    rb = benchmark.reindex(equity.index).pct_change()
    pair = pd.concat([r, rb], axis=1, keys=["r", "rb"]).dropna()
    if len(pair) < 3:
        return math.nan, math.nan
    ra = pair["r"].to_numpy(dtype=float)
    rba = pair["rb"].to_numpy(dtype=float)
    cov = np.cov(ra, rba, ddof=1)  # 2x2: cov[0,1] = cov(r, rb), cov[1,1] = var(rb)
    var_rb = float(cov[1, 1])
    if var_rb <= 0:
        return math.nan, math.nan
    beta = float(cov[0, 1]) / var_rb
    # Annualized Jensen's alpha: daily excess of mean return over beta*bench.
    alpha = (float(np.mean(ra)) - beta * float(np.mean(rba))) * TRADING_DAYS
    return _f(alpha), _f(beta)


# --------------------------------------------------------------------------- #
# Table / series helpers for report consumers                                  #
# --------------------------------------------------------------------------- #
def monthly_returns(equity: pd.Series) -> pd.DataFrame:
    """Calendar-month compounded returns as a years x [Jan..Dec, YTD] table.

    Each cell is the return compounded from daily bar returns within that
    month; ``YTD`` compounds the year's realized monthly returns. Months with no
    data are NaN.
    """
    cols = _MONTHS + ["YTD"]
    if equity is None or len(equity) < 2:
        return pd.DataFrame(columns=cols)

    r = equity.pct_change().fillna(0.0)
    # Compound daily returns within each (year, month) bucket.
    grouped = r.groupby([r.index.year, r.index.month]).apply(
        lambda s: float(np.prod(1.0 + s.to_numpy(dtype=float)) - 1.0)
    )
    grouped.index = grouped.index.set_names(["year", "month"])
    table = grouped.unstack("month").reindex(columns=range(1, 13))

    # YTD = compound the (non-NaN) monthly returns across each year's row.
    def _ytd(row: pd.Series) -> float:
        vals = row.dropna().to_numpy(dtype=float)
        return float(np.prod(1.0 + vals) - 1.0) if vals.size else math.nan

    table["YTD"] = table.apply(_ytd, axis=1)
    table.columns = cols
    table.index.name = "year"
    return table


def yearly_returns(equity: pd.Series) -> pd.Series:
    """Compounded calendar-year returns, indexed by integer year."""
    if equity is None or len(equity) < 2:
        return pd.Series(dtype=float, name="yearly_return")
    r = equity.pct_change().fillna(0.0)
    yearly = r.groupby(r.index.year).apply(
        lambda s: float(np.prod(1.0 + s.to_numpy(dtype=float)) - 1.0)
    )
    yearly.index.name = "year"
    yearly.name = "yearly_return"
    return yearly


def rolling_sharpe(equity: pd.Series, window: int = 252) -> pd.Series:
    """Rolling annualized Sharpe over ``window`` bars (rf = 0), same index.

    The first ``window - 1`` values are NaN. Windows with zero volatility are
    NaN rather than ``inf``.
    """
    r = equity.pct_change()
    roll_mean = r.rolling(window).mean()
    roll_std = r.rolling(window).std(ddof=1)
    sharpe = roll_mean / roll_std * ANNUALIZATION
    # Guard flat windows (std == 0 -> inf) into NaN.
    sharpe = sharpe.replace([np.inf, -np.inf], np.nan)
    sharpe.name = "rolling_sharpe"
    return sharpe

"""Custom quant/factor signals: cross-sectional momentum and risk factors.

Five factor signals live here, all consumed by the flagship
`strategies/examples/momentum_composite.yaml` strategy (three of them —
`risk_adjusted_momentum`, `distance_from_52w_high`, `return_smoothness` —
feed its weighted-zscore score) and individually usable by any other
strategy YAML:

  - `return_over_window`     — total return from t-window to t-skip (the
                                classic "12-1" momentum construction when
                                skip > 0).
  - `realized_vol`           — annualized volatility of daily simple
                                returns.
  - `risk_adjusted_momentum` — `return_over_window` scaled by `realized_vol`
                                (a Sharpe-like momentum score).
  - `distance_from_52w_high` — how far current close sits below its
                                trailing 52-week high, in [-1, 0].
  - `return_smoothness`      — negative "information discreteness"
                                (Da, Gurun & Warachka 2014, "Frog in the
                                Pan"): rewards momentum built from many
                                small same-sign daily moves over momentum
                                built from a few large jumps.

Same PIT contract as every other tier (`docs/adding_signals.md`): a signal
fn receives one symbol's OHLCV frame (columns at least open/high/low/close/
volume, optionally `total_return_close`; index a tz-naive IST
DatetimeIndex, ascending) and keyword params, and returns a `pd.Series`
aligned to `df.index` where row t depends only on rows <= t of `df`. Every
function below is built exclusively from `.shift(+n)` (n >= 0) and
`.rolling()` windows ending at t, both causal by construction — the
look-ahead detector (`tests/strategies/test_lookahead_detector.py`)
certifies this for every one of them on every test run.

Deferred: `beta` and `residual_momentum` (regression of a symbol's returns
against a benchmark/index) are intentionally NOT implemented here. A signal
fn as invoked by `registry.compute_signal` receives only the traded
symbol's own frame — there is no channel today for a signal to also see a
second (benchmark) frame. Routing "which second frame does this signal
need" is an engine-level concern (Phase 3, the same category of deferral
`strategies/filters.py` notes for regime-filter frame routing), not this
module's; adding these two factors now would mean either silently ignoring
the benchmark or reaching outside `df`, both worse than leaving them
unregistered until the engine can supply a benchmark frame.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from tradingos.strategies.registry import register_signal


def _price_series(df: pd.DataFrame) -> pd.Series:
    """Total-return close where available, else plain close.

    `data/actions.py::total_return_close` chain-links dividends back into
    the close series; momentum ranking should prefer it where dividend data
    exists (spec 1b). Not every frame carries the column (e.g. the
    look-ahead certifier's synthetic OHLCV has none), so this falls back to
    plain `close` rather than raising.
    """
    if "total_return_close" in df.columns:
        return df["total_return_close"]
    return df["close"]


@register_signal(
    "return_over_window",
    description=(
        "Total return from t-window to t-skip: P.shift(skip) / P.shift(window) - 1, "
        "using total_return_close when available (else close). skip=0 gives a plain "
        "trailing-window return; skip>0 skips the most recent bars (e.g. 12-1 momentum "
        "uses window=252, skip=21 to exclude the last trading month)."
    ),
    tier="factor",
    window=252,
    skip=0,
)
def return_over_window(df: pd.DataFrame, window: int = 252, skip: int = 0) -> pd.Series:
    """Trailing total return from `window` bars ago to `skip` bars ago.

    P = total_return_close if present else close. Value at row t:

        P.shift(skip)[t] / P.shift(window)[t] - 1  ==  P[t-skip] / P[t-window] - 1

    Both `.shift(skip)` and `.shift(window)` look strictly BACKWARD
    (n >= 0), so row t only ever reads P at rows <= t — causal by
    construction. NaN for the first `window` rows (`P.shift(window)` is NaN
    there).

    Raises:
        ValueError: if not `window > skip >= 0` — skip must be
            non-negative and strictly less than window, else the
            "from/to" span is empty or inverted.
    """
    if not (window > skip >= 0):
        raise ValueError(
            f"return_over_window requires window > skip >= 0, got window={window}, skip={skip}"
        )
    price = _price_series(df)
    return price.shift(skip) / price.shift(window) - 1.0


@register_signal(
    "realized_vol",
    description=(
        "Annualized volatility of daily simple returns: rolling std (ddof=1) of "
        "close.pct_change() over `window` trailing bars, scaled by sqrt(252). Uses "
        "plain close (not total-return) — a price-vol factor, not a total-return factor."
    ),
    tier="factor",
    window=63,
)
def realized_vol(df: pd.DataFrame, window: int = 63) -> pd.Series:
    """Annualized realized volatility of daily simple returns.

        r = close.pct_change()
        realized_vol[t] = std(r[t-window+1 .. t], ddof=1) * sqrt(252)

    `rolling(window, min_periods=window)` ending at t is causal by
    construction (reads only rows <= t). NaN until `window` return
    observations (window + 1 close bars) are available.
    """
    r = df["close"].pct_change()
    return r.rolling(window=window, min_periods=window).std(ddof=1) * np.sqrt(252.0)


@register_signal(
    "risk_adjusted_momentum",
    description=(
        "12-1-style risk-adjusted momentum: return_over_window(window, skip) divided "
        "by realized_vol(vol_window), both evaluated as of row t. A Sharpe-like momentum "
        "score; momentum_composite's flagship params are window=252, skip=21, vol_window=63."
    ),
    tier="factor",
    window=252,
    skip=21,
    vol_window=63,
)
def risk_adjusted_momentum(
    df: pd.DataFrame, window: int = 252, skip: int = 21, vol_window: int = 63
) -> pd.Series:
    """`return_over_window(df, window, skip)` divided by `realized_vol(df, vol_window)`.

    Both components are causal (see their own docstrings), so the ratio at
    row t depends only on rows <= t of `df`. Where the volatility is NaN
    (not yet warmed up) or exactly 0.0 (a degenerate flat/constant price
    series), the result is NaN rather than +/-inf or a divide-by-zero
    warning: `.replace(0.0, nan)` swaps an exact-zero vol for NaN before
    dividing, and NaN propagates through the division either way.

    Raises:
        ValueError: propagated from `return_over_window` if not
            `window > skip >= 0`.
    """
    ret = return_over_window(df, window=window, skip=skip)
    vol = realized_vol(df, window=vol_window)
    vol_safe = vol.replace(0.0, np.nan)
    return ret / vol_safe


@register_signal(
    "distance_from_52w_high",
    description=(
        "close / rolling_max(close, window) - 1, in [-1, 0]. 0 means at the trailing "
        "high; more negative means further below it. Higher (closer to 0) scores "
        "higher momentum — the intended sign for the momentum_composite score, which "
        "weights this factor positively."
    ),
    tier="factor",
    window=252,
)
def distance_from_52w_high(df: pd.DataFrame, window: int = 252) -> pd.Series:
    """How far close sits below its trailing `window`-bar high, as a fraction.

        roll_high[t] = max(close[t-window+1 .. t])
        distance_from_52w_high[t] = close[t] / roll_high[t] - 1

    Always <= 0 since roll_high[t] >= close[t] by construction (the rolling
    max includes close[t] itself); exactly 0.0 when close[t] IS the
    trailing high. `rolling(window, min_periods=window).max()` ending at t
    reads only rows <= t — causal. NaN for the first `window` rows.
    """
    close = df["close"]
    roll_high = close.rolling(window=window, min_periods=window).max()
    return close / roll_high - 1.0


@register_signal(
    "return_smoothness",
    description=(
        "Negative information discreteness (Da-Gurun-Warachka 'frog in the pan'): "
        "rewards momentum built from many small same-sign daily moves over momentum "
        "built from a few large jumps, holding the trailing total return's sign fixed."
    ),
    tier="factor",
    window=252,
)
def return_smoothness(df: pd.DataFrame, window: int = 252) -> pd.Series:
    """Negative information discreteness over the trailing `window` daily returns.

    Let r = close.pct_change() (daily simple returns) and, for the trailing
    window of `window` returns ending at row t:

        pct_pos = fraction of those `window` days with r > 0
        pct_neg = fraction of those `window` days with r < 0
                  (r == 0 counts toward neither pct_pos nor pct_neg)
        cum_ret = product(1 + r) - 1   over the same window
                  (the window's total compounded return)
        ID      = sign(cum_ret) * (pct_neg - pct_pos)
        signal  = -ID = sign(cum_ret) * (pct_pos - pct_neg)

    `sign` is `numpy.sign` (sign(0) == 0: a window with cum_ret exactly 0
    scores exactly 0). Intuition (Da, Gurun & Warachka 2014): a stock that
    grinds up (or down) via many small consistent daily moves has low
    |ID| — information arrives continuously, so the market underreacts and
    the move continues (frog-in-the-pan). A stock that reaches the same
    total return via a few large discontinuous jumps has high |ID|.
    `-ID` is therefore high for SMOOTH trends of either sign and low for
    JUMPY trends of either sign: a smooth uptrend and a smooth downtrend
    both score higher than a jumpy path with the same total return
    (symmetric in the sign of the trend — only smoothness is rewarded).
    momentum_composite combines this with `risk_adjusted_momentum`, which
    IS sign-of-trend-sensitive, so the composite score as a whole still
    favors uptrends overall.

    Implemented as one `rolling(window, min_periods=window).apply(...,
    raw=True)` call: the window ending at row t contains only rows <= t
    (rolling windows are causal by construction), and
    `min_periods=window` means the function is only invoked once a full,
    NaN-free window of `window` return observations is available — this
    guards the single structural NaN at the very first bar, where
    `close.pct_change()` has no prior close to compare against.
    """

    def _neg_information_discreteness(x: np.ndarray) -> float:
        pct_pos = float(np.mean(x > 0))
        pct_neg = float(np.mean(x < 0))
        cum_ret = float(np.prod(1.0 + x) - 1.0)
        sign = float(np.sign(cum_ret))
        return -(sign * (pct_neg - pct_pos))

    r = df["close"].pct_change()
    return r.rolling(window=window, min_periods=window).apply(
        _neg_information_discreteness, raw=True
    )

"""Regime and eligibility filters.

Filters share the exact same point-in-time (PIT) contract as signals
(`strategies/signals/*`): a filter function receives a per-symbol OHLCV
pandas DataFrame (index: tz-naive IST DatetimeIndex, columns at least
open/high/low/close/volume) and keyword params, and returns a boolean
`pd.Series` aligned to `df.index`. Row t of the returned series may use
ONLY rows <= t of `df` — the look-ahead detector test suite
(`tests/strategies/test_lookahead_detector.py`) certifies every registered
filter exactly as it does every registered signal.

Filters are registered with `register_filter` from `strategies.registry` and
referenced by name in a strategy YAML's `filters:` list (see
`config.schemas.FilterSpec`). Unlike signals, `FilterDef` carries no
`defaults` dict of its own — give every parameter a plain Python default on
the function signature; the engine calls `fn(df, **spec.params)` directly.

A filter's `df` is not necessarily the traded symbol's own frame: a regime
filter such as `index_above_ma` is typically applied to a benchmark/index
frame (e.g. Nifty 50) so the whole book can be gated off during a broad
downtrend, while an eligibility filter such as `min_price` is applied
per-symbol. Routing "which frame does this filter see" is an engine-level
concern (Phase 3), not this module's.
"""

from __future__ import annotations

import pandas as pd

from tradingos.strategies.registry import register_filter


@register_filter(
    "index_above_ma",
    description=(
        "Regime filter: true where close is above its rolling simple moving "
        "average (default 200-day). NaN-safe: emits False (not NaN) for "
        "rows before the moving average has warmed up. Typically applied to "
        "a benchmark/index frame rather than the traded symbol."
    ),
)
def index_above_ma(df: pd.DataFrame, window: int = 200) -> pd.Series:
    """True where df['close'] at row t (using rows <= t only) is above its
    trailing `window`-bar simple moving average.

    `rolling(window, min_periods=window)` is causal by construction: the
    value at row t is a function of rows [t - window + 1, t] only.
    """
    ma = df["close"].rolling(window=window, min_periods=window).mean()
    above = df["close"] > ma
    return above.fillna(False).astype(bool)


@register_filter(
    "min_price",
    description=(
        "Eligibility filter: true where close >= threshold (e.g. penny-stock "
        "exclusion). NaN-safe: emits False for missing/NaN closes."
    ),
)
def min_price(df: pd.DataFrame, threshold: float = 0.0) -> pd.Series:
    """True where df['close'] at row t is at or above `threshold`.

    A plain elementwise comparison — trivially causal, row t depends only on
    row t of `df`.
    """
    ok = df["close"] >= threshold
    return ok.fillna(False).astype(bool)

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


@register_filter(
    "fast_ma_above_slow_ma",
    description=(
        "Trend filter: true where the fast rolling SMA of close is above the "
        "slow one (golden-cross regime, default 50/200). NaN-safe: emits "
        "False until BOTH windows have warmed up."
    ),
)
def fast_ma_above_slow_ma(df: pd.DataFrame, fast: int = 50, slow: int = 200) -> pd.Series:
    """True where SMA(fast) at row t is above SMA(slow) at row t.

    Both means use `rolling(w, min_periods=w)` — causal by construction; the
    comparison is elementwise, so row t uses rows <= t only.
    """
    close = df["close"]
    f = close.rolling(window=fast, min_periods=fast).mean()
    s = close.rolling(window=slow, min_periods=slow).mean()
    return (f > s).fillna(False).astype(bool)


@register_filter(
    "above_ma_band",
    description=(
        "Hysteresis band around a rolling SMA: turns ON when close > "
        "entry_mult * SMA, OFF when close < exit_mult * SMA, and HOLDS its "
        "previous state inside the dead zone — suppressing whipsaw from "
        "noise-level crosses. False during SMA warm-up."
    ),
)
def above_ma_band(
    df: pd.DataFrame,
    window: int = 200,
    entry_mult: float = 1.02,
    exit_mult: float = 0.98,
) -> pd.Series:
    """Stateful-but-causal band filter.

    The state at row t is a deterministic function of rows <= t only (the
    state machine consumes the series in time order and never looks ahead),
    so precomputing the full series and slicing it at `now` — what the
    engine's FilterStore does — equals recomputing on the truncated frame.
    """
    close = df["close"]
    ma = close.rolling(window=window, min_periods=window).mean()
    enter = (close > ma * entry_mult).fillna(False).tolist()
    leave = (close < ma * exit_mult).fillna(False).tolist()
    warm = ma.notna().tolist()
    state = False
    out: list[bool] = []
    for on, off, ok in zip(enter, leave, warm, strict=True):
        if not ok:
            state = False
        elif on:
            state = True
        elif off:
            state = False
        out.append(state)
    return pd.Series(out, index=df.index, dtype=bool)


@register_filter(
    "above_ma_confirm",
    description=(
        "Confirmation filter: turns ON only after `days` CONSECUTIVE closes "
        "above the rolling SMA, OFF only after `days` consecutive closes "
        "below it; holds its previous state otherwise. False during warm-up."
    ),
)
def above_ma_confirm(df: pd.DataFrame, window: int = 200, days: int = 3) -> pd.Series:
    """Stateful-but-causal N-day confirmation of an SMA cross.

    Same causality argument as `above_ma_band`: the state at row t consumes
    rows <= t in order, so the precomputed series sliced at `now` matches a
    truncated-frame recompute.
    """
    close = df["close"]
    ma = close.rolling(window=window, min_periods=window).mean()
    above = (close > ma).fillna(False).tolist()
    below = (close < ma).fillna(False).tolist()
    warm = ma.notna().tolist()
    state = False
    run_above = 0
    run_below = 0
    out: list[bool] = []
    for a, b, ok in zip(above, below, warm, strict=True):
        if not ok:
            state = False
            run_above = 0
            run_below = 0
        else:
            run_above = run_above + 1 if a else 0
            run_below = run_below + 1 if b else 0
            if not state and run_above >= days:
                state = True
            elif state and run_below >= days:
                state = False
        out.append(state)
    return pd.Series(out, index=df.index, dtype=bool)

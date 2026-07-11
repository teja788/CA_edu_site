"""Built-in indicator wrappers over `pandas_ta_classic` (tier="builtin").

This module is tier 1 of the three-tier signal registry described in
`strategies/registry.py` and `docs/adding_signals.md`: thin, PIT-safe
wrappers around the standard technical-indicator library so a strategy YAML
can reference them by name, e.g. `{name: rsi, params: {length: 14}}`.

Point-in-time (PIT) contract — identical to every other tier: a signal
function receives one symbol's OHLCV `pd.DataFrame` (tz-naive IST
`DatetimeIndex`, columns open/high/low/close/volume) and keyword params, and
returns a `pd.Series` aligned to `df.index` where the value at row t depends
ONLY on rows <= t of `df`. `tests/strategies/test_lookahead_detector.py`
certifies every signal registered here (and everywhere else) by recomputing
it on frames truncated at several probe points; a leak fails the suite
loudly, naming the offending signal. Every wrapper below was individually
checked against that certifier before being registered.

Two indicators `pandas_ta_classic` computes in a way that is NOT
point-in-time safe by default are handled explicitly rather than wrapped
blindly:

  * `dpo` (Detrended Price Oscillator) is CENTERED by default, which shifts
    the reference moving average into the future. The wrapper below always
    passes `centered=False` to the underlying call, ignoring any
    caller-supplied `centered` param, so this signal can never be
    re-enabled into leaky mode via a strategy YAML's `params:` block.
  * `ichimoku`'s chikou span (`ICS_*`, "lagging span") is `close` shifted
    BACKWARD so it can be plotted trailing the price — row t of the
    returned column literally holds the close of row t + kijun. That is a
    genuine look-ahead and is excluded entirely; only the tenkan, kijun,
    and (causal, forward-DISPLAYED-but-backward-COMPUTED) senkou spans A/B
    are registered. See `_ichimoku_component` for the mechanics.

`vwap` is anchored per calendar day by `pandas_ta_classic`. On daily bars
each anchor group contains exactly one row, so `vwap` degenerates to that
day's typical price `(high + low + close) / 3` — mathematically correct but
not very informative. It is registered anyway (harmless, PIT-safe, and
genuinely meaningful the moment it's fed minute/intraday bars) with a
description noting the caveat.

Multi-output indicators (MACD, Bollinger Bands, Stochastic, SuperTrend,
Donchian, Keltner, ADX, Ichimoku, ...) are unpacked into one registered
signal per useful column, selected by COLUMN POSITION rather than by the
column name `pandas_ta_classic` generates — those names embed the parameter
values used (e.g. `MACD_12_26_9`), so a name-based lookup would silently
break the moment a strategy YAML overrides a default length/fast/slow/etc.
Position is stable across parameter choices because `pandas_ta_classic`
always builds these frames by concatenating the same columns in the same
order regardless of the parameter values passed.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd
import pandas_ta_classic as ta

from tradingos.core.errors import ConfigError
from tradingos.strategies.registry import SignalFn, register_signal

# ---------------------------------------------------------------------------
# PIT parameter guard: every pandas_ta_classic indicator accepts an `offset`
# kwarg that shifts its OUTPUT by that many bars. A NEGATIVE offset shifts the
# indicator INTO THE FUTURE — `rsi(close, offset=-1)` is bit-identical to
# `rsi(close).shift(-1)`, i.e. row t holds tomorrow's value: a genuine
# look-ahead leak a strategy YAML could otherwise enable via `params:`. The
# look-ahead certifier probes registered signals, but a YAML-supplied param is
# only exercised at run time, so the block must live here, at the one choke
# point every builtin wrapper passes through. Positive offsets only LAG the
# series (value at t comes from t-offset) and stay allowed.
# ---------------------------------------------------------------------------


def _guard_pit_params(params: dict[str, Any]) -> None:
    """Reject params that would shift a builtin indicator into the future.

    Raises :class:`ConfigError` (loudly, naming the offending param) for any
    ``offset`` that is not a non-negative real number. Other future-shifting
    knobs are neutralized in their specific wrappers: `dpo` force-disables
    `centered`, and `ichimoku` never forwards `include_chikou` (the lagging
    span is excluded outright).
    """
    if "offset" not in params:
        return
    offset = params["offset"]
    ok = isinstance(offset, (int, float)) and not isinstance(offset, bool) and offset >= 0
    if not ok:
        raise ConfigError(
            f"LOOK-AHEAD BLOCKED: builtin indicator param offset={offset!r} is rejected. "
            "A negative offset shifts the indicator into the future (row t would hold the "
            "value computed at row t+|offset|), violating the point-in-time contract "
            "(row t may use only rows <= t). Builtin signals accept only offset >= 0."
        )

# ---------------------------------------------------------------------------
# Input extractors: pull the positional Series arguments a given
# pandas_ta_classic function expects, in the order it expects them.
# ---------------------------------------------------------------------------

InputsFn = Callable[[pd.DataFrame], tuple[pd.Series, ...]]


def _close(df: pd.DataFrame) -> tuple[pd.Series, ...]:
    return (df["close"],)


def _close_volume(df: pd.DataFrame) -> tuple[pd.Series, ...]:
    return (df["close"], df["volume"])


def _high_low(df: pd.DataFrame) -> tuple[pd.Series, ...]:
    return (df["high"], df["low"])


def _high_low_close(df: pd.DataFrame) -> tuple[pd.Series, ...]:
    return (df["high"], df["low"], df["close"])


def _high_low_close_volume(df: pd.DataFrame) -> tuple[pd.Series, ...]:
    return (df["high"], df["low"], df["close"], df["volume"])


def _open_high_low_close(df: pd.DataFrame) -> tuple[pd.Series, ...]:
    return (df["open"], df["high"], df["low"], df["close"])


# ---------------------------------------------------------------------------
# Factory: turn a pandas_ta_classic function into a registry-shaped
# fn(df, **params) -> pd.Series. This is the one place that absorbs the
# boilerplate (None-handling, column selection, length/index parity) so each
# registration below is a single explicit, readable statement.
# ---------------------------------------------------------------------------


def _wrap(ta_fn: Callable[..., Any], inputs: InputsFn, column: int | None = None) -> SignalFn:
    """Build a `fn(df, **params) -> pd.Series` around a pandas_ta_classic call.

    Args:
        ta_fn: the pandas_ta_classic function to call, e.g. `ta.rsi`.
        inputs: extracts the positional price/volume Series `ta_fn` expects
            from `df`, in order (e.g. `_high_low_close` for `ta.atr`).
        column: for indicators that return a multi-column `DataFrame`
            (MACD, Bollinger Bands, ...), the 0-based position of the
            column this particular registered signal exposes. `None` for
            indicators that already return a single `pd.Series`.
    """

    def _fn(df: pd.DataFrame, **params: Any) -> pd.Series:
        _guard_pit_params(params)
        result = ta_fn(*inputs(df), **params)
        if result is None:
            # pandas_ta_classic returns None (rather than raising) when it
            # can't compute at all, e.g. a requested window exceeds the
            # available history. Degrade to an all-NaN series of the right
            # length rather than let compute_signal's length check crash.
            return pd.Series(np.nan, index=df.index, dtype="float64")
        series = result.iloc[:, column] if column is not None else result
        # Defensive: pandas_ta_classic always preserves df's index/length in
        # practice, but re-aligning is cheap and guarantees the length
        # parity compute_signal() requires even if that ever changes.
        return series.reindex(df.index)

    return _fn


def _ichimoku_component(column: int, description: str) -> None:
    """Register one causal Ichimoku line (tenkan, kijun, or a senkou span).

    `ta.ichimoku(..., include_chikou=False)` returns a tuple; index 0 is a
    DataFrame aligned to `df.index` with columns, in stable position order,
    [senkou_a, senkou_b, tenkan, kijun] (`include_chikou=False` drops the
    non-causal lagging span before it ever reaches this wrapper — see the
    module docstring). Index 1 of the tuple is a short future-cloud
    "extension" frame that extends past `df.index` entirely; it is never
    touched here.

    Senkou spans A/B are DISPLAYED shifted forward (that's the whole point
    of a "leading span"), but pandas_ta_classic returns them already shifted
    forward, which means the value written at row t was computed from data
    at row t - kijun — strictly backward-looking, hence causal. This was
    confirmed against the look-ahead certifier before registering.
    """

    def _fn(df: pd.DataFrame, **params: Any) -> pd.Series:
        _guard_pit_params(params)
        # `include_chikou` is never forwarded: the chikou span is close shifted
        # BACKWARD — a genuine look-ahead — and must stay excluded no matter
        # what a strategy YAML passes.
        params.pop("include_chikou", None)
        ichimoku_df, _future_cloud = ta.ichimoku(
            df["high"], df["low"], df["close"], include_chikou=False, **params
        )
        if ichimoku_df is None:
            return pd.Series(np.nan, index=df.index, dtype="float64")
        return ichimoku_df.iloc[:, column].reindex(df.index)

    name = ["ichimoku_senkou_a", "ichimoku_senkou_b", "ichimoku_tenkan", "ichimoku_kijun"][column]
    register_signal(name, description=description, tier="builtin", tenkan=9, kijun=26, senkou=52)(
        _fn
    )


def _dpo(df: pd.DataFrame, **params: Any) -> pd.Series:
    """Detrended Price Oscillator, forced non-centered.

    `ta.dpo` defaults to `centered=True`, which shifts its reference moving
    average into the future (a genuine look-ahead — confirmed against the
    certifier). `centered` is popped from `params` and never forwarded, so
    a strategy YAML cannot re-enable the leaky mode by passing
    `centered: true`.
    """
    _guard_pit_params(params)
    params.pop("centered", None)
    length = params.pop("length", 20)
    result = ta.dpo(df["close"], length=length, centered=False, **params)
    if result is None:
        return pd.Series(np.nan, index=df.index, dtype="float64")
    return result.reindex(df.index)


def _psar_line(df: pd.DataFrame, **params: Any) -> pd.Series:
    """Parabolic SAR, unified into one line (long-stop where in an uptrend,
    short-stop where in a downtrend — pandas_ta_classic reports these as two
    mutually-exclusive columns; combining them pointwise stays causal since
    each input column already is)."""
    _guard_pit_params(params)
    result = ta.psar(df["high"], df["low"], df["close"], **params)
    if result is None:
        return pd.Series(np.nan, index=df.index, dtype="float64")
    long_stop, short_stop = result.iloc[:, 0], result.iloc[:, 1]
    return long_stop.fillna(short_stop).reindex(df.index)


def _psar_direction(df: pd.DataFrame, **params: Any) -> pd.Series:
    """Parabolic SAR trend direction: +1 while the long stop is active
    (uptrend), -1 while the short stop is active (downtrend), NaN before
    warmup. Derived from the same two mutually-exclusive columns as
    `psar`."""
    _guard_pit_params(params)
    result = ta.psar(df["high"], df["low"], df["close"], **params)
    if result is None:
        return pd.Series(np.nan, index=df.index, dtype="float64")
    long_stop, short_stop = result.iloc[:, 0], result.iloc[:, 1]
    direction = pd.Series(np.nan, index=result.index, dtype="float64")
    direction[long_stop.notna()] = 1.0
    direction[short_stop.notna()] = -1.0
    return direction.reindex(df.index)


# ---------------------------------------------------------------------------
# Moving averages
# ---------------------------------------------------------------------------

register_signal(
    "sma", description="Simple moving average of close.", tier="builtin", length=20
)(_wrap(ta.sma, _close))

register_signal(
    "ema", description="Exponential moving average of close.", tier="builtin", length=20
)(_wrap(ta.ema, _close))

register_signal(
    "wma",
    description="Linearly weighted moving average of close (more weight on recent bars).",
    tier="builtin",
    length=20,
)(_wrap(ta.wma, _close))

register_signal(
    "hma",
    description="Hull moving average of close: a weighted-MA construction that reduces lag "
    "relative to a plain SMA/EMA of the same length.",
    tier="builtin",
    length=20,
)(_wrap(ta.hma, _close))

register_signal(
    "dema",
    description="Double exponential moving average of close (reduced-lag EMA variant).",
    tier="builtin",
    length=20,
)(_wrap(ta.dema, _close))

register_signal(
    "tema",
    description="Triple exponential moving average of close (further-reduced-lag EMA variant).",
    tier="builtin",
    length=20,
)(_wrap(ta.tema, _close))

register_signal(
    "vwma",
    description="Volume-weighted moving average of close over the trailing window.",
    tier="builtin",
    length=20,
)(_wrap(ta.vwma, _close_volume))

# ---------------------------------------------------------------------------
# Momentum
# ---------------------------------------------------------------------------

register_signal(
    "rsi",
    description="Relative Strength Index (Wilder smoothing). Bounded [0, 100]; "
    "conventionally >70 overbought, <30 oversold once warmed up.",
    tier="builtin",
    length=14,
)(_wrap(ta.rsi, _close))

register_signal(
    "roc",
    description="Rate of Change: percent change of close over the trailing window.",
    tier="builtin",
    length=10,
)(_wrap(ta.roc, _close))

register_signal(
    "cci",
    description="Commodity Channel Index: deviation of typical price from its moving average, "
    "scaled by mean absolute deviation.",
    tier="builtin",
    length=14,
)(_wrap(ta.cci, _high_low_close))

register_signal(
    "mfi",
    description="Money Flow Index: volume-weighted RSI. Bounded [0, 100].",
    tier="builtin",
    length=14,
)(_wrap(ta.mfi, _high_low_close_volume))

register_signal(
    "willr",
    description="Williams %R: close's position within the trailing high/low range, "
    "bounded [-100, 0].",
    tier="builtin",
    length=14,
)(_wrap(ta.willr, _high_low_close))

register_signal(
    "cmo",
    description="Chande Momentum Oscillator: (sum of gains - sum of losses) / "
    "(sum of gains + sum of losses) over the window, bounded [-100, 100].",
    tier="builtin",
    length=14,
)(_wrap(ta.cmo, _close))

register_signal(
    "ao",
    description="Awesome Oscillator: difference between fast and slow simple moving averages "
    "of the midpoint price (high+low)/2.",
    tier="builtin",
    fast=5,
    slow=34,
)(_wrap(ta.ao, _high_low))

register_signal(
    "apo",
    description="Absolute Price Oscillator: fast EMA minus slow EMA of close, in price units.",
    tier="builtin",
    fast=12,
    slow=26,
)(_wrap(ta.apo, _close))

register_signal(
    "uo",
    description="Ultimate Oscillator: weighted blend of buying pressure over three window "
    "lengths, bounded [0, 100].",
    tier="builtin",
    fast=7,
    medium=14,
    slow=28,
)(_wrap(ta.uo, _high_low_close))

register_signal(
    "bop",
    description="Balance of Power: (close - open) / (high - low), bounded [-1, 1].",
    tier="builtin",
)(_wrap(ta.bop, _open_high_low_close))

register_signal(
    "dpo",
    description="Detrended Price Oscillator (non-centered): close minus a trailing SMA offset "
    "back by length // 2 + 1 bars, isolating short-term cycles from the trend. Always computed "
    "with centered=False regardless of params — the centered variant looks into the future and "
    "is not point-in-time safe.",
    tier="builtin",
    length=20,
)(_dpo)

# --- multi-output momentum indicators ---

register_signal(
    "macd",
    description="MACD line: fast EMA minus slow EMA of close.",
    tier="builtin",
    fast=12,
    slow=26,
    signal=9,
)(_wrap(ta.macd, _close, column=0))

register_signal(
    "macd_hist",
    description="MACD histogram: MACD line minus its signal line.",
    tier="builtin",
    fast=12,
    slow=26,
    signal=9,
)(_wrap(ta.macd, _close, column=1))

register_signal(
    "macd_signal",
    description="MACD signal line: EMA of the MACD line.",
    tier="builtin",
    fast=12,
    slow=26,
    signal=9,
)(_wrap(ta.macd, _close, column=2))

register_signal(
    "ppo",
    description="Percentage Price Oscillator line: MACD expressed as a percent of the slow EMA "
    "(scale-free across symbols, unlike MACD).",
    tier="builtin",
    fast=12,
    slow=26,
    signal=9,
)(_wrap(ta.ppo, _close, column=0))

register_signal(
    "ppo_hist",
    description="PPO histogram: PPO line minus its signal line.",
    tier="builtin",
    fast=12,
    slow=26,
    signal=9,
)(_wrap(ta.ppo, _close, column=1))

register_signal(
    "ppo_signal",
    description="PPO signal line: EMA of the PPO line.",
    tier="builtin",
    fast=12,
    slow=26,
    signal=9,
)(_wrap(ta.ppo, _close, column=2))

register_signal(
    "trix",
    description="TRIX: rate of change of a triple-smoothed EMA of close; a momentum oscillator "
    "with built-in noise filtering.",
    tier="builtin",
    length=30,
    signal=9,
)(_wrap(ta.trix, _close, column=0))

register_signal(
    "trix_signal",
    description="Signal line (moving average) of TRIX.",
    tier="builtin",
    length=30,
    signal=9,
)(_wrap(ta.trix, _close, column=1))

register_signal(
    "stoch_k",
    description="Stochastic Oscillator %K: close's position within the trailing high/low "
    "range, smoothed. Bounded [0, 100].",
    tier="builtin",
    k=14,
    d=3,
    smooth_k=3,
)(_wrap(ta.stoch, _high_low_close, column=0))

register_signal(
    "stoch_d",
    description="Stochastic Oscillator %D: moving average of %K. Bounded [0, 100].",
    tier="builtin",
    k=14,
    d=3,
    smooth_k=3,
)(_wrap(ta.stoch, _high_low_close, column=1))

register_signal(
    "stochrsi_k",
    description="Stochastic RSI %K: Stochastic Oscillator applied to RSI instead of price. "
    "Bounded [0, 100].",
    tier="builtin",
    length=14,
    rsi_length=14,
    k=3,
    d=3,
)(_wrap(ta.stochrsi, _close, column=0))

register_signal(
    "stochrsi_d",
    description="Stochastic RSI %D: moving average of Stochastic RSI %K. Bounded [0, 100].",
    tier="builtin",
    length=14,
    rsi_length=14,
    k=3,
    d=3,
)(_wrap(ta.stochrsi, _close, column=1))

# ---------------------------------------------------------------------------
# Trend
# ---------------------------------------------------------------------------

register_signal(
    "adx",
    description="Average Directional Index: trend strength (not direction), bounded [0, 100]; "
    "conventionally >25 signals a trending market.",
    tier="builtin",
    length=14,
)(_wrap(ta.adx, _high_low_close, column=0))

register_signal(
    "adx_plus_di",
    description="+DI: smoothed positive directional movement, the ADX system's bullish "
    "pressure component.",
    tier="builtin",
    length=14,
)(_wrap(ta.adx, _high_low_close, column=1))

register_signal(
    "adx_minus_di",
    description="-DI: smoothed negative directional movement, the ADX system's bearish "
    "pressure component.",
    tier="builtin",
    length=14,
)(_wrap(ta.adx, _high_low_close, column=2))

register_signal(
    "aroon_down",
    description="Aroon Down: bars since the trailing low, scaled to [0, 100] "
    "(100 = the low was just made).",
    tier="builtin",
    length=14,
)(_wrap(ta.aroon, _high_low, column=0))

register_signal(
    "aroon_up",
    description="Aroon Up: bars since the trailing high, scaled to [0, 100] "
    "(100 = the high was just made).",
    tier="builtin",
    length=14,
)(_wrap(ta.aroon, _high_low, column=1))

register_signal(
    "aroon_osc",
    description="Aroon Oscillator: Aroon Up minus Aroon Down, bounded [-100, 100].",
    tier="builtin",
    length=14,
)(_wrap(ta.aroon, _high_low, column=2))

register_signal(
    "supertrend",
    description="SuperTrend line: ATR-banded trend-following stop/reversal level.",
    tier="builtin",
    length=7,
    multiplier=3.0,
)(_wrap(ta.supertrend, _high_low_close, column=0))

register_signal(
    "supertrend_direction",
    description="SuperTrend direction: +1 while price trends above the SuperTrend line, "
    "-1 while below.",
    tier="builtin",
    length=7,
    multiplier=3.0,
)(_wrap(ta.supertrend, _high_low_close, column=1))

register_signal(
    "psar",
    description="Parabolic SAR: trailing stop/reversal level, unified from pandas_ta_classic's "
    "separate long-stop/short-stop columns (see module docstring).",
    tier="builtin",
    af0=0.02,
    af=0.02,
    max_af=0.2,
)(_psar_line)

register_signal(
    "psar_direction",
    description="Parabolic SAR trend direction: +1 in an uptrend (long stop active), "
    "-1 in a downtrend (short stop active).",
    tier="builtin",
    af0=0.02,
    af=0.02,
    max_af=0.2,
)(_psar_direction)

_ichimoku_component(
    2,
    "Ichimoku Tenkan-sen (conversion line): midpoint of the trailing tenkan-period high/low.",
)
_ichimoku_component(
    3,
    "Ichimoku Kijun-sen (base line): midpoint of the trailing kijun-period high/low.",
)
_ichimoku_component(
    0,
    "Ichimoku Senkou Span A (leading span A): midpoint of tenkan and kijun, as returned by "
    "pandas_ta_classic already shifted forward by kijun bars (i.e. the value at row t was "
    "computed from data at row t - kijun) — causal despite conventionally being PLOTTED ahead "
    "of price. The chikou (lagging) span is excluded: it is close shifted backward and is a "
    "genuine look-ahead (see module docstring).",
)
_ichimoku_component(
    1,
    "Ichimoku Senkou Span B (leading span B): midpoint of the trailing senkou-period high/low, "
    "as returned by pandas_ta_classic already shifted forward by kijun bars — causal for the "
    "same reason as Senkou Span A.",
)

# ---------------------------------------------------------------------------
# Volatility
# ---------------------------------------------------------------------------

register_signal(
    "atr", description="Average True Range (Wilder smoothing): absolute volatility in price "
    "units.",
    tier="builtin",
    length=14,
)(_wrap(ta.atr, _high_low_close))

register_signal(
    "natr",
    description="Normalized Average True Range: ATR expressed as a percent of close, "
    "comparable across symbols at different price levels.",
    tier="builtin",
    length=14,
)(_wrap(ta.natr, _high_low_close))

register_signal(
    "massi",
    description="Mass Index: ratio of an EMA of the high-low range to a double EMA of the same "
    "range, used to flag potential trend reversals via range widening.",
    tier="builtin",
    fast=9,
    slow=25,
)(_wrap(ta.massi, _high_low))

# --- multi-output volatility indicators ---

register_signal(
    "bb_lower",
    description="Bollinger Band lower band: SMA of close minus `std` standard deviations.",
    tier="builtin",
    length=20,
    std=2.0,
)(_wrap(ta.bbands, _close, column=0))

register_signal(
    "bb_middle",
    description="Bollinger Band middle band: SMA of close.",
    tier="builtin",
    length=20,
    std=2.0,
)(_wrap(ta.bbands, _close, column=1))

register_signal(
    "bb_upper",
    description="Bollinger Band upper band: SMA of close plus `std` standard deviations.",
    tier="builtin",
    length=20,
    std=2.0,
)(_wrap(ta.bbands, _close, column=2))

register_signal(
    "bb_bandwidth",
    description="Bollinger Bandwidth: (upper - lower) / middle, a normalized volatility "
    "measure.",
    tier="builtin",
    length=20,
    std=2.0,
)(_wrap(ta.bbands, _close, column=3))

register_signal(
    "bb_percent",
    description="Bollinger %B: close's position within the bands, 0 = lower band, "
    "1 = upper band.",
    tier="builtin",
    length=20,
    std=2.0,
)(_wrap(ta.bbands, _close, column=4))

register_signal(
    "donchian_lower",
    description="Donchian Channel lower band: trailing low over `lower_length` bars.",
    tier="builtin",
    lower_length=20,
    upper_length=20,
)(_wrap(ta.donchian, _high_low, column=0))

register_signal(
    "donchian_middle",
    description="Donchian Channel middle: midpoint of the upper and lower bands.",
    tier="builtin",
    lower_length=20,
    upper_length=20,
)(_wrap(ta.donchian, _high_low, column=1))

register_signal(
    "donchian_upper",
    description="Donchian Channel upper band: trailing high over `upper_length` bars.",
    tier="builtin",
    lower_length=20,
    upper_length=20,
)(_wrap(ta.donchian, _high_low, column=2))

register_signal(
    "keltner_lower",
    description="Keltner Channel lower band: EMA of close minus `scalar` ATRs.",
    tier="builtin",
    length=20,
    scalar=2.0,
)(_wrap(ta.kc, _high_low_close, column=0))

register_signal(
    "keltner_middle",
    description="Keltner Channel middle: EMA of close.",
    tier="builtin",
    length=20,
    scalar=2.0,
)(_wrap(ta.kc, _high_low_close, column=1))

register_signal(
    "keltner_upper",
    description="Keltner Channel upper band: EMA of close plus `scalar` ATRs.",
    tier="builtin",
    length=20,
    scalar=2.0,
)(_wrap(ta.kc, _high_low_close, column=2))

# ---------------------------------------------------------------------------
# Volume
# ---------------------------------------------------------------------------

register_signal(
    "obv",
    description="On-Balance Volume: running total of volume signed by the direction of the "
    "close-to-close move.",
    tier="builtin",
)(_wrap(ta.obv, _close_volume))

register_signal(
    "vwap",
    description="Volume Weighted Average Price, anchored per calendar day. On daily bars each "
    "anchor group is a single row, so this degenerates to that day's typical price "
    "(high+low+close)/3 — still PIT-safe, but only genuinely meaningful as an intraday VWAP "
    "when fed minute/sub-daily bars.",
    tier="builtin",
)(_wrap(ta.vwap, _high_low_close_volume))

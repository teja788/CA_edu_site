"""Look-ahead prevention as a framework guarantee.

Strategy code NEVER touches raw frames during simulation — it receives a
`DataView` bound to the current simulation time and can only see bars whose
timestamp is <= now AND whose bar is complete:

  * daily bar dated D is visible once now >= D 15:30 (session close), or any
    later date;
  * minute bar stamped T (bar-open convention, as Kite returns) covers
    [T, T+1min) and is visible once now >= T + 1 minute.

Signals are precomputed over full history for speed (each registered signal is
itself certified point-in-time by the look-ahead detector test), then sliced
through this same guard, so precomputation cannot leak the future.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from tradingos.core.errors import DataError, LookAheadError
from tradingos.core.models import Timeframe
from tradingos.core.timeutils import MARKET_CLOSE
from tradingos.strategies.registry import compute_filter, compute_signal, signal_cache_key


class MarketData:
    """Immutable container: per-symbol OHLCV frames for one timeframe.

    Frames: pandas DataFrame indexed by tz-naive IST DatetimeIndex (ascending,
    unique), columns at least open/high/low/close/volume.
    """

    def __init__(
        self,
        frames: dict[str, pd.DataFrame],
        timeframe: Timeframe = Timeframe.DAY,
        snapshot_id: str = "adhoc",
    ) -> None:
        self.timeframe = timeframe
        self.snapshot_id = snapshot_id
        self._frames: dict[str, pd.DataFrame] = {}
        for sym, df in frames.items():
            if not isinstance(df.index, pd.DatetimeIndex):
                raise DataError(f"{sym}: frame index must be a DatetimeIndex")
            if not df.index.is_monotonic_increasing:
                raise DataError(f"{sym}: frame index must be sorted ascending")
            if df.index.has_duplicates:
                raise DataError(f"{sym}: duplicate timestamps in frame")
            # Own the frame instead of retaining a caller-controlled reference.
            # pandas 3 copy-on-write makes shallow copies returned by
            # ``full_frame`` cheap while isolating subsequent mutations.
            self._frames[sym] = df.copy(deep=True)

    @property
    def symbols(self) -> list[str]:
        return sorted(self._frames)

    def full_frame(self, symbol: str) -> pd.DataFrame:
        """Full history — for engine internals and precomputation ONLY.
        Strategy code must go through DataView."""
        if symbol not in self._frames:
            raise DataError(f"no data for symbol {symbol}")
        return self._frames[symbol].copy(deep=False)

    def union_index(self) -> pd.DatetimeIndex:
        if not self._frames:
            return pd.DatetimeIndex([])
        # One concatenate/deduplicate/sort pass avoids repeated union copies as
        # the symbol count grows.
        values = pd.concat(
            [pd.Series(df.index, copy=False) for df in self._frames.values()],
            ignore_index=True,
        ).unique()
        return pd.DatetimeIndex(values).sort_values()


def _join_benchmark_close(symbol_df: pd.DataFrame, bench_df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``symbol_df`` with a causal ``benchmark_close`` column.

    The benchmark's close is aligned onto the symbol frame's own index by exact
    timestamp (``reindex``): row t carries the benchmark bar stamped exactly t,
    or NaN where the benchmark has no bar there. Exact alignment can only ever
    read the benchmark's bar at ts == t (never a later one), so the join is
    causal — altering benchmark bars at ts > t cannot change ``benchmark_close``
    at row t. The original frames are never mutated (``assign`` copies)."""
    return symbol_df.assign(benchmark_close=bench_df["close"].reindex(symbol_df.index))


class SignalStore:
    """Per-run cache of precomputed signal series (symbol x signal-instance).

    Computed once per (symbol, signal name, params, benchmark, data snapshot) —
    parameter grids that share signals never recompute them.
    """

    def __init__(self, data: MarketData) -> None:
        self._data = data
        self._cache: dict[str, pd.Series] = {}

    def series(
        self,
        symbol: str,
        name: str,
        params: dict[str, Any],
        benchmark: str | None = None,
    ) -> pd.Series:
        key = signal_cache_key(symbol, name, params, self._data.snapshot_id, benchmark)
        if key not in self._cache:
            df = self._data.full_frame(symbol)
            if benchmark is not None:
                # Route the benchmark's close onto the symbol frame (causally)
                # BEFORE the signal fn sees it — the same second-frame path the
                # `symbol`-routed regime filters use, but for signals.
                df = _join_benchmark_close(df, self._data.full_frame(benchmark))
            self._cache[key] = compute_signal(name, df, params)
        return self._cache[key]


class FilterStore:
    """Per-run cache of precomputed filter series (symbol x filter-instance).

    Mirrors :class:`SignalStore`. Filters share signals' causality contract —
    row *t* uses only rows <= *t*, certified per registered filter by the
    look-ahead detector suite — so computing the full-history series once and
    slicing it through the DataView visibility guard is equivalent to
    recomputing the filter on the truncated frame at every rebalance (which
    was quadratic in run length).
    """

    def __init__(self, data: MarketData) -> None:
        self._data = data
        self._cache: dict[str, pd.Series] = {}

    def series(self, symbol: str, name: str, params: dict[str, Any]) -> pd.Series:
        key = signal_cache_key(symbol, f"filter:{name}", params, self._data.snapshot_id)
        if key not in self._cache:
            df = self._data.full_frame(symbol)
            if df.empty:
                # A filter fn is never invoked on an empty frame (the uncached
                # path never called it when no bars were visible); an empty
                # series makes every downstream `_latest_bool` read False.
                self._cache[key] = pd.Series(dtype=bool)
            else:
                self._cache[key] = compute_filter(name, df, params)
        return self._cache[key]


def bar_completion_time(bar_ts: pd.Timestamp, timeframe: Timeframe) -> pd.Timestamp:
    """Wall-clock time at which the bar stamped bar_ts is fully known."""
    if timeframe == Timeframe.DAY:
        return bar_ts.normalize() + pd.Timedelta(
            hours=MARKET_CLOSE.hour, minutes=MARKET_CLOSE.minute
        )
    return bar_ts + pd.Timedelta(minutes=1)


class DataView:
    """A window over MarketData limited to bars completed at or before `now`.

    This object is the ONLY data access strategies get inside a simulation.
    """

    def __init__(
        self,
        data: MarketData,
        signals: SignalStore,
        now: datetime,
        aux: dict[Timeframe, MarketData] | None = None,
    ) -> None:
        self._data = data
        self._signals = signals
        self._filters = FilterStore(data)
        self._now = pd.Timestamp(now)
        self._aux = aux or {}
        self._aux_signals = {tf: SignalStore(md) for tf, md in self._aux.items()}

    @property
    def now(self) -> pd.Timestamp:
        return self._now

    @property
    def symbols(self) -> list[str]:
        return self._data.symbols

    def _visible_cutoff(self, timeframe: Timeframe) -> pd.Timestamp:
        """Latest bar timestamp fully visible at self._now for a timeframe."""
        if timeframe == Timeframe.DAY:
            close_today = self._now.normalize() + pd.Timedelta(
                hours=MARKET_CLOSE.hour, minutes=MARKET_CLOSE.minute
            )
            if self._now >= close_today:
                return self._now.normalize()
            return self._now.normalize() - timedelta(days=1)
        return self._now - pd.Timedelta(minutes=1)

    def _sliced(self, symbol: str, timeframe: Timeframe | None = None) -> pd.DataFrame:
        tf = timeframe or self._data.timeframe
        md = self._data if tf == self._data.timeframe else self._aux.get(tf)
        if md is None:
            raise DataError(f"no {tf.value} data attached to this run")
        df = md.full_frame(symbol)
        return df.loc[: self._visible_cutoff(tf)]

    def history(
        self, symbol: str, n: int | None = None, timeframe: Timeframe | None = None
    ) -> pd.DataFrame:
        """OHLCV bars visible at `now` (optionally last n)."""
        df = self._sliced(symbol, timeframe)
        return df.tail(n) if n is not None else df

    def close(self, symbol: str) -> float | None:
        df = self._sliced(symbol)
        if df.empty:
            return None
        return float(df["close"].iloc[-1])

    def last_bar(self, symbol: str) -> pd.Series | None:
        df = self._sliced(symbol)
        if df.empty:
            return None
        return df.iloc[-1]

    def signal(
        self,
        symbol: str,
        name: str,
        params: dict[str, Any] | None = None,
        timeframe: Timeframe | None = None,
        benchmark: str | None = None,
    ) -> float | None:
        """Latest visible value of a registered signal for a symbol."""
        s = self.signal_series(symbol, name, params, timeframe, benchmark)
        s = s.dropna()
        if s.empty:
            return None
        return float(s.iloc[-1])

    def signal_series(
        self,
        symbol: str,
        name: str,
        params: dict[str, Any] | None = None,
        timeframe: Timeframe | None = None,
        benchmark: str | None = None,
    ) -> pd.Series:
        """Visible slice of a precomputed signal series.

        ``benchmark`` routes a second symbol's close onto the symbol frame as a
        ``benchmark_close`` column (see :func:`_join_benchmark_close`) before
        the signal is computed — for signals such as ``residual_momentum`` that
        regress the stock against an index. The benchmark frame is read from the
        same ``MarketData`` (and timeframe) as the traded symbol."""
        tf = timeframe or self._data.timeframe
        if tf == self._data.timeframe:
            store = self._signals
        elif tf in self._aux_signals:
            store = self._aux_signals[tf]
        else:
            raise DataError(f"no {tf.value} data attached to this run")
        series = store.series(symbol, name, params or {}, benchmark)
        return series.loc[: self._visible_cutoff(tf)]

    def filter_series(
        self, symbol: str, name: str, params: dict[str, Any] | None = None
    ) -> pd.Series:
        """Visible slice of a precomputed (cached once per run) filter series.

        Filters are causal exactly like signals, so the full-history series is
        computed once per (symbol, filter, params) and read through the same
        visibility guard — its last value at or before ``now`` equals the last
        value of the filter recomputed on the truncated frame. Filters are
        evaluated on the run's base timeframe only."""
        series = self._filters.series(symbol, name, params or {})
        return series.loc[: self._visible_cutoff(self._data.timeframe)]

    def assert_visible(self, ts: datetime, timeframe: Timeframe | None = None) -> None:
        """Raise LookAheadError if a bar stamped ts is not yet visible at now."""
        tf = timeframe or self._data.timeframe
        if pd.Timestamp(ts) > self._visible_cutoff(tf):
            raise LookAheadError(
                f"bar {ts} ({tf.value}) not visible at simulation time {self._now}"
            )

    def at(self, now: datetime) -> DataView:
        """A new view at a different time — engine use only (advancing the clock)."""
        view = DataView.__new__(DataView)
        view._data = self._data
        view._signals = self._signals
        view._filters = self._filters  # shared: filter cache is per run
        view._now = pd.Timestamp(now)
        view._aux = self._aux
        view._aux_signals = self._aux_signals
        return view

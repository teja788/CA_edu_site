"""Tests for engine/dataview.py — the look-ahead guard (THE safety boundary).

Covers: daily/minute visibility cutoffs, cross-timeframe aux access and the
missing-timeframe error, empty-history edge cases, clock advancement via
`.at()`, and SignalStore caching.
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest
from fixtures.synthetic import synthetic_daily, synthetic_minute

from tradingos.core.errors import DataError, LookAheadError
from tradingos.core.models import Timeframe
from tradingos.engine.dataview import DataView, MarketData, SignalStore
from tradingos.strategies.registry import register_signal


@register_signal("test_engine_counting_signal_probe", tier="custom", window=5)
def _probe_signal(df: pd.DataFrame, **params: object) -> pd.Series:
    """A small causal signal reused by the cross-timeframe tests below."""
    window = params["window"]
    return df["close"].rolling(window=window, min_periods=window).mean()


@pytest.fixture()
def daily_frame() -> pd.DataFrame:
    return synthetic_daily("DV_DAILY", start=date(2024, 1, 1), end=date(2024, 3, 31), seed=1)


@pytest.fixture()
def minute_frame() -> pd.DataFrame:
    return synthetic_minute("DV_MINUTE", day=date(2024, 1, 15), seed=1)


def test_union_index_is_sorted_unique_across_overlapping_frames() -> None:
    first = pd.DataFrame(
        {"close": [1.0, 2.0]}, index=pd.to_datetime(["2024-01-01", "2024-01-03"])
    )
    second = pd.DataFrame(
        {"close": [3.0, 4.0]}, index=pd.to_datetime(["2024-01-02", "2024-01-03"])
    )

    result = MarketData({"A": first, "B": second}).union_index()

    assert result.equals(pd.date_range("2024-01-01", periods=3, freq="D"))


# ---------------------------------------------------------------------------
# daily visibility
# ---------------------------------------------------------------------------


def test_daily_visibility_before_close_shows_yesterdays_bar(daily_frame: pd.DataFrame) -> None:
    mid = len(daily_frame.index) // 2
    d = daily_frame.index[mid]
    data = MarketData({"D": daily_frame}, timeframe=Timeframe.DAY, snapshot_id="daily-before")
    dv = DataView(data, SignalStore(data), d + timedelta(hours=9))  # 09:00, before 15:30 close

    last_visible = dv.last_bar("D")
    assert last_visible is not None
    # the bar dated d itself must not be visible yet
    assert last_visible.name < d
    assert dv.close("D") == pytest.approx(daily_frame.loc[last_visible.name, "close"])


def test_daily_visibility_at_and_after_close_shows_todays_bar(daily_frame: pd.DataFrame) -> None:
    mid = len(daily_frame.index) // 2
    d = daily_frame.index[mid]

    data = MarketData({"D": daily_frame}, timeframe=Timeframe.DAY, snapshot_id="daily-at-close")
    dv_at_close = DataView(data, SignalStore(data), d + timedelta(hours=15, minutes=30))
    dv_after_close = DataView(data, SignalStore(data), d + timedelta(hours=16))

    for dv in (dv_at_close, dv_after_close):
        last_visible = dv.last_bar("D")
        assert last_visible is not None
        assert last_visible.name == d
        assert dv.close("D") == pytest.approx(daily_frame.loc[d, "close"])


# ---------------------------------------------------------------------------
# minute visibility
# ---------------------------------------------------------------------------


def test_minute_bar_visible_only_from_open_plus_one_minute(minute_frame: pd.DataFrame) -> None:
    mid = len(minute_frame.index) // 2
    t = minute_frame.index[mid]  # bar-open stamp

    data = MarketData(
        {"M": minute_frame}, timeframe=Timeframe.MINUTE, snapshot_id="minute-visibility"
    )

    # exactly at bar-open: this bar covers [t, t+1min) and is not yet complete
    dv_at_open = DataView(data, SignalStore(data), t)
    last_before = dv_at_open.last_bar("M")
    assert last_before is not None
    assert last_before.name < t

    # one minute later: the bar is now complete and visible
    dv_after = DataView(data, SignalStore(data), t + timedelta(minutes=1))
    last_after = dv_after.last_bar("M")
    assert last_after is not None
    assert last_after.name == t


# ---------------------------------------------------------------------------
# cross-timeframe aux access
# ---------------------------------------------------------------------------


def test_cross_timeframe_aux_history_and_signal_access(
    daily_frame: pd.DataFrame, minute_frame: pd.DataFrame
) -> None:
    primary = MarketData({"X": minute_frame}, timeframe=Timeframe.MINUTE, snapshot_id="primary")
    aux_daily = MarketData({"X": daily_frame}, timeframe=Timeframe.DAY, snapshot_id="aux-daily")

    mid = len(minute_frame.index) // 2
    now = minute_frame.index[mid] + timedelta(minutes=1)

    dv = DataView(primary, SignalStore(primary), now, aux={Timeframe.DAY: aux_daily})

    # primary timeframe (minute) history is unaffected
    minute_hist = dv.history("X")
    assert minute_hist.index.max() == minute_frame.index[mid]

    # aux (daily) history is sliced with the DAY visibility rule at the same `now`
    daily_hist = dv.history("X", timeframe=Timeframe.DAY)
    assert (daily_hist.index <= now.normalize() - timedelta(days=1)).all()

    # aux signal access routes through the aux SignalStore
    series = dv.signal_series("X", "test_engine_counting_signal_probe", timeframe=Timeframe.DAY)
    assert (series.index <= now.normalize() - timedelta(days=1)).all()


def test_missing_timeframe_raises_dataerror_on_history_and_signal(
    minute_frame: pd.DataFrame,
) -> None:
    primary = MarketData(
        {"X": minute_frame}, timeframe=Timeframe.MINUTE, snapshot_id="missing-tf-primary"
    )
    dv = DataView(primary, SignalStore(primary), minute_frame.index[-1] + timedelta(minutes=1))

    with pytest.raises(DataError):
        dv.history("X", timeframe=Timeframe.DAY)
    with pytest.raises(DataError):
        dv.signal_series("X", "test_engine_counting_signal_probe", timeframe=Timeframe.DAY)


# ---------------------------------------------------------------------------
# empty-history edge cases
# ---------------------------------------------------------------------------


def test_close_and_last_bar_are_none_before_any_data_exists(daily_frame: pd.DataFrame) -> None:
    data = MarketData({"D": daily_frame}, timeframe=Timeframe.DAY, snapshot_id="empty-history")
    # `now` set well before the first bar in the frame
    now = daily_frame.index[0] - timedelta(days=30)
    dv = DataView(data, SignalStore(data), now)

    assert dv.close("D") is None
    assert dv.last_bar("D") is None
    assert dv.history("D").empty


def test_market_data_isolated_from_source_and_returned_frame_mutations(
    daily_frame: pd.DataFrame,
) -> None:
    original = float(daily_frame["close"].iloc[0])
    data = MarketData({"D": daily_frame}, snapshot_id="immutable")

    daily_frame.iloc[0, daily_frame.columns.get_loc("close")] = -1.0
    assert float(data.full_frame("D")["close"].iloc[0]) == original

    exposed = data.full_frame("D")
    exposed.iloc[0, exposed.columns.get_loc("close")] = -2.0
    assert float(data.full_frame("D")["close"].iloc[0]) == original


# ---------------------------------------------------------------------------
# at() clock advance
# ---------------------------------------------------------------------------


def test_at_advances_the_clock_and_changes_visibility(daily_frame: pd.DataFrame) -> None:
    data = MarketData({"D": daily_frame}, timeframe=Timeframe.DAY, snapshot_id="at-advance")
    store = SignalStore(data)
    start = daily_frame.index[10] + timedelta(hours=9)
    dv = DataView(data, store, start)

    later = daily_frame.index[20] + timedelta(hours=16)
    dv2 = dv.at(later)

    assert dv2.now == pd.Timestamp(later)
    assert dv.now == pd.Timestamp(start)  # original view is untouched (immutable-style advance)
    assert dv2.close("D") != dv.close("D")
    # the underlying data/signal store objects are shared, not recreated
    assert dv2._data is dv._data  # noqa: SLF001
    assert dv2._signals is dv._signals  # noqa: SLF001


def test_assert_visible_raises_lookaheaderror_for_future_ts(daily_frame: pd.DataFrame) -> None:
    data = MarketData({"D": daily_frame}, timeframe=Timeframe.DAY, snapshot_id="assert-visible")
    mid = len(daily_frame.index) // 2
    now = daily_frame.index[mid] + timedelta(hours=9)  # before close
    dv = DataView(data, SignalStore(data), now)

    with pytest.raises(LookAheadError):
        dv.assert_visible(daily_frame.index[mid])  # today's bar, not yet complete

    dv.assert_visible(daily_frame.index[mid - 1])  # yesterday's bar: fine


# ---------------------------------------------------------------------------
# SignalStore caching
# ---------------------------------------------------------------------------


def test_signal_store_computes_once_across_two_dataview_reads(daily_frame: pd.DataFrame) -> None:
    calls = {"n": 0}

    @register_signal("test_engine_counting_signal_caching", tier="custom")
    def _counting(df: pd.DataFrame, **params: object) -> pd.Series:
        calls["n"] += 1
        return df["close"].rolling(5, min_periods=1).mean()

    data = MarketData({"D": daily_frame}, timeframe=Timeframe.DAY, snapshot_id="cache-test")
    store = SignalStore(data)  # one store shared across both reads

    now1 = daily_frame.index[30] + timedelta(hours=16)
    now2 = daily_frame.index[60] + timedelta(hours=16)
    dv1 = DataView(data, store, now1)
    dv2 = DataView(data, store, now2)

    v1 = dv1.signal("D", "test_engine_counting_signal_caching")
    v2 = dv2.signal("D", "test_engine_counting_signal_caching")

    assert v1 is not None and v2 is not None
    assert calls["n"] == 1, "SignalStore must compute a (symbol, name, params, snapshot) once"


def test_signal_store_recomputes_for_a_different_snapshot_id(daily_frame: pd.DataFrame) -> None:
    calls = {"n": 0}

    @register_signal("test_engine_counting_signal_snapshot", tier="custom")
    def _counting(df: pd.DataFrame, **params: object) -> pd.Series:
        calls["n"] += 1
        return df["close"]

    data_a = MarketData({"D": daily_frame}, timeframe=Timeframe.DAY, snapshot_id="snap-a")
    data_b = MarketData({"D": daily_frame}, timeframe=Timeframe.DAY, snapshot_id="snap-b")
    now = daily_frame.index[30] + timedelta(hours=16)

    DataView(data_a, SignalStore(data_a), now).signal("D", "test_engine_counting_signal_snapshot")
    DataView(data_b, SignalStore(data_b), now).signal("D", "test_engine_counting_signal_snapshot")

    assert calls["n"] == 2, "a different data snapshot_id must not reuse another run's cache"

"""sync_symbols tests. `kite` and `store` are entirely faked -- never network,
never the real (sibling-built) BarStore."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import polars as pl

from tradingos.config.settings import Settings
from tradingos.core.models import Timeframe
from tradingos.core.timeutils import now_ist
from tradingos.data.instruments import Instrument
from tradingos.data.meta import meta_session
from tradingos.data.sync import MINUTE_LOOKBACK_DAYS, sync_symbols


def seed_instrument(settings: Settings, token: int, symbol: str) -> None:
    today = now_ist().date()
    with meta_session(settings.meta_db_path) as session:
        session.add(
            Instrument(
                instrument_token=token,
                tradingsymbol=symbol,
                name=symbol,
                exchange="NSE",
                segment="NSE",
                instrument_type="EQ",
                lot_size=1,
                tick_size=0.05,
                first_seen=today,
                last_seen=today,
            )
        )
        session.commit()


class FakeKite:
    def __init__(self, responder) -> None:
        self._responder = responder
        self.calls: list[tuple] = []

    def historical_data(self, instrument_token, from_date, to_date, interval):
        self.calls.append((instrument_token, from_date, to_date, interval))
        return self._responder(instrument_token, from_date, to_date, interval)


class FakeStore:
    """Minimal stand-in for the (sibling-built) BarStore, matching its pinned API."""

    def __init__(self, last_ts_map: dict[tuple[str, Timeframe], datetime] | None = None) -> None:
        self._last_ts = dict(last_ts_map or {})
        self.written: list[tuple[str, Timeframe, pl.DataFrame]] = []

    def last_ts(self, symbol: str, timeframe: Timeframe) -> datetime | None:
        return self._last_ts.get((symbol, timeframe))

    def write_raw(self, symbol: str, timeframe: Timeframe, df: pl.DataFrame) -> int:
        self.written.append((symbol, timeframe, df))
        if df.height > 0:
            self._last_ts[(symbol, timeframe)] = df["ts"].max()
        return df.height

    def symbols(self, timeframe: Timeframe) -> list[str]:
        return sorted({s for (s, tf) in self._last_ts if tf == timeframe})


def _bar_row(d: date, price: float = 100.0) -> dict:
    return {
        "date": datetime.combine(d, datetime.min.time()).replace(hour=9, minute=15),
        "open": price,
        "high": price,
        "low": price,
        "close": price,
        "volume": 1000,
    }


def day_responder(_token, from_date, to_date, _interval):
    rows = []
    cur = from_date
    while cur <= to_date:
        rows.append(_bar_row(cur))
        cur += timedelta(days=1)
    return rows


def test_resumes_from_one_bar_after_last_ts(settings: Settings) -> None:
    seed_instrument(settings, 1, "RELIANCE")
    kite = FakeKite(day_responder)
    store = FakeStore({("RELIANCE", Timeframe.DAY): datetime(2024, 1, 5, 9, 15)})

    results = sync_symbols(
        kite, settings, ["RELIANCE"], [Timeframe.DAY], store=store, default_start=date(2010, 1, 1)
    )

    assert len(results) == 1
    r = results[0]
    assert r.error is None
    assert kite.calls[0][0] == 1  # instrument_token
    assert kite.calls[0][1] == date(2024, 1, 6)  # one day after last_ts's date


def test_first_sync_uses_default_start_for_day_timeframe(settings: Settings) -> None:
    seed_instrument(settings, 2, "TCS")
    kite = FakeKite(day_responder)
    store = FakeStore()

    sync_symbols(
        kite, settings, ["TCS"], [Timeframe.DAY], store=store, default_start=date(2020, 1, 1)
    )

    assert kite.calls[0][1] == date(2020, 1, 1)


def test_first_sync_caps_minute_lookback_window(settings: Settings) -> None:
    seed_instrument(settings, 3, "INFY")
    kite = FakeKite(lambda *_a: [])
    store = FakeStore()
    today = now_ist().date()

    results = sync_symbols(
        kite, settings, ["INFY"], [Timeframe.MINUTE], store=store, default_start=date(2010, 1, 1)
    )

    assert results[0].rows_added == 0
    expected_start = today - timedelta(days=MINUTE_LOOKBACK_DAYS)
    assert kite.calls[0][1] == expected_start


def test_already_up_to_date_makes_no_requests(settings: Settings) -> None:
    seed_instrument(settings, 4, "WIPRO")
    kite = FakeKite(day_responder)
    today = now_ist().date()
    store = FakeStore({("WIPRO", Timeframe.DAY): datetime.combine(today, datetime.min.time())})

    results = sync_symbols(kite, settings, ["WIPRO"], [Timeframe.DAY], store=store)

    assert kite.calls == []
    assert results[0].rows_added == 0
    assert results[0].error is None


def test_writes_fetched_data_to_store_and_reports_extent(settings: Settings) -> None:
    seed_instrument(settings, 5, "HDFC")
    kite = FakeKite(day_responder)
    store = FakeStore()
    start = date(2024, 1, 1)

    results = sync_symbols(
        kite, settings, ["HDFC"], [Timeframe.DAY], store=store, default_start=start
    )

    r = results[0]
    assert r.rows_added > 0
    assert r.from_ts is not None
    assert r.to_ts is not None
    assert r.from_ts <= r.to_ts
    assert store.written[0][0] == "HDFC"
    assert store.written[0][1] == Timeframe.DAY
    assert store.written[0][2].height == r.rows_added


def test_bad_symbol_error_is_captured_and_batch_continues(settings: Settings) -> None:
    seed_instrument(settings, 6, "GOODCO")
    kite = FakeKite(day_responder)
    store = FakeStore()

    results = sync_symbols(
        kite,
        settings,
        ["MISSING", "GOODCO"],
        [Timeframe.DAY],
        store=store,
        default_start=date(2024, 1, 1),
    )

    assert len(results) == 2
    bad = next(r for r in results if r.symbol == "MISSING")
    good = next(r for r in results if r.symbol == "GOODCO")
    assert bad.error is not None
    assert bad.rows_added == 0
    assert good.error is None
    assert good.rows_added > 0


def test_on_synced_hook_called_only_for_successes(settings: Settings) -> None:
    seed_instrument(settings, 7, "AXISBANK")
    kite = FakeKite(day_responder)
    store = FakeStore()
    calls: list[tuple[str, Timeframe]] = []

    sync_symbols(
        kite,
        settings,
        ["MISSING", "AXISBANK"],
        [Timeframe.DAY],
        store=store,
        default_start=date(2024, 1, 1),
        on_synced=lambda s, tf: calls.append((s, tf)),
    )

    assert calls == [("AXISBANK", Timeframe.DAY)]


# ---------------------------------------------------------------------------
# completed-bar clamp: an intraday sync must never store a still-forming candle
# ---------------------------------------------------------------------------


def test_daily_sync_before_close_clamps_to_previous_day(settings: Settings) -> None:
    seed_instrument(settings, 20, "CLAMPCO")
    kite = FakeKite(day_responder)
    store = FakeStore({("CLAMPCO", Timeframe.DAY): datetime(2024, 1, 5, 9, 15)})

    # Wednesday 2024-01-10 12:00 IST: today's daily candle is still forming
    results = sync_symbols(
        kite,
        settings,
        ["CLAMPCO"],
        [Timeframe.DAY],
        store=store,
        now=datetime(2024, 1, 10, 12, 0),
    )

    assert results[0].error is None
    assert kite.calls[0][2] == date(2024, 1, 9)  # to_date excludes today
    stored = store.written[0][2]
    assert stored["ts"].max().date() == date(2024, 1, 9)


def test_daily_sync_at_close_includes_today(settings: Settings) -> None:
    seed_instrument(settings, 21, "CLOSECO")
    kite = FakeKite(day_responder)
    store = FakeStore({("CLOSECO", Timeframe.DAY): datetime(2024, 1, 5, 9, 15)})

    # 15:30 IST: today's daily bar is complete (bars complete AT the close)
    results = sync_symbols(
        kite,
        settings,
        ["CLOSECO"],
        [Timeframe.DAY],
        store=store,
        now=datetime(2024, 1, 10, 15, 30),
    )

    assert results[0].error is None
    assert kite.calls[0][2] == date(2024, 1, 10)


def test_daily_sync_intraday_with_only_today_missing_makes_no_request(
    settings: Settings,
) -> None:
    seed_instrument(settings, 22, "UPTODATECO")
    kite = FakeKite(day_responder)
    store = FakeStore({("UPTODATECO", Timeframe.DAY): datetime(2024, 1, 9, 9, 15)})

    results = sync_symbols(
        kite,
        settings,
        ["UPTODATECO"],
        [Timeframe.DAY],
        store=store,
        now=datetime(2024, 1, 10, 12, 0),
    )

    assert kite.calls == []
    assert results[0].rows_added == 0
    assert results[0].error is None


def test_minute_sync_drops_still_forming_bar(settings: Settings) -> None:
    seed_instrument(settings, 23, "MINCO")
    day = date(2024, 1, 10)

    def minute_responder(_token, _from_date, _to_date, _interval):
        # 09:58 and 09:59 bars are complete at 10:00:30; the 10:00 bar is
        # still forming (it completes at 10:01).
        return [
            {
                "date": datetime(2024, 1, 10, 9, 58),
                "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 10,
            },
            {
                "date": datetime(2024, 1, 10, 9, 59),
                "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 10,
            },
            {
                "date": datetime(2024, 1, 10, 10, 0),
                "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 10,
            },
        ]

    kite = FakeKite(minute_responder)
    store = FakeStore()

    results = sync_symbols(
        kite,
        settings,
        ["MINCO"],
        [Timeframe.MINUTE],
        store=store,
        now=datetime(2024, 1, 10, 10, 0, 30),
    )

    assert results[0].error is None
    assert results[0].rows_added == 2
    stored = store.written[0][2]
    assert stored["ts"].to_list() == [
        datetime(2024, 1, 10, 9, 58),
        datetime(2024, 1, 10, 9, 59),
    ]
    assert results[0].to_ts == datetime(2024, 1, 10, 9, 59)
    # the fetch itself still spans through today (minute bars complete
    # continuously; only the forming tail is dropped) -- the LAST chunk's
    # to_date is today
    assert kite.calls[-1][2] == day


def test_result_count_is_symbols_times_timeframes(settings: Settings) -> None:
    seed_instrument(settings, 8, "A")
    seed_instrument(settings, 9, "B")
    kite = FakeKite(day_responder)
    store = FakeStore()

    results = sync_symbols(
        kite,
        settings,
        ["A", "B"],
        [Timeframe.DAY, Timeframe.MINUTE],
        store=store,
        default_start=date(2024, 1, 1),
    )

    assert len(results) == 4
    pairs = {(r.symbol, r.timeframe) for r in results}
    assert pairs == {
        ("A", Timeframe.DAY),
        ("A", Timeframe.MINUTE),
        ("B", Timeframe.DAY),
        ("B", Timeframe.MINUTE),
    }

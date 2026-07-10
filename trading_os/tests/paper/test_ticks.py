from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import polars as pl
import pytest
from fixtures.ticks import kite_tick_dicts, synthetic_ticks

from tradingos.config.settings import Settings
from tradingos.core.errors import ConfigError
from tradingos.core.models import Tick
from tradingos.core.timeutils import to_naive_ist
from tradingos.paper.ticks import TICK_SCHEMA, TickRecorder, TickStreamer, read_ticks

_PART_NAME_RE = re.compile(r"^part-\d{5}-[0-9a-f]{8}\.parquet$")


# ---------------------------------------------------------------------------
# TickRecorder
# ---------------------------------------------------------------------------


def test_flush_on_empty_buffer_returns_empty_list(settings: Settings) -> None:
    rec = TickRecorder(settings.ticks_dir)
    assert rec.flush() == []


def test_record_buffers_without_writing_until_flush_every(settings: Settings) -> None:
    rec = TickRecorder(settings.ticks_dir, flush_every=5)
    ticks = synthetic_ticks(n=5, seed=1)
    day_dir = settings.ticks_dir / ticks[0].ts.date().isoformat()

    for t in ticks[:4]:
        rec.record(t)
    assert not day_dir.exists()

    rec.record(ticks[4])  # 5th tick crosses flush_every -> auto-flush
    assert day_dir.exists()
    parts = list(day_dir.glob("part-*.parquet"))
    assert len(parts) == 1
    assert pl.read_parquet(parts[0]).height == 5


def test_explicit_flush_writes_part_file_with_expected_naming(settings: Settings) -> None:
    rec = TickRecorder(settings.ticks_dir, flush_every=500)
    ticks = synthetic_ticks(n=10, seed=2)
    for t in ticks:
        rec.record(t)

    paths = rec.flush()
    assert len(paths) == 1
    path = paths[0]
    assert path.exists()
    assert path.parent.name == ticks[0].ts.date().isoformat()
    assert path.parent.parent == settings.ticks_dir
    assert _PART_NAME_RE.match(path.name), path.name

    # buffer is drained: a second flush with nothing new writes nothing
    assert rec.flush() == []


def test_part_file_sequence_increments_within_one_instance(settings: Settings) -> None:
    rec = TickRecorder(settings.ticks_dir, flush_every=3)
    ticks = synthetic_ticks(n=9, seed=3)
    for t in ticks:
        rec.record(t)
    rec.close()

    day_dir = settings.ticks_dir / ticks[0].ts.date().isoformat()
    parts = sorted(p.name for p in day_dir.glob("part-*.parquet"))
    assert len(parts) == 3
    assert [p.split("-")[1] for p in parts] == ["00000", "00001", "00002"]


def test_close_flushes_remainder(settings: Settings) -> None:
    rec = TickRecorder(settings.ticks_dir, flush_every=500)
    ticks = synthetic_ticks(n=3, seed=4)
    for t in ticks:
        rec.record(t)
    rec.close()

    day_dir = settings.ticks_dir / ticks[0].ts.date().isoformat()
    parts = list(day_dir.glob("part-*.parquet"))
    assert len(parts) == 1
    assert pl.read_parquet(parts[0]).height == 3


def test_record_splits_across_day_directories(settings: Settings) -> None:
    day1 = date(2024, 1, 15)
    day2 = date(2024, 1, 16)
    ticks_day1 = synthetic_ticks(n=4, day=day1, seed=10)
    ticks_day2 = synthetic_ticks(n=6, day=day2, seed=11)

    rec = TickRecorder(settings.ticks_dir, flush_every=500)
    for t in ticks_day1 + ticks_day2:
        rec.record(t)
    paths = rec.flush()

    assert len(paths) == 2
    assert {p.parent.name for p in paths} == {day1.isoformat(), day2.isoformat()}
    day1_path = next(p for p in paths if p.parent.name == day1.isoformat())
    day2_path = next(p for p in paths if p.parent.name == day2.isoformat())
    assert pl.read_parquet(day1_path).height == 4
    assert pl.read_parquet(day2_path).height == 6


# ---------------------------------------------------------------------------
# read_ticks
# ---------------------------------------------------------------------------


def test_read_ticks_round_trip_sorted_by_ts(settings: Settings) -> None:
    rec = TickRecorder(settings.ticks_dir, flush_every=37)
    ticks = synthetic_ticks(n=150, seed=5)
    for t in ticks:
        rec.record(t)
    rec.close()

    df = read_ticks(settings.ticks_dir, ticks[0].ts.date())
    assert df.height == len(ticks)
    ts_list = df["ts"].to_list()
    assert ts_list == sorted(ts_list)
    assert ts_list == [to_naive_ist(t.ts) for t in ticks]
    assert df["symbol"].unique().to_list() == [ticks[0].symbol]
    assert df["last_price"].to_list() == [t.last_price for t in ticks]


def test_read_ticks_filters_by_symbol(settings: Settings) -> None:
    day = date(2024, 2, 1)
    a = synthetic_ticks(symbol="AAA", token=1, day=day, n=10, seed=6)
    b = synthetic_ticks(symbol="BBB", token=2, day=day, n=10, seed=7)
    rec = TickRecorder(settings.ticks_dir, flush_every=500)
    for t in a + b:
        rec.record(t)
    rec.close()

    df_a = read_ticks(settings.ticks_dir, day, symbol="AAA")
    assert df_a.height == 10
    assert df_a["symbol"].unique().to_list() == ["AAA"]

    df_none = read_ticks(settings.ticks_dir, day, symbol="ZZZ")
    assert df_none.height == 0
    assert list(df_none.columns) == list(TICK_SCHEMA.keys())


def test_read_ticks_empty_day_returns_schema_correct_empty_frame(settings: Settings) -> None:
    df = read_ticks(settings.ticks_dir, date(2099, 1, 1))
    assert df.height == 0
    assert list(df.columns) == list(TICK_SCHEMA.keys())
    for col, dtype in TICK_SCHEMA.items():
        assert df.schema[col] == dtype


def test_restart_new_recorder_instance_preserves_old_part_files(settings: Settings) -> None:
    day = date(2024, 3, 1)
    ticks1 = synthetic_ticks(day=day, n=5, seed=8)
    rec1 = TickRecorder(settings.ticks_dir, flush_every=500)
    for t in ticks1:
        rec1.record(t)
    rec1.close()

    day_dir = settings.ticks_dir / day.isoformat()
    first_parts = {p.name for p in day_dir.glob("part-*.parquet")}
    assert len(first_parts) == 1

    # Simulate a process restart: a brand new TickRecorder instance, seq
    # resets to 0, but the uuid suffix guarantees no filename collision.
    ticks2 = synthetic_ticks(day=day, n=5, seed=9)
    rec2 = TickRecorder(settings.ticks_dir, flush_every=500)
    for t in ticks2:
        rec2.record(t)
    rec2.close()

    all_parts = {p.name for p in day_dir.glob("part-*.parquet")}
    assert first_parts.issubset(all_parts)
    assert len(all_parts) == 2

    df = read_ticks(settings.ticks_dir, day)
    assert df.height == 10


# ---------------------------------------------------------------------------
# TickStreamer fakes
# ---------------------------------------------------------------------------


class FakeTicker:
    """Fake KiteTicker double: records subscribe/set_mode/connect calls and
    exposes on_* callback attributes so tests can fire them manually."""

    MODE_FULL = "full"
    MODE_QUOTE = "quote"
    MODE_LTP = "ltp"

    def __init__(self, api_key: str, access_token: str, **kwargs: Any) -> None:
        self.api_key = api_key
        self.access_token = access_token
        self.init_kwargs = kwargs
        self.on_ticks: Any = None
        self.on_connect: Any = None
        self.on_close: Any = None
        self.on_error: Any = None
        self.on_reconnect: Any = None
        self.on_noreconnect: Any = None
        self.subscribe_calls: list[list[int]] = []
        self.set_mode_calls: list[tuple[str, list[int]]] = []
        self.connect_calls: list[dict[str, Any]] = []
        self.close_calls = 0
        self._connected = False

    def subscribe(self, instrument_tokens: list[int]) -> None:
        self.subscribe_calls.append(list(instrument_tokens))

    def set_mode(self, mode: str, instrument_tokens: list[int]) -> None:
        self.set_mode_calls.append((mode, list(instrument_tokens)))

    def connect(self, threaded: bool = False, **kwargs: Any) -> None:
        self.connect_calls.append({"threaded": threaded, **kwargs})
        self._connected = True

    def is_connected(self) -> bool:
        return self._connected

    def close(self, code: Any = None, reason: Any = None) -> None:
        self.close_calls += 1
        self._connected = False


class FakeTickerFactory:
    """Callable `ticker_factory`; records every FakeTicker it constructs so
    tests can reach in and fire the on_* callbacks manually."""

    def __init__(self) -> None:
        self.instances: list[FakeTicker] = []

    def __call__(self, *args: Any, **kwargs: Any) -> FakeTicker:
        ticker = FakeTicker(*args, **kwargs)
        self.instances.append(ticker)
        return ticker

    @property
    def last(self) -> FakeTicker:
        return self.instances[-1]


TOKEN_TO_SYMBOL = {1001: "AAA", 1002: "BBB"}


def _make_streamer(**overrides: Any) -> tuple[TickStreamer, FakeTickerFactory, list[Tick]]:
    factory = FakeTickerFactory()
    received: list[Tick] = []
    kwargs: dict[str, Any] = dict(
        api_key="key",
        access_token="token",
        token_to_symbol=TOKEN_TO_SYMBOL,
        on_tick=received.append,
        ticker_factory=factory,
    )
    kwargs.update(overrides)
    streamer = TickStreamer(**kwargs)
    return streamer, factory, received


# ---------------------------------------------------------------------------
# TickStreamer: construction / instrument cap
# ---------------------------------------------------------------------------


def test_too_many_instruments_raises_config_error() -> None:
    token_to_symbol = {i: f"SYM{i}" for i in range(3001)}
    with pytest.raises(ConfigError):
        TickStreamer(
            api_key="key",
            access_token="token",
            token_to_symbol=token_to_symbol,
            on_tick=lambda t: None,
            ticker_factory=FakeTickerFactory(),
        )


def test_exactly_max_instruments_is_allowed() -> None:
    token_to_symbol = {i: f"SYM{i}" for i in range(TickStreamer.MAX_INSTRUMENTS_PER_CONNECTION)}
    streamer, _factory, _received = _make_streamer(token_to_symbol=token_to_symbol)
    assert streamer is not None


# ---------------------------------------------------------------------------
# TickStreamer: lifecycle
# ---------------------------------------------------------------------------


def test_start_connects_threaded_by_default() -> None:
    streamer, factory, _received = _make_streamer()
    streamer.start()
    assert factory.last.connect_calls == [{"threaded": True}]
    assert streamer.is_connected is True


def test_start_can_run_unthreaded() -> None:
    streamer, factory, _received = _make_streamer()
    streamer.start(threaded=False)
    assert factory.last.connect_calls == [{"threaded": False}]


def test_stop_closes_underlying_ticker() -> None:
    streamer, factory, _received = _make_streamer()
    streamer.start()
    streamer.stop()
    assert factory.last.close_calls == 1
    assert streamer.is_connected is False


# ---------------------------------------------------------------------------
# TickStreamer: on_connect resubscribe
# ---------------------------------------------------------------------------


def test_on_connect_resubscribes_full_token_list_in_mode_full() -> None:
    _streamer, factory, _received = _make_streamer()
    ticker = factory.last
    ticker.on_connect(ticker, {"some": "response"})
    assert ticker.subscribe_calls == [[1001, 1002]]
    assert ticker.set_mode_calls == [("full", [1001, 1002])]


# ---------------------------------------------------------------------------
# TickStreamer: kite dict -> Tick mapping
# ---------------------------------------------------------------------------


def test_on_ticks_maps_kite_dict_with_depth_to_tick() -> None:
    _streamer, factory, received = _make_streamer()
    ticker = factory.last
    src = synthetic_ticks(symbol="AAA", token=1001, n=1, seed=42)
    raw = kite_tick_dicts(src)

    ticker.on_ticks(ticker, raw)

    assert len(received) == 1
    tick = received[0]
    assert tick.symbol == "AAA"
    assert tick.instrument_token == 1001
    assert tick.bid == src[0].bid
    assert tick.ask == src[0].ask
    assert tick.last_price == src[0].last_price
    assert tick.volume == src[0].volume
    assert tick.ts == to_naive_ist(src[0].ts)
    assert tick.ts.tzinfo is None


def test_missing_depth_maps_to_none_bid_ask() -> None:
    _streamer, factory, received = _make_streamer()
    ticker = factory.last
    src = synthetic_ticks(symbol="AAA", token=1001, n=1, seed=1)
    raw = kite_tick_dicts(src)
    del raw[0]["depth"]

    ticker.on_ticks(ticker, raw)

    assert received[0].bid is None
    assert received[0].ask is None
    assert received[0].last_price == src[0].last_price


def test_zero_price_depth_level_maps_to_none() -> None:
    _streamer, factory, received = _make_streamer()
    ticker = factory.last
    src = synthetic_ticks(symbol="AAA", token=1001, n=1, seed=2)
    raw = kite_tick_dicts(src)
    raw[0]["depth"]["buy"] = [{"price": 0, "quantity": 0, "orders": 0}]
    raw[0]["depth"]["sell"] = []

    ticker.on_ticks(ticker, raw)

    assert received[0].bid is None
    assert received[0].ask is None


def test_missing_exchange_timestamp_falls_back_to_last_trade_time() -> None:
    _streamer, factory, received = _make_streamer()
    ticker = factory.last
    src = synthetic_ticks(symbol="AAA", token=1001, n=1, seed=3)
    raw = kite_tick_dicts(src)
    fallback_ts = src[0].ts - timedelta(seconds=5)
    raw[0]["last_trade_time"] = fallback_ts
    del raw[0]["exchange_timestamp"]

    ticker.on_ticks(ticker, raw)

    assert received[0].ts == to_naive_ist(fallback_ts)


def test_exchange_timestamp_preferred_over_last_trade_time() -> None:
    _streamer, factory, received = _make_streamer()
    ticker = factory.last
    src = synthetic_ticks(symbol="AAA", token=1001, n=1, seed=13)
    raw = kite_tick_dicts(src)
    raw[0]["last_trade_time"] = src[0].ts - timedelta(seconds=100)

    ticker.on_ticks(ticker, raw)

    assert received[0].ts == to_naive_ist(src[0].ts)


def test_missing_both_timestamps_falls_back_to_now(monkeypatch: pytest.MonkeyPatch) -> None:
    fixed_now = datetime(2024, 1, 15, 12, 0, 0)
    monkeypatch.setattr("tradingos.paper.ticks.now_ist", lambda: fixed_now)
    _streamer, factory, received = _make_streamer()
    ticker = factory.last
    src = synthetic_ticks(symbol="AAA", token=1001, n=1, seed=4)
    raw = kite_tick_dicts(src)
    del raw[0]["exchange_timestamp"]
    del raw[0]["last_trade_time"]

    ticker.on_ticks(ticker, raw)

    assert received[0].ts == fixed_now


def test_ts_normalized_from_tz_aware_exchange_timestamp() -> None:
    _streamer, factory, received = _make_streamer()
    ticker = factory.last
    src = synthetic_ticks(symbol="AAA", token=1001, n=1, seed=9)
    raw = kite_tick_dicts(src)
    aware = src[0].ts.replace(tzinfo=ZoneInfo("Asia/Kolkata")).astimezone(ZoneInfo("UTC"))
    raw[0]["exchange_timestamp"] = aware

    ticker.on_ticks(ticker, raw)

    assert received[0].ts.tzinfo is None
    assert received[0].ts == src[0].ts


def test_unknown_token_dropped_with_warning(caplog: pytest.LogCaptureFixture) -> None:
    _streamer, factory, received = _make_streamer()
    ticker = factory.last
    src = synthetic_ticks(symbol="ZZZ", token=9999, n=1, seed=5)
    raw = kite_tick_dicts(src)

    with caplog.at_level(logging.WARNING, logger="tradingos.paper.ticks"):
        ticker.on_ticks(ticker, raw)

    assert received == []
    assert "9999" in caplog.text


# ---------------------------------------------------------------------------
# TickStreamer: recorder wiring + callback robustness
# ---------------------------------------------------------------------------


def test_recorder_records_tick_before_on_tick_callback(settings: Settings) -> None:
    rec = TickRecorder(settings.ticks_dir, flush_every=1)
    _streamer, factory, received = _make_streamer(recorder=rec)
    ticker = factory.last
    src = synthetic_ticks(symbol="AAA", token=1001, n=1, seed=6)
    raw = kite_tick_dicts(src)

    ticker.on_ticks(ticker, raw)

    assert len(received) == 1
    day_dir = settings.ticks_dir / src[0].ts.date().isoformat()
    assert len(list(day_dir.glob("part-*.parquet"))) == 1


def test_on_tick_callback_exception_does_not_propagate(
    caplog: pytest.LogCaptureFixture,
) -> None:
    def bad_callback(tick: Tick) -> None:
        raise RuntimeError("boom")

    factory = FakeTickerFactory()
    streamer = TickStreamer(
        api_key="key",
        access_token="token",
        token_to_symbol=TOKEN_TO_SYMBOL,
        on_tick=bad_callback,
        ticker_factory=factory,
    )
    ticker = factory.last
    src = synthetic_ticks(symbol="AAA", token=1001, n=1, seed=7)
    raw = kite_tick_dicts(src)

    with caplog.at_level(logging.ERROR, logger="tradingos.paper.ticks"):
        ticker.on_ticks(ticker, raw)  # must not raise

    assert streamer is not None
    assert "boom" in caplog.text


def test_on_ticks_continues_after_callback_exception_for_remaining_ticks() -> None:
    calls: list[Tick] = []

    def flaky_callback(tick: Tick) -> None:
        if len(calls) == 0:
            calls.append(tick)
            raise RuntimeError("boom")
        calls.append(tick)

    factory = FakeTickerFactory()
    streamer = TickStreamer(
        api_key="key",
        access_token="token",
        token_to_symbol=TOKEN_TO_SYMBOL,
        on_tick=flaky_callback,
        ticker_factory=factory,
    )
    ticker = factory.last
    src = synthetic_ticks(symbol="AAA", token=1001, n=2, seed=14)
    raw = kite_tick_dicts(src)

    ticker.on_ticks(ticker, raw)

    assert streamer is not None
    assert len(calls) == 2  # both ticks processed despite the first raising


# ---------------------------------------------------------------------------
# TickStreamer: on_noreconnect -> on_disconnect hook
# ---------------------------------------------------------------------------


def test_on_noreconnect_calls_on_disconnect_hook() -> None:
    calls: list[str] = []
    factory = FakeTickerFactory()
    streamer = TickStreamer(
        api_key="key",
        access_token="token",
        token_to_symbol=TOKEN_TO_SYMBOL,
        on_tick=lambda t: None,
        on_disconnect=calls.append,
        ticker_factory=factory,
    )
    ticker = factory.last

    ticker.on_noreconnect(ticker)

    assert streamer is not None
    assert len(calls) == 1
    assert isinstance(calls[0], str) and calls[0]


def test_on_noreconnect_without_hook_does_not_raise() -> None:
    factory = FakeTickerFactory()
    streamer = TickStreamer(
        api_key="key",
        access_token="token",
        token_to_symbol=TOKEN_TO_SYMBOL,
        on_tick=lambda t: None,
        ticker_factory=factory,
    )
    ticker = factory.last

    ticker.on_noreconnect(ticker)  # must not raise

    assert streamer is not None

"""Tests for paper/runner.py: PaperSessionRunner's session-open order
placement, session-close rebalance + EOD report, and the cron scheduler shell
around both.

A tiny deterministic strategy (a single "close price" signal, top-2-of-3
selection, equal-weight sizing) is used throughout so every queued order's
symbol/side/qty/client_order_id is a hand-computed literal, not just "did it
run" -- see module docstring convention in tests/paper/test_eod.py.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time

import pandas as pd
import polars as pl
import pytest

from tradingos.config.schemas import (
    ScoreSpec,
    SelectionSpec,
    SignalSpec,
    SizingSpec,
    StrategyConfig,
    UniverseSpec,
)
from tradingos.config.settings import Settings
from tradingos.core.models import (
    Fill,
    Order,
    OrderStatus,
    OrderType,
    Product,
    Side,
    Tick,
    Timeframe,
)
from tradingos.core.timeutils import MARKET_CLOSE
from tradingos.data.calendar import NSECalendar
from tradingos.data.store import BarStore
from tradingos.paper.broker import PaperBroker
from tradingos.paper.ledgerdb import PaperStore
from tradingos.paper.runner import PaperSessionRunner
from tradingos.strategies.registry import register_signal

_LOGGER_NAME = "tradingos.paper.runner"


@register_signal("runner_test_close")
def _close_signal(df: pd.DataFrame, **params: object) -> pd.Series:
    return df["close"]


# ---------------------------------------------------------------------------
# fixtures / helpers
# ---------------------------------------------------------------------------


def _make_config(name: str, capital: float = 100_000.0) -> StrategyConfig:
    return StrategyConfig(
        name=name,
        capital=capital,
        universe=UniverseSpec(symbols=["AAA", "BBB", "CCC"], point_in_time=False),
        signals=[SignalSpec(id="px", name="runner_test_close")],
        score=ScoreSpec(type="single"),
        selection=SelectionSpec(method="top_n", n=2, exit_rank=2),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.6),
    )


def _seed_bar(
    bar_store: BarStore, symbol: str, day: date, close: float, open_: float | None = None
) -> None:
    if open_ is None:
        open_ = close
    df = pl.DataFrame(
        {
            "ts": [datetime.combine(day, time(0, 0))],
            "open": [open_],
            "high": [max(open_, close)],
            "low": [min(open_, close)],
            "close": [close],
            "volume": [100_000],
        }
    )
    bar_store.write_raw(symbol, Timeframe.DAY, df)


def _make_broker(
    settings: Settings,
    config: StrategyConfig,
    store: PaperStore,
    calendar: NSECalendar,
    now: datetime | None = None,
    slippage_bps: float | None = None,
) -> PaperBroker:
    return PaperBroker(
        settings,
        strategy_id=config.name,
        capital=config.capital,
        slippage_bps=slippage_bps,
        calendar=calendar,
        store=store,
        enforce_market_hours=False,
        # Pin the broker's clock to the fixture day where given: an order only
        # immediate-matches against a SAME-DAY quote (quote ts date == now_fn()
        # date), so the wall clock must agree with the synthetic tick dates.
        now_fn=(lambda: now) if now is not None else None,
    )


def _make_runner(
    settings: Settings,
    config: StrategyConfig,
    store: PaperStore,
    now: datetime | None = None,
    slippage_bps: float | None = None,
) -> tuple[PaperSessionRunner, PaperBroker, NSECalendar]:
    calendar = NSECalendar(settings)
    broker = _make_broker(settings, config, store, calendar, now=now, slippage_bps=slippage_bps)
    runner = PaperSessionRunner(settings, config, broker, calendar=calendar, store=store)
    return runner, broker, calendar


# ---------------------------------------------------------------------------
# on_session_open
# ---------------------------------------------------------------------------


def test_on_session_open_places_and_fills_queued_orders(settings: Settings) -> None:
    config = _make_config("runner-open")
    store = PaperStore(settings.paper_db_path, config.name)
    store.ensure_run(config.capital)
    day = date(2024, 2, 7)  # Wednesday, an ordinary NSE trading day
    runner, broker, _calendar = _make_runner(
        settings, config, store, now=datetime.combine(day, time(9, 20))
    )
    order_a = Order(
        client_order_id="o-a",
        symbol="AAA",
        side=Side.BUY,
        qty=10,
        order_type=OrderType.MARKET,
        product=Product.CNC,
    )
    order_b = Order(
        client_order_id="o-b",
        symbol="BBB",
        side=Side.BUY,
        qty=5,
        order_type=OrderType.MARKET,
        product=Product.CNC,
    )
    broker.queue_for_open(order_a, day)
    broker.queue_for_open(order_b, day)

    # Quotes must exist before place_order can match a MARKET order.
    broker.on_tick(
        Tick(
            symbol="AAA",
            instrument_token=1,
            ts=datetime.combine(day, time(9, 16)),
            last_price=100.0,
            bid=99.9,
            ask=100.1,
            volume=1_000,
        )
    )
    broker.on_tick(
        Tick(
            symbol="BBB",
            instrument_token=2,
            ts=datetime.combine(day, time(9, 16)),
            last_price=200.0,
            bid=199.9,
            ask=200.1,
            volume=1_000,
        )
    )

    placed = runner.on_session_open(day)

    assert len(placed) == 2
    assert {o.symbol for o in placed} == {"AAA", "BBB"}
    for o in placed:
        assert o.status == OrderStatus.COMPLETE
        assert o.filled_qty == o.qty

    holdings = {p.symbol: p.qty for p in broker.get_holdings()}
    assert holdings == {"AAA": 10, "BBB": 5}


def test_on_session_open_with_nothing_queued_returns_empty(settings: Settings) -> None:
    config = _make_config("runner-open-empty")
    store = PaperStore(settings.paper_db_path, config.name)
    store.ensure_run(config.capital)
    runner, _broker, _calendar = _make_runner(settings, config, store)

    assert runner.on_session_open(date(2024, 2, 7)) == []


# ---------------------------------------------------------------------------
# prime_open_quotes
# ---------------------------------------------------------------------------


def test_prime_open_quotes_fills_planned_order_at_open_plus_slippage(
    settings: Settings,
) -> None:
    """A tickless session (--once): prime_open_quotes feeds the day's bar OPEN
    as a synthetic 09:15 tick, so the planned MARKET BUY fills at exactly
    round(open * (1 + slip), 2) -- the day's OPEN, never its close."""
    config = _make_config("runner-prime")
    store = PaperStore(settings.paper_db_path, config.name)
    store.ensure_run(config.capital)
    day = date(2024, 2, 7)  # Wednesday, an ordinary NSE trading day
    runner, broker, _calendar = _make_runner(
        settings,
        config,
        store,
        now=datetime.combine(day, time(9, 20)),
        slippage_bps=10.0,  # slip = 0.001 exactly, for a deterministic literal
    )

    bar_store = BarStore(settings)
    # open != close so a fill at the close would be caught: 100.0 vs 110.0.
    _seed_bar(bar_store, "AAA", day, close=110.0, open_=100.0)

    order = Order(
        client_order_id="prime-a",
        symbol="AAA",
        side=Side.BUY,
        qty=10,
        order_type=OrderType.MARKET,
        product=Product.CNC,
    )
    broker.queue_for_open(order, day)

    assert runner.prime_open_quotes(day) == 1

    placed = runner.on_session_open(day)

    assert len(placed) == 1
    assert placed[0].status == OrderStatus.COMPLETE
    assert placed[0].filled_qty == 10
    fills = store.fills(day=day)
    assert len(fills) == 1
    # Synthetic open tick has bid/ask None -> MARKET BUY prices off last=open:
    # round(100.0 * (1 + 10bps), 2) = 100.10.
    assert fills[0].price == pytest.approx(100.10)
    assert {p.symbol: p.qty for p in broker.get_holdings()} == {"AAA": 10}


def test_prime_open_quotes_skips_symbol_without_day_bar(
    settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    """No bar for `day` in the store: prime feeds nothing (returns 0), logs a
    WARNING, and the planned order stays PENDING (no quote -> place_planned
    leaves it for a later retry)."""
    config = _make_config("runner-prime-missing")
    store = PaperStore(settings.paper_db_path, config.name)
    store.ensure_run(config.capital)
    day = date(2024, 2, 8)  # Thursday
    runner, broker, _calendar = _make_runner(
        settings, config, store, now=datetime.combine(day, time(9, 20))
    )

    bar_store = BarStore(settings)
    _seed_bar(bar_store, "AAA", date(2024, 2, 7), 100.0)  # stale: no bar for `day`

    order = Order(
        client_order_id="prime-b",
        symbol="AAA",
        side=Side.BUY,
        qty=10,
        order_type=OrderType.MARKET,
        product=Product.CNC,
    )
    broker.queue_for_open(order, day)

    with caplog.at_level(logging.WARNING, logger=_LOGGER_NAME):
        fed = runner.prime_open_quotes(day)

    assert fed == 0
    assert "AAA" in caplog.text
    assert "stay PENDING" in caplog.text

    placed = runner.on_session_open(day)  # no quote known -> nothing placeable

    assert placed == []
    stored = store.get_order("prime-b")
    assert stored is not None
    assert stored.status == OrderStatus.PENDING


# ---------------------------------------------------------------------------
# on_session_close
# ---------------------------------------------------------------------------


def test_on_session_close_snapshots_evaluates_and_queues_rebalance(settings: Settings) -> None:
    config = _make_config("runner-close")
    store = PaperStore(settings.paper_db_path, config.name)
    store.ensure_run(config.capital)

    # Pre-existing holding that will NOT make the cut (only top-2 of 3 by
    # close price are selected, and AAA has the lowest close -> gets sold).
    store.record_fill(
        Fill(
            client_order_id="seed-aaa",
            symbol="AAA",
            side=Side.BUY,
            qty=100,
            price=100.0,
            ts=datetime(2024, 2, 6, 9, 20),
            charges=0.0,
            product=Product.CNC,
        )
    )

    runner, broker, calendar = _make_runner(settings, config, store)
    bar_store = BarStore(settings)
    day = date(2024, 2, 8)  # Thursday
    _seed_bar(bar_store, "AAA", day, 100.0)
    _seed_bar(bar_store, "BBB", day, 200.0)
    _seed_bar(bar_store, "CCC", day, 300.0)

    # equity right now: cash 100_000 - 100*100 = 90_000, + mark(AAA)=100*100
    # (marked at entry price, never re-marked) = 100_000.0 exactly.
    assert broker.equity() == pytest.approx(100_000.0)

    report_path = runner.on_session_close(day)

    assert report_path.exists()
    assert report_path.name == f"eod-{day.isoformat()}.html"

    close_ts = datetime.combine(day, MARKET_CLOSE)
    equity_curve = store.equity_curve()
    assert close_ts in equity_curve.index
    # The 15:30 snapshot is marked to the day's closes: cash 90_000 +
    # 100 shares * AAA close 100.0 = 100_000.0 (close == fill price here;
    # see test_on_session_close_marks_no_tick_broker_to_day_close for the
    # case where they differ).
    assert equity_curve.loc[close_ts] == pytest.approx(100_000.0)

    next_day = calendar.next_trading_day(day)
    assert next_day == date(2024, 2, 9)  # Friday, no holiday in between

    queued = store.planned_orders(next_day)
    assert [o.symbol for o in queued] == ["AAA", "BBB", "CCC"]
    assert [o.side for o in queued] == [Side.SELL, Side.BUY, Side.BUY]
    assert [o.qty for o in queued] == [100, 250, 166]
    assert [o.client_order_id for o in queued] == [
        f"{config.name}-{next_day.isoformat()}-AAA-SELL",
        f"{config.name}-{next_day.isoformat()}-BBB-BUY",
        f"{config.name}-{next_day.isoformat()}-CCC-BUY",
    ]
    for o in queued:
        assert o.tag == "rebalance"
        assert o.order_type == OrderType.MARKET
        assert o.product == Product.CNC
        assert o.status == OrderStatus.PENDING


def test_on_session_close_idempotent_client_order_ids_on_rerun(settings: Settings) -> None:
    """Re-running on_session_close for the same day (a restart) recomputes the
    exact same client_order_ids -- queue_for_open upserts by that id rather
    than duplicating the queue."""
    config = _make_config("runner-close-idempotent")
    store = PaperStore(settings.paper_db_path, config.name)
    store.ensure_run(config.capital)
    store.record_fill(
        Fill(
            client_order_id="seed-aaa",
            symbol="AAA",
            side=Side.BUY,
            qty=100,
            price=100.0,
            ts=datetime(2024, 2, 6, 9, 20),
            charges=0.0,
            product=Product.CNC,
        )
    )

    runner, _broker, calendar = _make_runner(settings, config, store)
    bar_store = BarStore(settings)
    day = date(2024, 2, 8)
    _seed_bar(bar_store, "AAA", day, 100.0)
    _seed_bar(bar_store, "BBB", day, 200.0)
    _seed_bar(bar_store, "CCC", day, 300.0)

    runner.on_session_close(day)
    runner.on_session_close(day)

    next_day = calendar.next_trading_day(day)
    queued = store.planned_orders(next_day)
    assert len(queued) == 3  # not 6 -- the second pass upserted, not duplicated


def test_on_session_close_rerun_cancels_stale_planned_orders(settings: Settings) -> None:
    """A close-job re-run whose freshly computed targets no longer want a
    previously queued order must CANCEL that stale queue entry — otherwise it
    still fires at the next open alongside the new orders (review fix,
    2026-07-10).

    Run 1 holds AAA=100 and queues AAA-SELL-100 / BBB-BUY-250 / CCC-BUY-166.
    AAA is then sold intraday (fill recorded, broker rebuilt — the restart
    scenario); run 2's delta set is only BBB/CCC, so the stale AAA-SELL must
    end CANCELLED while BBB/CCC are upserted with re-sized quantities."""
    config = _make_config("runner-close-stale-planned")
    store = PaperStore(settings.paper_db_path, config.name)
    store.ensure_run(config.capital)
    store.record_fill(
        Fill(
            client_order_id="seed-aaa",
            symbol="AAA",
            side=Side.BUY,
            qty=100,
            price=100.0,
            ts=datetime(2024, 2, 6, 9, 20),
            charges=0.0,
            product=Product.CNC,
        )
    )

    runner, _broker, calendar = _make_runner(settings, config, store)
    bar_store = BarStore(settings)
    day = date(2024, 2, 8)
    _seed_bar(bar_store, "AAA", day, 100.0)
    _seed_bar(bar_store, "BBB", day, 200.0)
    _seed_bar(bar_store, "CCC", day, 300.0)

    runner.on_session_close(day)
    next_day = calendar.next_trading_day(day)
    assert [o.client_order_id for o in store.planned_orders(next_day)] == [
        f"{config.name}-{next_day.isoformat()}-AAA-SELL",
        f"{config.name}-{next_day.isoformat()}-BBB-BUY",
        f"{config.name}-{next_day.isoformat()}-CCC-BUY",
    ]

    # AAA gets sold intraday (e.g. a manual exit); the runner restarts and the
    # close job re-runs for the same day. Holdings are now empty, cash 120_000
    # (100_000 - 10_000 buy + 30_000 sell), so the new deltas are only
    # BBB +300 (60_000/200) and CCC +200 (60_000/300).
    store.record_fill(
        Fill(
            client_order_id="manual-exit-aaa",
            symbol="AAA",
            side=Side.SELL,
            qty=100,
            price=300.0,
            ts=datetime(2024, 2, 8, 10, 0),
            charges=0.0,
            product=Product.CNC,
        )
    )
    runner2, _broker2, _calendar2 = _make_runner(settings, config, store)
    runner2.on_session_close(day)

    queued = store.planned_orders(next_day)
    assert [o.symbol for o in queued] == ["BBB", "CCC"]
    assert [o.side for o in queued] == [Side.BUY, Side.BUY]
    assert [o.qty for o in queued] == [300, 200]

    stale = store.get_order(f"{config.name}-{next_day.isoformat()}-AAA-SELL")
    assert stale is not None
    assert stale.status == OrderStatus.CANCELLED


def test_on_session_close_no_delta_queues_nothing(settings: Settings) -> None:
    config = _make_config("runner-close-noop")
    store = PaperStore(settings.paper_db_path, config.name)
    store.ensure_run(config.capital)

    # Holdings already exactly match what tomorrow's rebalance would target.
    store.record_fill(
        Fill(
            client_order_id="seed-bbb",
            symbol="BBB",
            side=Side.BUY,
            qty=250,
            price=200.0,
            ts=datetime(2024, 2, 6, 9, 20),
            charges=0.0,
            product=Product.CNC,
        )
    )
    store.record_fill(
        Fill(
            client_order_id="seed-ccc",
            symbol="CCC",
            side=Side.BUY,
            qty=166,
            price=300.0,
            ts=datetime(2024, 2, 6, 9, 25),
            charges=0.0,
            product=Product.CNC,
        )
    )

    runner, broker, calendar = _make_runner(settings, config, store)
    bar_store = BarStore(settings)
    day = date(2024, 2, 8)
    _seed_bar(bar_store, "AAA", day, 100.0)
    _seed_bar(bar_store, "BBB", day, 200.0)
    _seed_bar(bar_store, "CCC", day, 300.0)

    assert broker.equity() == pytest.approx(100_000.0)

    report_path = runner.on_session_close(day)

    assert report_path.exists()
    next_day = calendar.next_trading_day(day)
    assert store.planned_orders(next_day) == []


def test_on_session_close_marks_no_tick_broker_to_day_close(settings: Settings) -> None:
    """A broker that saw NO ticks (fresh replay of a stored fill -- e.g. a
    report-only / --once run) must get its 15:30 snapshot valued at the day's
    close from the bar store, NOT at the old fill price."""
    config = _make_config("runner-mark-close")
    store = PaperStore(settings.paper_db_path, config.name)
    store.ensure_run(config.capital)
    store.record_fill(
        Fill(
            client_order_id="seed-aaa",
            symbol="AAA",
            side=Side.BUY,
            qty=100,
            price=100.0,
            ts=datetime(2024, 2, 6, 9, 20),
            charges=0.0,
            product=Product.CNC,
        )
    )

    runner, broker, _calendar = _make_runner(settings, config, store)
    bar_store = BarStore(settings)
    day = date(2024, 2, 8)
    _seed_bar(bar_store, "AAA", day, 150.0)  # AAA closed at 150, up from the 100.0 fill
    _seed_bar(bar_store, "BBB", day, 200.0)
    _seed_bar(bar_store, "CCC", day, 300.0)

    # Pre-close, the replayed ledger (no ticks ever) still values AAA at its
    # fill price: cash 90_000 + 100 * 100.0 = 100_000.
    assert broker.equity() == pytest.approx(100_000.0)

    runner.on_session_close(day)

    close_ts = datetime.combine(day, MARKET_CLOSE)
    equity_curve = store.equity_curve()
    # cash 90_000 + 100 shares * day close 150.0 = 105_000 -- the day's close
    # from the bar store, not the stale fill-price valuation of 100_000.
    assert equity_curve.loc[close_ts] == pytest.approx(105_000.0)
    assert broker.equity() == pytest.approx(105_000.0)


def test_on_session_close_warns_on_stale_bar_data(
    settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    config = _make_config("runner-stale")
    store = PaperStore(settings.paper_db_path, config.name)
    store.ensure_run(config.capital)
    runner, _broker, _calendar = _make_runner(settings, config, store)

    bar_store = BarStore(settings)
    stale_day = date(2024, 2, 7)
    day = date(2024, 2, 8)  # no bar dated `day` is stored -- one day stale
    _seed_bar(bar_store, "AAA", stale_day, 100.0)
    _seed_bar(bar_store, "BBB", stale_day, 200.0)
    _seed_bar(bar_store, "CCC", stale_day, 300.0)

    with caplog.at_level(logging.WARNING, logger=_LOGGER_NAME):
        report_path = runner.on_session_close(day)

    assert report_path.exists()  # stale data is a loud warning, not a hard stop
    assert "STALE" in caplog.text
    assert day.isoformat() in caplog.text


# ---------------------------------------------------------------------------
# build_scheduler
# ---------------------------------------------------------------------------


def _cron_field(job: object, name: str) -> str:
    return str(next(f for f in job.trigger.fields if f.name == name))  # type: ignore[attr-defined]


def test_build_scheduler_returns_expected_cron_jobs(settings: Settings) -> None:
    config = _make_config("runner-sched")
    store = PaperStore(settings.paper_db_path, config.name)
    runner, _broker, _calendar = _make_runner(settings, config, store)

    scheduler = runner.build_scheduler()
    try:
        jobs = {job.id: job for job in scheduler.get_jobs()}
        assert len(jobs) == 2

        open_job = jobs[f"{config.name}-session-open"]
        assert _cron_field(open_job, "day_of_week") == "mon-fri"
        assert _cron_field(open_job, "hour") == "9"
        # 09:15-09:25, once a minute: the first firing can beat the day's
        # first ticks (MARKET orders rest until a same-day quote exists), so
        # the open is retried idempotently across a 10-minute window.
        assert _cron_field(open_job, "minute") == "15-25"

        close_job = jobs[f"{config.name}-session-close"]
        assert _cron_field(close_job, "day_of_week") == "mon-fri"
        assert _cron_field(close_job, "hour") == "15"
        assert _cron_field(close_job, "minute") == "35"
    finally:
        # scheduler.shutdown() requires a started scheduler; it was never
        # started (no thread/timer exists), so there is nothing to tear down.
        assert scheduler.state is not None


# ---------------------------------------------------------------------------
# scheduler wrapper: no-op on non-trading days, swallows exceptions
# ---------------------------------------------------------------------------


def test_scheduler_wrappers_skip_non_trading_days(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _make_config("runner-holiday")
    store = PaperStore(settings.paper_db_path, config.name)
    runner, _broker, _calendar = _make_runner(settings, config, store)

    called: list[str] = []
    monkeypatch.setattr(runner, "on_session_open", lambda day: called.append("open"))
    monkeypatch.setattr(runner, "on_session_close", lambda day: called.append("close"))

    saturday = datetime(2024, 2, 10, 9, 15)  # weekend -> not an NSE trading day
    runner._run_open_job(now=saturday)
    runner._run_close_job(now=saturday)

    assert called == []


def test_scheduler_wrappers_swallow_exceptions(
    settings: Settings, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    config = _make_config("runner-boom")
    store = PaperStore(settings.paper_db_path, config.name)
    runner, _broker, _calendar = _make_runner(settings, config, store)

    def boom(day: date) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(runner, "on_session_open", boom)
    monkeypatch.setattr(runner, "on_session_close", boom)

    trading_dt = datetime(2024, 2, 8, 9, 15)  # an ordinary NSE trading day

    with caplog.at_level(logging.ERROR, logger=_LOGGER_NAME):
        runner._run_open_job(now=trading_dt)  # must not raise
        runner._run_close_job(now=trading_dt)  # must not raise

    assert caplog.text.count("boom") >= 2
    assert "session open job failed" in caplog.text
    assert "session close job failed" in caplog.text

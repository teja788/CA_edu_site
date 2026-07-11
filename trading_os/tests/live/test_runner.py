"""Tests for live/runner.py: LiveSessionRunner's session-open order
placement (from the runner-owned planned queue), session-close rebalance +
next-open queueing, stale-planned cancellation, and the cron scheduler shell.

Reuses ``FakeKite`` / ``FakeClock`` / ``make_broker`` / ``_permissive_limits``
from ``tests/live/test_broker.py`` (imported, not duplicated -- that file is
never modified here). A tiny deterministic strategy (single "close price"
signal, top-2-of-3 selection, equal-weight sizing) mirrors
``tests/paper/test_runner.py`` so every queued order is a hand-computed
literal, not just "did it run". A DIFFERENT registered-signal name
(``live_runner_test_close``) is used to avoid registry collisions with the
paper runner's tests.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time

import pandas as pd
import polars as pl
import pytest

from live.test_broker import FakeClock, FakeKite, make_broker  # noqa: E402 -- test seam reuse
from tradingos.broker.killswitch import KillSwitch
from tradingos.config.schemas import (
    ScoreSpec,
    SelectionSpec,
    SignalSpec,
    SizingSpec,
    StrategyConfig,
    UniverseSpec,
)
from tradingos.config.settings import Settings
from tradingos.core.errors import BrokerError
from tradingos.core.models import Order, OrderStatus, OrderType, Product, Side, Timeframe
from tradingos.core.timeutils import session_bounds
from tradingos.data.calendar import NSECalendar
from tradingos.data.store import BarStore
from tradingos.live.broker import ZerodhaLiveBroker
from tradingos.live.runner import LiveSessionRunner
from tradingos.paper.ledgerdb import PaperStore
from tradingos.strategies.registry import register_signal

_LOGGER_NAME = "tradingos.live.runner"


@register_signal("live_runner_test_close")
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
        signals=[SignalSpec(id="px", name="live_runner_test_close")],
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


def _make_runner(
    settings: Settings,
    config: StrategyConfig,
    store: PaperStore,
    kite: FakeKite,
    now: datetime,
    dry_run: bool = True,
    kill_switch: KillSwitch | None = None,
) -> tuple[LiveSessionRunner, ZerodhaLiveBroker, NSECalendar]:
    calendar = NSECalendar(settings)
    clock = FakeClock(now)
    broker = make_broker(
        settings, store, kite, dry_run=dry_run, clock=clock, kill_switch=kill_switch
    )
    runner = LiveSessionRunner(
        settings, config, broker, calendar=calendar, store=store, now_fn=clock
    )
    return runner, broker, calendar


def _planned_order(cid: str, symbol: str, side: Side, qty: int) -> Order:
    return Order(
        client_order_id=cid,
        symbol=symbol,
        side=side,
        qty=qty,
        order_type=OrderType.MARKET,
        product=Product.CNC,
        tag="rebalance",
    )


# ---------------------------------------------------------------------------
# on_session_open
# ---------------------------------------------------------------------------


def test_on_session_open_places_queued_orders_in_dry_run(settings: Settings) -> None:
    config = _make_config("live-runner-open")
    store = PaperStore(settings.live_db_path, config.name)
    day = date(2024, 2, 7)  # Wednesday, an ordinary NSE trading day
    kite = FakeKite(ltp_price=100.0)
    runner, broker, _calendar = _make_runner(
        settings, config, store, kite, now=datetime.combine(day, time(9, 20))
    )
    store.save_order(_planned_order("o-a", "AAA", Side.BUY, 10), planned_for=day)
    store.save_order(_planned_order("o-b", "BBB", Side.BUY, 5), planned_for=day)

    placed = runner.on_session_open(day)

    assert len(placed) == 2
    assert {o.symbol for o in placed} == {"AAA", "BBB"}
    for o in placed:
        assert o.status == OrderStatus.OPEN  # dry-run journals OPEN with a DRY-n id
        assert o.broker_order_id is not None and o.broker_order_id.startswith("DRY-")
    assert kite.place_calls == []  # dry-run never calls the mutating API

    # The exact intended kite kwargs are what the CLI prints in dry-run.
    assert len(broker.intended_calls) == 2
    assert {kw["tradingsymbol"] for kw in broker.intended_calls} == {"AAA", "BBB"}
    for kw in broker.intended_calls:
        assert kw["variety"] == "regular"
        assert kw["transaction_type"] == "BUY"
        assert kw["order_type"] == "MARKET"


def test_on_session_open_after_dry_rehearsal_still_places_for_real(
    settings: Settings,
) -> None:
    """A morning dry-run rehearsal consumes the planned queue (rows go OPEN
    with DRY-n ids). The real session for the same day must still place those
    orders at Kite -- the runner re-reads them via
    ``planned_orders(include_dry_placed=True)`` and the broker supersedes the
    dry intents. Without the fix the real session silently places nothing."""
    config = _make_config("live-runner-dry-then-live")
    store = PaperStore(settings.live_db_path, config.name)
    day = date(2024, 2, 7)
    now = datetime.combine(day, time(9, 20))
    store.save_order(_planned_order("dl-a", "AAA", Side.BUY, 10), planned_for=day)
    store.save_order(_planned_order("dl-b", "BBB", Side.BUY, 5), planned_for=day)

    # 1. dry-run rehearsal consumes the queue.
    dry_runner, _dry_broker, _ = _make_runner(
        settings, config, store, FakeKite(ltp_price=100.0), now=now, dry_run=True
    )
    rehearsed = dry_runner.on_session_open(day)
    assert len(rehearsed) == 2
    assert store.get_order("dl-a").broker_order_id.startswith("DRY-")

    # 2. the real session must still place both orders at Kite, exactly once.
    live_kite = FakeKite(ltp_price=100.0)
    live_runner, _live_broker, _ = _make_runner(
        settings, config, store, live_kite, now=now, dry_run=False
    )
    placed = live_runner.on_session_open(day)

    assert len(placed) == 2
    assert {o.symbol for o in placed} == {"AAA", "BBB"}
    assert all(o.broker_order_id.startswith("KITE") for o in placed)
    assert len(live_kite.place_calls) == 2

    # 3. a scheduler re-fire (09:16 etc.) must not re-place anything.
    assert live_runner.on_session_open(day) == []
    assert len(live_kite.place_calls) == 2


def test_on_session_open_with_nothing_queued_returns_empty(settings: Settings) -> None:
    config = _make_config("live-runner-open-empty")
    store = PaperStore(settings.live_db_path, config.name)
    day = date(2024, 2, 7)
    kite = FakeKite()
    runner, _broker, _calendar = _make_runner(
        settings, config, store, kite, now=datetime.combine(day, time(9, 20))
    )

    assert runner.on_session_open(day) == []


def test_on_session_open_kill_switch_halts_batch_leaving_rest_pending(
    settings: Settings,
) -> None:
    """The kill switch is checked per-order inside the broker BEFORE any Kite
    call. The order in flight when it trips is rejected+persisted by the
    broker itself; the runner's batch loop then halts, leaving every
    not-yet-attempted order PENDING for a retry once the switch disengages."""
    config = _make_config("live-runner-killswitch")
    store = PaperStore(settings.live_db_path, config.name)
    day = date(2024, 2, 7)
    kite = FakeKite()
    ks = KillSwitch(settings.kill_switch_path)
    ks.engage("halt for test")
    runner, _broker, _calendar = _make_runner(
        settings, config, store, kite, now=datetime.combine(day, time(9, 20)), kill_switch=ks
    )
    store.save_order(_planned_order("k-a", "AAA", Side.BUY, 10), planned_for=day)
    store.save_order(_planned_order("k-b", "BBB", Side.BUY, 5), planned_for=day)

    placed = runner.on_session_open(day)

    assert placed == []
    assert store.get_order("k-a").status == OrderStatus.REJECTED
    assert store.get_order("k-b").status == OrderStatus.PENDING  # never attempted
    assert kite.calls == []  # kill switch is checked before any Kite call


# ---------------------------------------------------------------------------
# on_session_close
# ---------------------------------------------------------------------------


def test_on_session_close_evaluates_and_queues_rebalance(settings: Settings) -> None:
    config = _make_config("live-runner-close")
    store = PaperStore(settings.live_db_path, config.name)
    day = date(2024, 2, 8)  # Thursday
    kite = FakeKite(
        holdings_response=[
            {
                "tradingsymbol": "AAA",
                "quantity": 100,
                "t1_quantity": 0,
                "average_price": 100.0,
                "last_price": 100.0,
            }
        ],
        margins_response={
            "available": {"live_balance": 90_000.0, "cash": 90_000.0},
            "utilised": {"debits": 0.0},
        },
    )
    runner, broker, calendar = _make_runner(
        settings, config, store, kite, now=datetime.combine(day, time(15, 35))
    )
    bar_store = BarStore(settings)
    _seed_bar(bar_store, "AAA", day, 100.0)
    _seed_bar(bar_store, "BBB", day, 200.0)
    _seed_bar(bar_store, "CCC", day, 300.0)

    # equity: cash 90_000 + 100 * AAA last_price 100.0 = 100_000
    assert broker.equity() == pytest.approx(100_000.0)

    queued = runner.on_session_close(day)

    next_day = calendar.next_trading_day(day)
    assert next_day == date(2024, 2, 9)  # Friday, no holiday in between

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

    planned = store.planned_orders(next_day)
    assert len(planned) == 3


def test_on_session_close_no_delta_queues_nothing(settings: Settings) -> None:
    config = _make_config("live-runner-close-noop")
    store = PaperStore(settings.live_db_path, config.name)
    day = date(2024, 2, 8)
    kite = FakeKite(
        holdings_response=[
            {
                "tradingsymbol": "BBB",
                "quantity": 250,
                "t1_quantity": 0,
                "average_price": 200.0,
                "last_price": 200.0,
            },
            {
                "tradingsymbol": "CCC",
                "quantity": 166,
                "t1_quantity": 0,
                "average_price": 300.0,
                "last_price": 300.0,
            },
        ],
        margins_response={
            "available": {"live_balance": 200.0, "cash": 200.0},  # 250*200+166*300+200 ~ 100_000
            "utilised": {"debits": 0.0},
        },
    )
    runner, _broker, calendar = _make_runner(
        settings, config, store, kite, now=datetime.combine(day, time(15, 35))
    )
    bar_store = BarStore(settings)
    _seed_bar(bar_store, "AAA", day, 100.0)
    _seed_bar(bar_store, "BBB", day, 200.0)
    _seed_bar(bar_store, "CCC", day, 300.0)

    queued = runner.on_session_close(day)

    assert queued == []
    next_day = calendar.next_trading_day(day)
    assert store.planned_orders(next_day) == []


def test_on_session_close_snapshots_close_equity(settings: Settings) -> None:
    config = _make_config("live-runner-close-snapshot")
    store = PaperStore(settings.live_db_path, config.name)
    day = date(2024, 2, 8)  # Thursday
    kite = FakeKite(
        holdings_response=[
            {
                "tradingsymbol": "AAA",
                "quantity": 100,
                "t1_quantity": 0,
                "average_price": 100.0,
                "last_price": 100.0,
            }
        ],
        margins_response={
            "available": {"live_balance": 90_000.0, "cash": 90_000.0},
            "utilised": {"debits": 0.0},
        },
    )
    runner, _broker, _calendar = _make_runner(
        settings, config, store, kite, now=datetime.combine(day, time(15, 35))
    )
    bar_store = BarStore(settings)
    _seed_bar(bar_store, "AAA", day, 100.0)
    _seed_bar(bar_store, "BBB", day, 200.0)
    _seed_bar(bar_store, "CCC", day, 300.0)

    runner.on_session_close(day)

    close_ts = session_bounds(day)[1]
    equity_curve = store.equity_curve()
    cash_curve = store.cash_curve()
    assert close_ts in equity_curve.index
    # cash 90_000 + 100 * AAA last_price 100.0 = 100_000, mirroring paper's
    # PaperBroker.snapshot close-equity convention.
    assert equity_curve[close_ts] == pytest.approx(100_000.0)
    assert cash_curve[close_ts] == pytest.approx(90_000.0)


def test_on_session_close_skips_snapshot_when_margins_read_fails_but_close_still_completes(
    settings: Settings, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A margins-only read failure (the runner's SECOND, snapshot-only
    ``get_margins()`` call, distinct from the equity read the runner already
    made and reuses for sizing) must skip only the equity snapshot -- the
    close evaluation must still complete using the equity value already
    fetched, producing the exact same rebalance as the healthy-margins case,
    without a third (also-failing) broker round trip."""
    config = _make_config("live-runner-close-margins-fail")
    store = PaperStore(settings.live_db_path, config.name)
    day = date(2024, 2, 8)
    kite = FakeKite(
        holdings_response=[
            {
                "tradingsymbol": "AAA",
                "quantity": 100,
                "t1_quantity": 0,
                "average_price": 100.0,
                "last_price": 100.0,
            }
        ],
        margins_response={
            "available": {"live_balance": 90_000.0, "cash": 90_000.0},
            "utilised": {"debits": 0.0},
        },
    )
    runner, broker, calendar = _make_runner(
        settings, config, store, kite, now=datetime.combine(day, time(15, 35))
    )
    bar_store = BarStore(settings)
    _seed_bar(bar_store, "AAA", day, 100.0)
    _seed_bar(bar_store, "BBB", day, 200.0)
    _seed_bar(bar_store, "CCC", day, 300.0)

    # The runner's `equity()` read (used for sizing) succeeds; its second,
    # snapshot-only `get_margins()` read fails -- simulating a transient
    # broker hiccup on that specific call.
    real_get_margins = broker.get_margins
    call_count = {"n": 0}

    def flaky_get_margins():
        call_count["n"] += 1
        if call_count["n"] >= 2:
            raise BrokerError("margins temporarily unavailable")
        return real_get_margins()

    monkeypatch.setattr(broker, "get_margins", flaky_get_margins)

    with caplog.at_level(logging.WARNING, logger=_LOGGER_NAME):
        queued = runner.on_session_close(day)

    assert "skipping close equity snapshot" in caplog.text

    close_ts = session_bounds(day)[1]
    assert close_ts not in store.equity_curve().index  # snapshot was skipped

    # Close evaluation still completed, using the already-fetched equity
    # (100_000) for sizing -- identical result to the healthy-margins case.
    next_day = calendar.next_trading_day(day)
    assert [o.symbol for o in queued] == ["AAA", "BBB", "CCC"]
    assert [o.side for o in queued] == [Side.SELL, Side.BUY, Side.BUY]
    assert [o.qty for o in queued] == [100, 250, 166]
    assert next_day == date(2024, 2, 9)


def test_on_session_close_rerun_cancels_stale_planned_orders_without_kite_cancel(
    settings: Settings,
) -> None:
    """A close-job re-run (e.g. after a restart) whose freshly computed
    targets no longer want a previously queued order must CANCEL that stale
    queue entry -- but WITHOUT ever calling kite.cancel_order, because the
    stale order was only ever a local queue entry, never sent to the broker."""
    config = _make_config("live-runner-stale")
    store = PaperStore(settings.live_db_path, config.name)
    day = date(2024, 2, 8)
    now = datetime.combine(day, time(15, 35))

    kite1 = FakeKite(
        holdings_response=[
            {
                "tradingsymbol": "AAA",
                "quantity": 100,
                "t1_quantity": 0,
                "average_price": 100.0,
                "last_price": 100.0,
            }
        ],
        margins_response={
            "available": {"live_balance": 90_000.0, "cash": 90_000.0},
            "utilised": {"debits": 0.0},
        },
    )
    runner1, _broker1, calendar = _make_runner(settings, config, store, kite1, now=now)
    bar_store = BarStore(settings)
    _seed_bar(bar_store, "AAA", day, 100.0)
    _seed_bar(bar_store, "BBB", day, 200.0)
    _seed_bar(bar_store, "CCC", day, 300.0)

    runner1.on_session_close(day)
    next_day = calendar.next_trading_day(day)
    assert [o.client_order_id for o in store.planned_orders(next_day)] == [
        f"{config.name}-{next_day.isoformat()}-AAA-SELL",
        f"{config.name}-{next_day.isoformat()}-BBB-BUY",
        f"{config.name}-{next_day.isoformat()}-CCC-BUY",
    ]

    # Runner restarts (fresh broker instance, SAME journal store). AAA was
    # sold intraday at the broker (e.g. a manual exit) -- reflected as a
    # change in what Kite itself now reports for holdings/margins.
    kite2 = FakeKite(
        holdings_response=[],
        margins_response={
            "available": {"live_balance": 120_000.0, "cash": 120_000.0},
            "utilised": {"debits": 0.0},
        },
    )
    runner2, _broker2, _calendar2 = _make_runner(settings, config, store, kite2, now=now)

    queued = runner2.on_session_close(day)

    assert [o.symbol for o in queued] == ["BBB", "CCC"]
    assert [o.side for o in queued] == [Side.BUY, Side.BUY]
    assert [o.qty for o in queued] == [300, 200]

    stale = store.get_order(f"{config.name}-{next_day.isoformat()}-AAA-SELL")
    assert stale is not None
    assert stale.status == OrderStatus.CANCELLED

    assert [name for name, _ in kite1.calls if name == "cancel_order"] == []
    assert [name for name, _ in kite2.calls if name == "cancel_order"] == []


def test_on_session_close_warns_on_stale_bar_data(
    settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    config = _make_config("live-runner-stale-data")
    store = PaperStore(settings.live_db_path, config.name)
    day = date(2024, 2, 8)  # no bar dated `day` is stored -- one day stale
    kite = FakeKite()
    runner, _broker, _calendar = _make_runner(
        settings, config, store, kite, now=datetime.combine(day, time(15, 35))
    )
    bar_store = BarStore(settings)
    stale_day = date(2024, 2, 7)
    _seed_bar(bar_store, "AAA", stale_day, 100.0)
    _seed_bar(bar_store, "BBB", stale_day, 200.0)
    _seed_bar(bar_store, "CCC", stale_day, 300.0)

    with caplog.at_level(logging.WARNING, logger=_LOGGER_NAME):
        runner.on_session_close(day)  # stale data is a loud warning, not a hard stop

    assert "STALE" in caplog.text
    assert day.isoformat() in caplog.text


# ---------------------------------------------------------------------------
# build_scheduler
# ---------------------------------------------------------------------------


def _cron_field(job: object, name: str) -> str:
    return str(next(f for f in job.trigger.fields if f.name == name))  # type: ignore[attr-defined]


def test_build_scheduler_returns_expected_cron_jobs(settings: Settings) -> None:
    config = _make_config("live-runner-sched")
    store = PaperStore(settings.live_db_path, config.name)
    kite = FakeKite()
    runner, _broker, _calendar = _make_runner(
        settings, config, store, kite, now=datetime(2024, 2, 7, 9, 0)
    )

    scheduler = runner.build_scheduler()
    try:
        jobs = {job.id: job for job in scheduler.get_jobs()}
        assert len(jobs) == 3

        open_job = jobs[f"{config.name}-session-open"]
        assert _cron_field(open_job, "day_of_week") == "mon-fri"
        assert _cron_field(open_job, "hour") == "9"
        assert _cron_field(open_job, "minute") == "15-25"

        close_job = jobs[f"{config.name}-session-close"]
        assert _cron_field(close_job, "day_of_week") == "mon-fri"
        assert _cron_field(close_job, "hour") == "15"
        assert _cron_field(close_job, "minute") == "35"

        reconcile_job = jobs[f"{config.name}-reconcile"]
        assert _cron_field(reconcile_job, "day_of_week") == "mon-fri"
        assert _cron_field(reconcile_job, "hour") == "9-15"
        assert _cron_field(reconcile_job, "minute") == "*/5"
    finally:
        assert scheduler.state is not None  # never started; nothing to shut down


# ---------------------------------------------------------------------------
# scheduler wrappers: no-op on non-trading days, swallow exceptions
# ---------------------------------------------------------------------------


def test_open_close_job_wrappers_skip_non_trading_days(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _make_config("live-runner-holiday")
    store = PaperStore(settings.live_db_path, config.name)
    kite = FakeKite()
    runner, _broker, _calendar = _make_runner(
        settings, config, store, kite, now=datetime(2024, 2, 7, 9, 0)
    )

    called: list[str] = []
    monkeypatch.setattr(runner, "on_session_open", lambda day: called.append("open"))
    monkeypatch.setattr(runner, "on_session_close", lambda day: called.append("close"))

    saturday = datetime(2024, 2, 10, 9, 15)  # weekend -> not an NSE trading day
    runner._run_open_job(now=saturday)
    runner._run_close_job(now=saturday)

    assert called == []


def test_open_close_job_wrappers_swallow_exceptions(
    settings: Settings, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    config = _make_config("live-runner-boom")
    store = PaperStore(settings.live_db_path, config.name)
    kite = FakeKite()
    runner, _broker, _calendar = _make_runner(
        settings, config, store, kite, now=datetime(2024, 2, 7, 9, 0)
    )

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


def test_reconcile_job_noop_outside_session_window(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _make_config("live-runner-reconcile-window")
    store = PaperStore(settings.live_db_path, config.name)
    kite = FakeKite()
    runner, _broker, _calendar = _make_runner(
        settings, config, store, kite, now=datetime(2024, 2, 7, 9, 0)
    )

    called: list[object] = []
    monkeypatch.setattr(
        "tradingos.live.runner._reconcile_once", lambda broker, alerter: called.append(1)
    )

    # Before 09:15 and after 15:30 of an ordinary trading day: no-op.
    runner._run_reconcile_job(now=datetime(2024, 2, 7, 9, 0))
    runner._run_reconcile_job(now=datetime(2024, 2, 7, 15, 45))
    # A weekend firing: no-op too.
    runner._run_reconcile_job(now=datetime(2024, 2, 10, 12, 0))

    assert called == []


def test_reconcile_job_calls_reconcile_once_within_session_window(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _make_config("live-runner-reconcile-call")
    store = PaperStore(settings.live_db_path, config.name)
    kite = FakeKite()
    runner, broker, _calendar = _make_runner(
        settings, config, store, kite, now=datetime(2024, 2, 7, 9, 0)
    )

    seen: list[object] = []

    def fake_reconcile_once(b: object, alerter: object) -> list[object]:
        seen.append(b)
        return []

    monkeypatch.setattr("tradingos.live.runner._reconcile_once", fake_reconcile_once)

    runner._run_reconcile_job(now=datetime(2024, 2, 7, 10, 0))  # mid-session, trading day

    assert seen == [broker]


def test_reconcile_job_swallows_exceptions(
    settings: Settings, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    config = _make_config("live-runner-reconcile-boom")
    store = PaperStore(settings.live_db_path, config.name)
    kite = FakeKite()
    runner, _broker, _calendar = _make_runner(
        settings, config, store, kite, now=datetime(2024, 2, 7, 9, 0)
    )

    def boom(broker: object, alerter: object) -> list[object]:
        raise RuntimeError("reconcile boom")

    monkeypatch.setattr("tradingos.live.runner._reconcile_once", boom)

    with caplog.at_level(logging.ERROR, logger=_LOGGER_NAME):
        runner._run_reconcile_job(now=datetime(2024, 2, 7, 10, 0))  # must not raise

    assert "reconciliation job failed" in caplog.text

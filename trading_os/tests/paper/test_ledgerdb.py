"""Paper ledger SQLite persistence: round-trip, upsert, day filters, curves,
day-start-equity fallback, reset scoping, engine caching."""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import pytest
from sqlmodel import select

from tradingos.config.settings import Settings
from tradingos.core.models import Fill, Order, OrderStatus, OrderType, Product, Side
from tradingos.paper.ledgerdb import PaperOrderRow, PaperStore, paper_db_session, paper_engine

# --------------------------------------------------------------------------
# engine cache
# --------------------------------------------------------------------------


def test_engine_cached_per_resolved_path(settings: Settings) -> None:
    store_a = PaperStore(settings.paper_db_path, "strat-a")
    store_b = PaperStore(settings.paper_db_path, "strat-b")
    eng_a = paper_engine(store_a.db_path)
    eng_b = paper_engine(store_b.db_path)
    assert eng_a is eng_b
    assert eng_a is paper_engine(settings.paper_db_path)


# --------------------------------------------------------------------------
# Order / Fill round trip
# --------------------------------------------------------------------------


def test_order_round_trip_lossless_all_fields_set(settings: Settings) -> None:
    store = PaperStore(settings.paper_db_path, "strat-a")
    order = Order(
        broker_order_id="BRK-1",
        symbol="TCS",
        exchange="NSE",
        side=Side.SELL,
        qty=15,
        filled_qty=15,
        order_type=OrderType.LIMIT,
        product=Product.MIS,
        limit_price=3500.5,
        trigger_price=3490.0,
        status=OrderStatus.COMPLETE,
        status_message="filled",
        strategy_id="strat-a",
        tag="paper",
        created_at=datetime(2024, 1, 15, 9, 20),
        updated_at=datetime(2024, 1, 15, 9, 21),
    )
    store.save_order(order)
    fetched = store.get_order(order.client_order_id)
    assert fetched == order


def test_order_round_trip_lossless_minimal_none_fields(settings: Settings) -> None:
    store = PaperStore(settings.paper_db_path, "strat-a")
    order = Order(symbol="INFY", side=Side.BUY, qty=1, strategy_id="strat-a")
    store.save_order(order)
    fetched = store.get_order(order.client_order_id)
    assert fetched == order
    assert fetched is not None
    assert fetched.broker_order_id is None
    assert fetched.limit_price is None
    assert fetched.trigger_price is None
    assert fetched.status_message is None
    assert fetched.tag is None
    assert fetched.created_at is None
    assert fetched.updated_at is None


def test_get_order_missing_returns_none(settings: Settings) -> None:
    store = PaperStore(settings.paper_db_path, "strat-a")
    assert store.get_order("does-not-exist") is None


def test_fill_round_trip_lossless_and_day_filter(settings: Settings) -> None:
    store = PaperStore(settings.paper_db_path, "strat-a")
    order = Order(
        symbol="TCS",
        side=Side.BUY,
        qty=10,
        strategy_id="strat-a",
        created_at=datetime(2024, 1, 15, 9, 16),
    )
    store.save_order(order)
    fill = Fill(
        client_order_id=order.client_order_id,
        symbol="TCS",
        side=Side.BUY,
        qty=10,
        price=3500.25,
        ts=datetime(2024, 1, 15, 9, 20, 5),
        charges=12.34,
        product=Product.CNC,
    )
    store.record_fill(fill)

    fetched = store.all_fills()
    assert fetched == [fill]

    assert store.fills(day=date(2024, 1, 15)) == [fill]
    assert store.fills(day=date(2024, 1, 16)) == []


# --------------------------------------------------------------------------
# save_order upsert semantics
# --------------------------------------------------------------------------


def test_save_order_upsert_updates_status_and_preserves_planned_for(settings: Settings) -> None:
    store = PaperStore(settings.paper_db_path, "strat-a")
    order = Order(
        symbol="TCS",
        side=Side.BUY,
        qty=10,
        status=OrderStatus.PENDING,
        strategy_id="strat-a",
        created_at=datetime(2024, 1, 15, 15, 31),
    )
    store.save_order(order, planned_for=date(2024, 1, 16))

    # placed from the planned queue the next morning: status changes, no
    # planned_for arg given -> existing planned_for must be preserved.
    order.transition(OrderStatus.OPEN)
    order.updated_at = datetime(2024, 1, 16, 9, 16)
    store.save_order(order)

    fetched = store.get_order(order.client_order_id)
    assert fetched is not None
    assert fetched.status == OrderStatus.OPEN
    assert fetched.updated_at == datetime(2024, 1, 16, 9, 16)

    planned = store.planned_orders(date(2024, 1, 16))
    assert planned == []  # no longer PENDING, so it drops out of the planned queue

    # explicit planned_for overwrites the stored value
    store.save_order(order, planned_for=date(2024, 1, 17))
    with paper_db_session(store.db_path) as session:
        row = session.exec(
            select(PaperOrderRow).where(PaperOrderRow.client_order_id == order.client_order_id)
        ).first()
        assert row is not None
        assert row.planned_for == date(2024, 1, 17)


# --------------------------------------------------------------------------
# day filters / planned queue / orders_placed_count
# --------------------------------------------------------------------------


def test_orders_day_filter_and_planned_orders(settings: Settings) -> None:
    store = PaperStore(settings.paper_db_path, "strat-a")
    d1 = date(2024, 1, 15)
    d2 = date(2024, 1, 16)

    o1 = Order(
        symbol="TCS",
        side=Side.BUY,
        qty=1,
        status=OrderStatus.PENDING,
        created_at=datetime(2024, 1, 15, 15, 31),
    )
    o2 = Order(
        symbol="INFY",
        side=Side.BUY,
        qty=2,
        status=OrderStatus.PENDING,
        created_at=datetime(2024, 1, 15, 15, 31),
    )
    o3 = Order(
        symbol="WIPRO",
        side=Side.SELL,
        qty=3,
        status=OrderStatus.OPEN,
        created_at=datetime(2024, 1, 16, 9, 16),
    )
    store.save_order(o1, planned_for=d2)
    store.save_order(o2, planned_for=d2)
    store.save_order(o3)

    day1_orders = store.orders(day=d1)
    assert {o.client_order_id for o in day1_orders} == {o1.client_order_id, o2.client_order_id}

    day2_orders = store.orders(day=d2)
    assert [o.client_order_id for o in day2_orders] == [o3.client_order_id]

    planned = store.planned_orders(d2)
    assert [o.client_order_id for o in planned] == [o1.client_order_id, o2.client_order_id]

    # once o1 is actually placed, it drops out of the planned queue even
    # though its planned_for date is preserved
    o1.transition(OrderStatus.OPEN)
    store.save_order(o1)
    assert [o.client_order_id for o in store.planned_orders(d2)] == [o2.client_order_id]


def test_orders_placed_count_excludes_pending(settings: Settings) -> None:
    store = PaperStore(settings.paper_db_path, "strat-a")
    day = date(2024, 1, 15)

    pending = Order(
        symbol="TCS",
        side=Side.BUY,
        qty=1,
        status=OrderStatus.PENDING,
        created_at=datetime(2024, 1, 15, 15, 31),
    )
    opened = Order(
        symbol="INFY",
        side=Side.BUY,
        qty=1,
        status=OrderStatus.OPEN,
        created_at=datetime(2024, 1, 15, 9, 16),
    )
    completed = Order(
        symbol="WIPRO",
        side=Side.SELL,
        qty=1,
        status=OrderStatus.COMPLETE,
        created_at=datetime(2024, 1, 15, 9, 17),
        updated_at=datetime(2024, 1, 15, 9, 18),
    )
    other_day = Order(
        symbol="HDFC",
        side=Side.BUY,
        qty=1,
        status=OrderStatus.OPEN,
        created_at=datetime(2024, 1, 16, 9, 16),
    )
    for o in (pending, opened, completed, other_day):
        store.save_order(o)

    assert store.orders_placed_count(day) == 2


# --------------------------------------------------------------------------
# equity / cash curves
# --------------------------------------------------------------------------


def test_equity_curve_sorted_and_upsert_by_ts(settings: Settings) -> None:
    store = PaperStore(settings.paper_db_path, "strat-a")
    store.snapshot_equity(datetime(2024, 1, 16, 15, 30), equity=110_000.0, cash=50_000.0)
    store.snapshot_equity(datetime(2024, 1, 15, 15, 30), equity=100_000.0, cash=40_000.0)
    # upsert on the same ts -> overwrite in place, no duplicate row
    store.snapshot_equity(datetime(2024, 1, 15, 15, 30), equity=101_000.0, cash=41_000.0)

    curve = store.equity_curve()
    assert isinstance(curve, pd.Series)
    assert curve.index.name == "ts"
    assert curve.name == "equity"
    assert curve.index.is_monotonic_increasing
    assert len(curve) == 2
    assert curve.iloc[0] == 101_000.0
    assert curve.iloc[1] == 110_000.0

    cash_curve = store.cash_curve()
    assert cash_curve.name == "cash"
    assert list(cash_curve.values) == [41_000.0, 50_000.0]


def test_equity_curve_empty_when_no_snapshots(settings: Settings) -> None:
    store = PaperStore(settings.paper_db_path, "strat-empty")
    curve = store.equity_curve()
    assert curve.empty
    assert curve.dtype == float
    assert curve.index.name == "ts"
    assert curve.name == "equity"

    cash = store.cash_curve()
    assert cash.empty
    assert cash.name == "cash"


# --------------------------------------------------------------------------
# day_start_equity fallback chain
# --------------------------------------------------------------------------


def test_day_start_equity_fallback_chain(settings: Settings) -> None:
    store = PaperStore(settings.paper_db_path, "strat-a")
    d1 = date(2024, 1, 15)
    d2 = date(2024, 1, 16)
    d3 = date(2024, 1, 17)

    # no run row, no snapshots -> None
    assert store.day_start_equity(d1) is None

    # run row exists, no snapshots yet -> stored capital
    store.ensure_run(capital=500_000.0)
    assert store.day_start_equity(d1) == 500_000.0

    # snapshot(s) strictly BEFORE the day -> latest one before it
    store.snapshot_equity(datetime(2024, 1, 15, 15, 30), equity=505_000.0, cash=500_000.0)
    store.snapshot_equity(datetime(2024, 1, 15, 16, 0), equity=506_000.0, cash=500_000.0)
    assert store.day_start_equity(d2) == 506_000.0

    # snapshot(s) ON the day -> earliest one on that day wins, even with a
    # later snapshot the same day
    store.snapshot_equity(datetime(2024, 1, 17, 9, 20), equity=510_000.0, cash=500_000.0)
    store.snapshot_equity(datetime(2024, 1, 17, 15, 30), equity=515_000.0, cash=500_000.0)
    assert store.day_start_equity(d3) == 510_000.0


# --------------------------------------------------------------------------
# ensure_run / capital
# --------------------------------------------------------------------------


def test_ensure_run_keeps_stored_capital_on_mismatch(
    settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("WARNING")
    store = PaperStore(settings.paper_db_path, "strat-a")
    row1 = store.ensure_run(capital=100_000.0)
    assert row1.capital == 100_000.0

    row2 = store.ensure_run(capital=250_000.0)
    assert row2.capital == 100_000.0  # kept, not overwritten
    assert store.capital() == 100_000.0
    assert any("already exists" in rec.message for rec in caplog.records)


def test_capital_none_when_no_run(settings: Settings) -> None:
    store = PaperStore(settings.paper_db_path, "strat-a")
    assert store.capital() is None


# --------------------------------------------------------------------------
# reset — scoped to strategy_id; isolation between two strategies in one DB
# --------------------------------------------------------------------------


def test_reset_scoped_to_strategy_id_two_strategies_isolated(settings: Settings) -> None:
    db_path = settings.paper_db_path
    store_a = PaperStore(db_path, "strat-a")
    store_b = PaperStore(db_path, "strat-b")

    store_a.ensure_run(capital=100_000.0)
    store_b.ensure_run(capital=200_000.0)

    order_a = Order(
        symbol="TCS",
        side=Side.BUY,
        qty=5,
        strategy_id="strat-a",
        status=OrderStatus.OPEN,
        created_at=datetime(2024, 1, 15, 9, 16),
    )
    order_b = Order(
        symbol="INFY",
        side=Side.BUY,
        qty=7,
        strategy_id="strat-b",
        status=OrderStatus.OPEN,
        created_at=datetime(2024, 1, 15, 9, 16),
    )
    store_a.save_order(order_a)
    store_b.save_order(order_b)

    fill_a = Fill(
        client_order_id=order_a.client_order_id,
        symbol="TCS",
        side=Side.BUY,
        qty=5,
        price=100.0,
        ts=datetime(2024, 1, 15, 9, 20),
        charges=1.5,
    )
    fill_b = Fill(
        client_order_id=order_b.client_order_id,
        symbol="INFY",
        side=Side.BUY,
        qty=7,
        price=200.0,
        ts=datetime(2024, 1, 15, 9, 20),
        charges=2.5,
    )
    store_a.record_fill(fill_a)
    store_b.record_fill(fill_b)

    store_a.snapshot_equity(datetime(2024, 1, 15, 15, 30), equity=100_500.0, cash=99_000.0)
    store_b.snapshot_equity(datetime(2024, 1, 15, 15, 30), equity=201_000.0, cash=199_000.0)

    # sanity: each store only ever sees its own rows
    assert len(store_a.orders()) == 1
    assert len(store_b.orders()) == 1
    assert len(store_a.all_fills()) == 1
    assert len(store_b.all_fills()) == 1

    store_a.reset()

    assert store_a.orders() == []
    assert store_a.all_fills() == []
    assert store_a.equity_curve().empty
    assert store_a.capital() is None

    # strat-b completely untouched by strat-a's reset
    assert len(store_b.orders()) == 1
    assert len(store_b.all_fills()) == 1
    assert not store_b.equity_curve().empty
    assert store_b.capital() == 200_000.0

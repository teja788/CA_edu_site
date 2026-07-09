"""Fill-simulation semantics for the event-driven engine.

Covers, with hand-computed expectations in comments:

* T+1 open fill: a signal at close(T) queues an order that fills at open(T+1)
  at ``open * (1 ± slip)`` — verified end-to-end through the engine.
* LIMIT crossing logic on both sides (fill / no-fill).
* Volume-participation cap splitting one large order across bars, remainder
  staying WORKING until filled.
* ``same_close`` timing filling against the same bar's close.
"""

from __future__ import annotations

from datetime import date, datetime, time

import pandas as pd
import pytest
from fixtures.synthetic import synthetic_universe

from tradingos.config.schemas import (
    ExecutionSpec,
    RebalanceSpec,
    ScoreSpec,
    SelectionSpec,
    SignalSpec,
    SizingSpec,
    StrategyConfig,
    UniverseSpec,
)
from tradingos.core.models import Order, OrderStatus, OrderType, Product, Side, Timeframe
from tradingos.costs.model import CostModel
from tradingos.engine.base import StaticUniverseResolver
from tradingos.engine.dataview import MarketData
from tradingos.engine.event.engine import EventEngine
from tradingos.engine.event.execution import ChargeCalculator, FillSimulator
from tradingos.strategies.registry import register_signal


@register_signal("test_engine_fill_close", tier="custom")
def _close_signal(df: pd.DataFrame, **params: object) -> pd.Series:
    """Rank purely by the latest close (causal: row t uses only close_t)."""
    return df["close"].astype("float64")

_TS = datetime(2021, 1, 4, 9, 15)


def _bar(open_: float, high: float, low: float, close: float, volume: int) -> pd.Series:
    return pd.Series(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume}
    )


def _open_order(symbol: str, side: Side, qty: int, order_type: OrderType, **kw: object) -> Order:
    order = Order(symbol=symbol, side=side, qty=qty, order_type=order_type, **kw)
    order.transition(OrderStatus.OPEN)  # accepted into the book
    return order


def _sim(slippage_bps: float = 25.0, max_participation: float = 0.05) -> FillSimulator:
    charges = ChargeCalculator(CostModel("zerodha_2026"), Product.CNC)
    return FillSimulator(charges, slippage_bps, max_participation, Product.CNC)


# ---------------------------------------------------------------------------
# MARKET fills at the reference price ± slippage
# ---------------------------------------------------------------------------


def test_market_buy_fills_at_open_plus_slippage() -> None:
    sim = _sim(slippage_bps=25.0, max_participation=1.0)
    order = _open_order("X", Side.BUY, 100, OrderType.MARKET)
    bar = _bar(100.00, 101.0, 99.0, 100.5, 1_000_000)

    fills = sim.execute([order], {"X": bar}, _TS, basis="open")

    # open 100.00 * (1 + 25/10000) = 100.25
    assert len(fills) == 1
    assert fills[0].price == pytest.approx(100.25)
    assert fills[0].qty == 100
    assert fills[0].ts == _TS
    assert order.status == OrderStatus.COMPLETE


def test_market_sell_receives_open_minus_slippage() -> None:
    sim = _sim(slippage_bps=25.0, max_participation=1.0)
    # a sell needs an open long to be meaningful downstream; the simulator itself
    # only prices/qtys the fill, so a bare order is fine here.
    order = _open_order("X", Side.SELL, 100, OrderType.MARKET)
    bar = _bar(200.00, 201.0, 199.0, 200.0, 1_000_000)

    fills = sim.execute([order], {"X": bar}, _TS, basis="open")

    # open 200.00 * (1 - 25/10000) = 199.50
    assert fills[0].price == pytest.approx(199.50)


def test_same_close_timing_fills_at_close() -> None:
    sim = _sim(slippage_bps=25.0, max_participation=1.0)
    order = _open_order("X", Side.BUY, 10, OrderType.MARKET)
    bar = _bar(100.00, 205.0, 95.0, 200.00, 1_000_000)

    fills = sim.execute([order], {"X": bar}, _TS, basis="close")

    # close 200.00 * (1 + 25/10000) = 200.50 (uses close, not open)
    assert fills[0].price == pytest.approx(200.50)


# ---------------------------------------------------------------------------
# LIMIT crossing
# ---------------------------------------------------------------------------


def test_buy_limit_fills_when_bar_trades_through_at_min_open_limit() -> None:
    sim = _sim(max_participation=1.0)
    order = _open_order("X", Side.BUY, 50, OrderType.LIMIT, limit_price=99.00)
    # low 98 <= limit 99 -> crossed; fill at min(open=100, limit=99) = 99.00
    bar = _bar(100.00, 101.0, 98.0, 100.0, 1_000_000)

    fills = sim.execute([order], {"X": bar}, _TS)

    assert fills[0].price == pytest.approx(99.00)
    assert order.status == OrderStatus.COMPLETE


def test_buy_limit_does_not_fill_when_not_crossed() -> None:
    sim = _sim(max_participation=1.0)
    order = _open_order("X", Side.BUY, 50, OrderType.LIMIT, limit_price=99.00)
    # low 99.5 > limit 99 -> not crossed
    bar = _bar(100.0, 101.0, 99.5, 100.5, 1_000_000)

    fills = sim.execute([order], {"X": bar}, _TS)

    assert fills == []
    assert order.status == OrderStatus.OPEN  # stays working


def test_sell_limit_fills_at_max_open_limit_when_crossed() -> None:
    sim = _sim(max_participation=1.0)
    order = _open_order("X", Side.SELL, 50, OrderType.LIMIT, limit_price=101.00)
    # high 101.5 >= limit 101 -> crossed; fill at max(open=100, limit=101) = 101.00
    bar = _bar(100.0, 101.5, 99.0, 100.0, 1_000_000)

    fills = sim.execute([order], {"X": bar}, _TS)

    assert fills[0].price == pytest.approx(101.00)


def test_sell_limit_does_not_fill_when_not_crossed() -> None:
    sim = _sim(max_participation=1.0)
    order = _open_order("X", Side.SELL, 50, OrderType.LIMIT, limit_price=101.00)
    bar = _bar(100.0, 100.5, 99.0, 100.0, 1_000_000)  # high 100.5 < 101

    assert sim.execute([order], {"X": bar}, _TS) == []
    assert order.status == OrderStatus.OPEN


# ---------------------------------------------------------------------------
# participation cap: one big order split across bars
# ---------------------------------------------------------------------------


def test_participation_cap_splits_order_and_remainder_stays_working() -> None:
    # max_participation 0.05, volume 1000 -> cap = floor(0.05 * 1000) = 50 per bar.
    sim = _sim(slippage_bps=0.0, max_participation=0.05)
    order = _open_order("X", Side.BUY, 120, OrderType.MARKET)

    bar1 = _bar(100.0, 101.0, 99.0, 100.0, 1_000)
    fills1 = sim.execute([order], {"X": bar1}, datetime(2021, 1, 4, 9, 15))
    # bar 1: fills 50, 70 remaining, order PARTIAL
    assert fills1[0].qty == 50
    assert order.filled_qty == 50
    assert order.remaining_qty == 70
    assert order.status == OrderStatus.PARTIAL

    bar2 = _bar(100.0, 101.0, 99.0, 100.0, 1_000)
    fills2 = sim.execute([order], {"X": bar2}, datetime(2021, 1, 5, 9, 15))
    # bar 2: fills another 50, 20 remaining, still PARTIAL
    assert fills2[0].qty == 50
    assert order.remaining_qty == 20
    assert order.status == OrderStatus.PARTIAL

    bar3 = _bar(100.0, 101.0, 99.0, 100.0, 1_000)
    fills3 = sim.execute([order], {"X": bar3}, datetime(2021, 1, 6, 9, 15))
    # bar 3: fills remaining 20, order COMPLETE
    assert fills3[0].qty == 20
    assert order.remaining_qty == 0
    assert order.status == OrderStatus.COMPLETE


# ---------------------------------------------------------------------------
# engine-level T+1 open semantics
# ---------------------------------------------------------------------------


def test_engine_entry_fills_at_next_open_price() -> None:
    """A rebalance at close(t0) fills at open(t1) = the next bar's open.

    Monthly cadence: AAA is bought at the January rebalance and — because there
    is no intervening rebalance to re-size the lot — it is filled EXACTLY once,
    at open(t1)=100.00. BBB overtakes it at the February rebalance, so AAA is
    sold and the round trip records the pristine entry VWAP.
    """
    dates = pd.date_range(date(2021, 1, 1), date(2021, 2, 28), freq="B")
    n = len(dates)
    jan = [d.month == 1 for d in dates]
    aaa_close = [200.0 if j else 50.0 for j in jan]  # top in Jan, laggard in Feb
    bbb_close = [100.0 if j else 300.0 for j in jan]  # laggard in Jan, top in Feb

    aaa_open = list(aaa_close)
    aaa_open[1] = 100.00  # open(t1): the fill price base -> 100.00 * 1.0025 = 100.25
    aaa = pd.DataFrame(
        {
            "open": aaa_open,
            "high": [c + 5 for c in aaa_close],
            "low": [min(o, c) - 5 for o, c in zip(aaa_open, aaa_close, strict=True)],
            "close": aaa_close,
            "volume": [10_000_000] * n,
        },
        index=dates,
    )
    bbb = pd.DataFrame(
        {
            "open": bbb_close,
            "high": [c + 5 for c in bbb_close],
            "low": [c - 5 for c in bbb_close],
            "close": bbb_close,
            "volume": [10_000_000] * n,
        },
        index=dates,
    )
    data = MarketData({"AAA": aaa, "BBB": bbb}, timeframe=Timeframe.DAY, snapshot_id="t1")

    cfg = StrategyConfig(
        name="t1_open",
        start=date(2021, 1, 1),
        end=date(2021, 2, 28),
        capital=1_000_000,
        universe=UniverseSpec(symbols=["AAA", "BBB"], point_in_time=False),
        signals=[SignalSpec(id="c", name="test_engine_fill_close")],
        score=ScoreSpec(type="single"),
        selection=SelectionSpec(method="top_n", n=1, exit_rank=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=1.0),
        rebalance=RebalanceSpec(frequency="monthly", trading_day=1),
        execution=ExecutionSpec(timing="next_open", slippage_bps=25.0, max_participation=1.0),
    )
    res = EventEngine().run(cfg, data, StaticUniverseResolver())

    aaa_trades = [t for t in res.trades if t.symbol == "AAA"]
    assert aaa_trades, "expected an AAA round-trip trade"
    first = aaa_trades[0]
    # entry filled at open(t1)=100.00 * (1 + 25/10000) = 100.25, stamped 09:15 of t1
    assert first.entry_price == pytest.approx(100.25)
    assert first.entry_ts.time() == time(9, 15)
    assert first.entry_ts.date() == dates[1].date()


def test_engine_is_deterministic_across_runs() -> None:
    data_frames = synthetic_universe(
        ["AAA", "BBB", "CCC"], start=date(2021, 1, 1), end=date(2021, 12, 31)
    )
    data = MarketData(data_frames, timeframe=Timeframe.DAY, snapshot_id="det")
    cfg = StrategyConfig(
        name="det",
        start=date(2021, 1, 1),
        end=date(2021, 12, 31),
        capital=1_000_000,
        universe=UniverseSpec(symbols=["AAA", "BBB", "CCC"], point_in_time=False),
        selection=SelectionSpec(method="top_n", n=1, exit_rank=2),
        sizing=SizingSpec(method="equal_weight", max_position_pct=1.0),
    )
    r1 = EventEngine().run(cfg, data, StaticUniverseResolver())
    r2 = EventEngine().run(cfg, data, StaticUniverseResolver())
    assert r1.equity.equals(r2.equity)
    assert r1.total_costs == r2.total_costs

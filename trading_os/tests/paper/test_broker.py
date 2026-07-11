"""Tests for paper/broker.py: PaperBroker.

One test class per modelling assumption documented in the module docstring
of ``tradingos.paper.broker`` (price arithmetic, LIMIT semantics, whole-order
fills, the BUY cash guard and SELL oversell guard with their working-order
reservations -- LIMIT and resting-MARKET both, the same-day-quote immediate-
match rule, the fill-time cash guard, SL/SL-M rejection, idempotency), plus
restart safety, the atomic fill+order persistence it depends on, the
queue/plan lifecycle with its per-order fault tolerance, the day-start equity
snapshot, CNC/MIS bucketing, modify/cancel and mark_to_market.

Deterministic throughout: hand-built ``core.models.Tick`` objects (never live
data) with an explicit ``slippage_bps`` so fill prices are pinned exactly, and
tz-naive IST timestamps on real trading days consistent with the rest of
``tests/paper/*.py`` (2024-01-15 Monday, 2024-01-16 Tuesday).

Time is fully controlled: every broker is constructed with a ``FakeClock``
injected as ``now_fn`` and pinned to the same day as its ticks, so
``created_at`` / ``updated_at`` / fill timestamps are asserted EXACTLY --
immediate fills stamp the clock's now, on_tick fills stamp the tick's ts.
Market-hours risk gating is bypassed everywhere via a permissive
``RiskLimits`` (``market_hours_only=False``) so no test depends on which
session hour the pinned clock names.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Literal

import pytest
from fixtures.ticks import synthetic_ticks

from tradingos.broker.killswitch import KillSwitch
from tradingos.broker.risk import RiskLimits
from tradingos.config.settings import Settings
from tradingos.core.alerts import TelegramAlerter
from tradingos.core.errors import BrokerError, KillSwitchActive, OrderStateError, RiskViolation
from tradingos.core.models import Fill, Order, OrderStatus, OrderType, Product, Side, Tick
from tradingos.core.timeutils import MARKET_OPEN
from tradingos.costs.model import CostModel
from tradingos.data.calendar import NSECalendar
from tradingos.paper.broker import PaperBroker
from tradingos.paper.ledgerdb import PaperStore

DAY0 = date(2024, 1, 15)  # Monday
DAY1 = date(2024, 1, 16)  # Tuesday
T0 = datetime(2024, 1, 15, 10, 0)  # default pinned "now" and first-tick time


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


class FakeClock:
    """Injectable ``now_fn`` for PaperBroker: every internal timestamp the
    broker stamps (place_order's now, updated_at, snapshot default) reads this
    clock, so tests advance time explicitly via ``clock.now = ...``."""

    def __init__(self, now: datetime = T0) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


def _permissive_limits(**overrides: object) -> RiskLimits:
    """Generous limits that never trip unless a test overrides a field to
    specifically exercise that rule. Isolates PaperBroker's OWN guards (cash,
    oversell, kill switch, SL/SL-M, idempotency, ...) from
    PreTradeRiskChecker's rules, which are already covered end to end by
    tests/broker/test_risk.py."""
    kwargs: dict[str, object] = dict(
        max_order_value=10_000_000.0,
        max_position_pct=1_000.0,  # effectively unlimited: 100,000% of equity
        max_daily_loss=10_000_000.0,
        max_orders_per_day=1_000,
        restricted_symbols=frozenset(),
        market_hours_only=False,
    )
    kwargs.update(overrides)
    return RiskLimits(**kwargs)  # type: ignore[arg-type]


def make_broker(
    settings: Settings,
    store: PaperStore,
    *,
    capital: float = 100_000.0,
    product: Product = Product.CNC,
    slippage_bps: float | None = 10.0,
    limit_fill_mode: Literal["touch", "cross"] = "touch",
    risk_limits: RiskLimits | None = None,
    kill_switch: KillSwitch | None = None,
    clock: FakeClock | None = None,
    enforce_market_hours: bool = False,
) -> PaperBroker:
    """A PaperBroker wired to an on-disk ``store``, a disabled TelegramAlerter,
    a fresh (non-engaged) file KillSwitch, permissive risk limits and a
    FakeClock pinned to T0 by default -- each test overrides only the knob it
    cares about. ``strategy_id`` is always taken from ``store`` so the two can
    never disagree."""
    return PaperBroker(
        settings,
        strategy_id=store.strategy_id,
        capital=capital,
        product=product,
        slippage_bps=slippage_bps,
        limit_fill_mode=limit_fill_mode,
        risk_limits=risk_limits or _permissive_limits(),
        kill_switch=kill_switch or KillSwitch(settings.kill_switch_path),
        calendar=NSECalendar(settings),
        alerter=TelegramAlerter(None, None),
        store=store,
        enforce_market_hours=enforce_market_hours,
        now_fn=clock or FakeClock(),
    )


def make_tick(
    symbol: str,
    ts: datetime,
    last: float,
    *,
    bid: float | None = None,
    ask: float | None = None,
    volume: int = 1_000,
    token: int = 1,
) -> Tick:
    return Tick(
        symbol=symbol, instrument_token=token, ts=ts, last_price=last, bid=bid, ask=ask, volume=volume
    )


# --------------------------------------------------------------------------
# 1. Market fill price arithmetic
# --------------------------------------------------------------------------


class TestMarketFillPriceArithmetic:
    def test_market_buy_fills_at_ask_times_one_plus_slippage(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "buy-ask")
        broker = make_broker(settings, store, slippage_bps=10.0)
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.15))

        broker.place_order(Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.MARKET))

        fill = store.all_fills()[-1]
        assert fill.price == round(100.15 * (1 + 10 / 10_000.0), 2)
        assert fill.ts == T0  # immediate fill stamps the injected clock's now

    def test_market_sell_fills_at_bid_times_one_minus_slippage(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "sell-bid")
        clock = FakeClock(T0)
        broker = make_broker(settings, store, slippage_bps=10.0, clock=clock)
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.1))
        broker.place_order(Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.MARKET))

        clock.now = datetime(2024, 1, 15, 10, 5)
        broker.on_tick(make_tick("AAA", clock.now, last=105.0, bid=104.85, ask=105.2))
        broker.place_order(Order(symbol="AAA", side=Side.SELL, qty=5, order_type=OrderType.MARKET))

        fill = store.all_fills()[-1]
        assert fill.price == round(104.85 * (1 - 10 / 10_000.0), 2)
        assert fill.ts == datetime(2024, 1, 15, 10, 5)

    def test_market_buy_falls_back_to_last_price_when_ask_is_none(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "buy-fallback")
        broker = make_broker(settings, store, slippage_bps=10.0)
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=None, ask=None))

        broker.place_order(Order(symbol="AAA", side=Side.BUY, qty=5, order_type=OrderType.MARKET))

        fill = store.all_fills()[-1]
        assert fill.price == round(100.0 * (1 + 10 / 10_000.0), 2)

    def test_market_sell_falls_back_to_last_price_when_bid_is_none(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "sell-fallback")
        broker = make_broker(settings, store, slippage_bps=10.0)
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.1))
        broker.place_order(Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.MARKET))

        broker.on_tick(make_tick("AAA", datetime(2024, 1, 15, 10, 5), last=105.0, bid=None, ask=None))
        broker.place_order(Order(symbol="AAA", side=Side.SELL, qty=5, order_type=OrderType.MARKET))

        fill = store.all_fills()[-1]
        assert fill.price == round(105.0 * (1 - 10 / 10_000.0), 2)

    def test_known_value_buy_price_paisa_rounding(self, settings: Settings, tmp_path: Path) -> None:
        """Hand-computed: 105.335 * 1.001 = 105.440335 -> rounds to 105.44."""
        store = PaperStore(tmp_path / "paper.sqlite", "rounding-buy")
        broker = make_broker(settings, store, slippage_bps=10.0)
        broker.on_tick(make_tick("AAA", T0, last=105.0, bid=104.9, ask=105.335))

        broker.place_order(Order(symbol="AAA", side=Side.BUY, qty=1, order_type=OrderType.MARKET))

        assert store.all_fills()[-1].price == 105.44

    def test_known_value_sell_price_paisa_rounding(self, settings: Settings, tmp_path: Path) -> None:
        """Hand-computed: 2489.995 * 0.999 = 2487.505005 -> rounds to 2487.51."""
        store = PaperStore(tmp_path / "paper.sqlite", "rounding-sell")
        broker = make_broker(settings, store, slippage_bps=10.0)
        broker.on_tick(make_tick("AAA", T0, last=2490.0, bid=2489.995, ask=2490.5))
        broker.place_order(Order(symbol="AAA", side=Side.BUY, qty=1, order_type=OrderType.MARKET))

        broker.place_order(Order(symbol="AAA", side=Side.SELL, qty=1, order_type=OrderType.MARKET))

        assert store.all_fills()[-1].price == 2487.51


# --------------------------------------------------------------------------
# 2. LIMIT semantics
# --------------------------------------------------------------------------


class TestLimitSemantics:
    def test_limit_buy_fills_at_limit_price_exactly_ignoring_slippage(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "limit-buy-exact")
        broker = make_broker(settings, store, slippage_bps=10.0)  # nonzero, on purpose
        broker.on_tick(make_tick("AAA", T0, last=95.0, bid=94.9, ask=95.1))

        order = broker.place_order(
            Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.LIMIT, limit_price=100.0)
        )

        assert order.status == OrderStatus.COMPLETE
        assert store.all_fills()[-1].price == 100.0

    def test_limit_sell_fills_at_limit_price_exactly_ignoring_slippage(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "limit-sell-exact")
        broker = make_broker(settings, store, slippage_bps=10.0)
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.1))
        broker.place_order(Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.MARKET))

        order = broker.place_order(
            Order(symbol="AAA", side=Side.SELL, qty=10, order_type=OrderType.LIMIT, limit_price=90.0)
        )

        assert order.status == OrderStatus.COMPLETE
        assert store.all_fills()[-1].price == 90.0

    def test_touch_mode_fills_buy_when_last_equals_limit(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "touch-eq")
        broker = make_broker(settings, store, limit_fill_mode="touch")
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.1))

        order = broker.place_order(
            Order(symbol="AAA", side=Side.BUY, qty=5, order_type=OrderType.LIMIT, limit_price=100.0)
        )

        assert order.status == OrderStatus.COMPLETE

    def test_cross_mode_does_not_fill_buy_when_last_equals_limit_but_fills_once_strictly_through(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "cross-eq")
        broker = make_broker(settings, store, limit_fill_mode="cross")
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.1))

        order = broker.place_order(
            Order(symbol="AAA", side=Side.BUY, qty=5, order_type=OrderType.LIMIT, limit_price=100.0)
        )
        assert order.status == OrderStatus.OPEN  # cross mode needs strictly through, not touch

        crossing_tick = make_tick("AAA", datetime(2024, 1, 15, 10, 5), last=99.0, bid=98.9, ask=99.1)
        fills = broker.on_tick(crossing_tick)

        assert len(fills) == 1
        assert fills[0].ts == crossing_tick.ts
        assert broker.get_order(order.client_order_id).status == OrderStatus.COMPLETE

    def test_non_marketable_limit_rests_open_then_fills_on_later_marketable_tick(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "rest-then-fill")
        broker = make_broker(settings, store)

        order = broker.place_order(
            Order(symbol="AAA", side=Side.BUY, qty=5, order_type=OrderType.LIMIT, limit_price=90.0)
        )
        assert order.status == OrderStatus.OPEN  # no quote at all yet

        non_marketable = make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.1)
        assert broker.on_tick(non_marketable) == []
        assert broker.get_order(order.client_order_id).status == OrderStatus.OPEN

        marketable = make_tick("AAA", datetime(2024, 1, 15, 10, 5), last=90.0, bid=89.9, ask=90.1)
        fills = broker.on_tick(marketable)

        assert len(fills) == 1
        assert fills[0].price == 90.0
        assert fills[0].ts == marketable.ts
        assert broker.get_order(order.client_order_id).status == OrderStatus.COMPLETE


# --------------------------------------------------------------------------
# 3. Whole-order fills only
# --------------------------------------------------------------------------


class TestWholeOrderFillsOnly:
    def test_limit_order_open_then_complete_with_full_qty_fill_and_order_persisted(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "whole-order")
        broker = make_broker(settings, store)

        order = broker.place_order(
            Order(symbol="AAA", side=Side.BUY, qty=7, order_type=OrderType.LIMIT, limit_price=90.0)
        )
        assert order.status == OrderStatus.OPEN
        assert order.filled_qty == 0
        assert store.get_order(order.client_order_id).status == OrderStatus.OPEN

        tick = make_tick("AAA", T0, last=90.0, bid=89.9, ask=90.1)
        fills = broker.on_tick(tick)

        assert len(fills) == 1
        assert fills[0].qty == 7  # whole order, no partial

        stored = store.get_order(order.client_order_id)
        assert stored.status == OrderStatus.COMPLETE
        assert stored.filled_qty == 7
        assert store.all_fills() == [fills[0]]

    def test_no_order_ever_reaches_partial_status(self, settings: Settings, tmp_path: Path) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "no-partial")
        broker = make_broker(settings, store)

        broker.place_order(
            Order(symbol="AAA", side=Side.BUY, qty=3, order_type=OrderType.LIMIT, limit_price=90.0)
        )
        broker.on_tick(make_tick("AAA", T0, last=90.0, bid=89.9, ask=90.1))

        statuses = {o.status for o in store.orders()}
        assert OrderStatus.PARTIAL not in statuses
        assert statuses == {OrderStatus.COMPLETE}


# --------------------------------------------------------------------------
# 4. Cash guard (BUY) and working-order reservations
# --------------------------------------------------------------------------


class TestCashGuard:
    def test_buy_exceeding_cash_rejected_and_raises(self, settings: Settings, tmp_path: Path) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "cash-guard")
        broker = make_broker(settings, store, capital=10_000.0, slippage_bps=10.0)
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.05))

        order = Order(symbol="AAA", side=Side.BUY, qty=1_000, order_type=OrderType.MARKET)
        with pytest.raises(RiskViolation, match="insufficient cash"):
            broker.place_order(order)

        stored = store.get_order(order.client_order_id)
        assert stored is not None
        assert stored.status == OrderStatus.REJECTED
        assert "insufficient cash" in (stored.status_message or "")
        assert store.all_fills() == []

    def test_resting_limit_buy_reservation_blocks_second_buy_that_would_otherwise_fit(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """900 shares @ limit 100 reserves ~90,106.76 of a 100,000 capital,
        leaving ~9,893.24 available. A second BUY costing ~10,021.88 fits
        gross cash (100,000) but not net of the first order's reservation."""
        store = PaperStore(tmp_path / "paper.sqlite", "cash-reservation")
        broker = make_broker(settings, store, capital=100_000.0, slippage_bps=10.0)

        first = broker.place_order(
            Order(symbol="AAA", side=Side.BUY, qty=900, order_type=OrderType.LIMIT, limit_price=100.0)
        )
        assert first.status == OrderStatus.OPEN  # no quote for AAA -> rests, reserving cash

        broker.on_tick(make_tick("BBB", T0, last=100.0, bid=99.9, ask=100.0))
        second = Order(symbol="BBB", side=Side.BUY, qty=100, order_type=OrderType.MARKET)

        with pytest.raises(RiskViolation, match="insufficient cash"):
            broker.place_order(second)

        assert store.get_order(second.client_order_id).status == OrderStatus.REJECTED

    def test_resting_market_buy_reservation_blocks_second_buy_that_would_otherwise_fit(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """A MARKET BUY resting on a stale quote reserves its latest-quote
        estimate: 900 shares at ask 100 * (1+10bps) = 100.1 -> ~90,196.87
        reserved of 100,000, leaving ~9,803.13. A second BUY costing ~9,921.65
        fits gross cash but not net of that reservation."""
        store = PaperStore(tmp_path / "paper.sqlite", "market-reservation")
        clock = FakeClock(T0)
        broker = make_broker(settings, store, capital=100_000.0, slippage_bps=10.0, clock=clock)
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.0))
        broker.on_tick(make_tick("BBB", T0, last=100.0, bid=99.9, ask=100.0))

        clock.now = datetime(2024, 1, 16, 9, 16)  # both quotes are now stale (yesterday's)
        first = broker.place_order(
            Order(symbol="AAA", side=Side.BUY, qty=900, order_type=OrderType.MARKET)
        )
        assert first.status == OrderStatus.OPEN  # stale quote -> rests, reserving its estimate

        second = Order(symbol="BBB", side=Side.BUY, qty=99, order_type=OrderType.MARKET)
        with pytest.raises(RiskViolation, match="insufficient cash"):
            broker.place_order(second)

        assert store.get_order(second.client_order_id).status == OrderStatus.REJECTED
        assert store.all_fills() == []


# --------------------------------------------------------------------------
# 5. Oversell guard (SELL, long-only CNC)
# --------------------------------------------------------------------------


class TestOversellGuard:
    def test_sell_without_any_holding_rejected(self, settings: Settings, tmp_path: Path) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "oversell-simple")
        broker = make_broker(settings, store)
        # a quote is needed so the MARKET order reaches the oversell check
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.1))

        order = Order(symbol="AAA", side=Side.SELL, qty=1, order_type=OrderType.MARKET)
        with pytest.raises(RiskViolation, match="oversell"):
            broker.place_order(order)

        assert store.get_order(order.client_order_id).status == OrderStatus.REJECTED

    def test_resting_sell_reservation_blocks_second_sell_of_even_one_share(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "oversell-reservation")
        broker = make_broker(settings, store, capital=100_000.0)
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.1))
        broker.place_order(Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.MARKET))

        resting_sell = broker.place_order(
            Order(symbol="AAA", side=Side.SELL, qty=10, order_type=OrderType.LIMIT, limit_price=200.0)
        )
        assert resting_sell.status == OrderStatus.OPEN  # 200 > last(100) -> not marketable

        second = Order(symbol="AAA", side=Side.SELL, qty=1, order_type=OrderType.MARKET)
        with pytest.raises(RiskViolation, match="oversell"):
            broker.place_order(second)

        assert store.get_order(second.client_order_id).status == OrderStatus.REJECTED


# --------------------------------------------------------------------------
# 6. SL / SL-M unsupported
# --------------------------------------------------------------------------


class TestStopOrdersUnsupported:
    @pytest.mark.parametrize("order_type", [OrderType.SL, OrderType.SL_M])
    def test_sl_orders_rejected_without_raising(
        self, settings: Settings, tmp_path: Path, order_type: OrderType
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", f"stop-{order_type.value}")
        broker = make_broker(settings, store)
        order = Order(
            symbol="AAA",
            side=Side.BUY,
            qty=10,
            order_type=order_type,
            trigger_price=95.0,
            limit_price=96.0 if order_type == OrderType.SL else None,
        )

        result = broker.place_order(order)  # must NOT raise

        assert result.status == OrderStatus.REJECTED
        assert result.status_message == "not supported in paper"
        stored = store.get_order(order.client_order_id)
        assert stored is not None
        assert stored.status == OrderStatus.REJECTED
        assert stored.status_message == "not supported in paper"


# --------------------------------------------------------------------------
# 7. Kill switch
# --------------------------------------------------------------------------


class TestKillSwitchEngaged:
    def test_place_order_persists_rejected_and_raises(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "kill-switch")
        ks = KillSwitch(tmp_path / "KILL_SWITCH")
        ks.engage("manual halt")
        broker = make_broker(settings, store, kill_switch=ks)

        order = Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.LIMIT, limit_price=100.0)
        with pytest.raises(KillSwitchActive, match="manual halt"):
            broker.place_order(order)

        stored = store.get_order(order.client_order_id)
        assert stored is not None
        assert stored.status == OrderStatus.REJECTED
        assert "manual halt" in (stored.status_message or "")


# --------------------------------------------------------------------------
# 8. Pre-trade risk violation
# --------------------------------------------------------------------------


class TestRiskViolationRejection:
    def test_max_order_value_exceeded_persists_rejected_and_raises(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "risk-violation")
        broker = make_broker(settings, store, risk_limits=_permissive_limits(max_order_value=100.0))

        order = Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.LIMIT, limit_price=1_000.0)
        with pytest.raises(RiskViolation, match="order value"):
            broker.place_order(order)

        stored = store.get_order(order.client_order_id)
        assert stored is not None
        assert stored.status == OrderStatus.REJECTED
        assert "order value" in (stored.status_message or "")


# --------------------------------------------------------------------------
# 9. Idempotency
# --------------------------------------------------------------------------


class TestIdempotency:
    def test_replace_after_fill_returns_stored_order_without_double_filling(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "idempotency")
        broker = make_broker(settings, store)
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.1))

        cid = "fixed-client-order-id"
        # strategy_id set to match the store: PaperStore always stamps its OWN
        # strategy_id onto a row it persists (regardless of what the Order
        # object carried), so setting it here up front keeps `first` -- never
        # itself round-tripped through the store -- comparable field-for-field
        # to `second`, which IS the store-persisted row.
        first = broker.place_order(
            Order(
                client_order_id=cid,
                symbol="AAA",
                side=Side.BUY,
                qty=10,
                order_type=OrderType.MARKET,
                strategy_id=store.strategy_id,
            )
        )
        assert first.status == OrderStatus.COMPLETE
        assert first.created_at == T0  # stamped from the injected clock

        equity_after_first = broker.equity()
        fills_after_first = len(store.all_fills())

        # A fresh Order instance carrying the same client_order_id, as a
        # caller retrying after a crash/timeout would construct.
        retry = Order(
            client_order_id=cid,
            symbol="AAA",
            side=Side.BUY,
            qty=10,
            order_type=OrderType.MARKET,
            strategy_id=store.strategy_id,
        )
        second = broker.place_order(retry)

        assert second.status == OrderStatus.COMPLETE
        assert second == first
        assert broker.equity() == pytest.approx(equity_after_first)
        assert len(store.all_fills()) == fills_after_first


# --------------------------------------------------------------------------
# 10. MARKET order before any quote
# --------------------------------------------------------------------------


class TestNoQuoteGuard:
    def test_market_order_before_any_quote_raises_and_persists_nothing(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "no-quote")
        broker = make_broker(settings, store)

        order = Order(symbol="NEVERTICKED", side=Side.BUY, qty=5, order_type=OrderType.MARKET)
        with pytest.raises(BrokerError, match="no price reference"):
            broker.place_order(order)

        assert store.get_order(order.client_order_id) is None
        assert store.orders() == []


# --------------------------------------------------------------------------
# 10b. Stale (previous-day) quote handling
# --------------------------------------------------------------------------


class TestStaleQuoteHandling:
    def test_market_order_on_stale_quote_rests_open_and_fills_on_new_days_tick_at_that_ticks_price(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """Immediate matching requires a SAME-DAY quote: a MARKET order placed
        while the last quote is yesterday's is accepted OPEN (never priced off
        the stale quote) and fills on the day's first tick at THAT tick's
        price -- the paper analogue of 'at the open' across an overnight gap."""
        store = PaperStore(tmp_path / "paper.sqlite", "stale-rests")
        clock = FakeClock(T0)
        broker = make_broker(settings, store, slippage_bps=10.0, clock=clock)
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.1))  # day0 quote

        placement_time = datetime(2024, 1, 16, 9, 16)
        clock.now = placement_time  # day1: the day0 quote is now stale
        order = broker.place_order(Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.MARKET))

        assert order.status == OrderStatus.OPEN  # accepted, NOT filled off yesterday's quote
        assert order.created_at == placement_time
        assert store.all_fills() == []
        assert store.get_order(order.client_order_id).status == OrderStatus.OPEN

        day1_tick = make_tick("AAA", datetime(2024, 1, 16, 9, 17), last=110.0, bid=109.9, ask=110.2)
        fills = broker.on_tick(day1_tick)

        assert len(fills) == 1
        assert fills[0].price == round(110.2 * (1 + 10 / 10_000.0), 2)  # the NEW day's ask
        assert fills[0].ts == day1_tick.ts
        assert broker.get_order(order.client_order_id).status == OrderStatus.COMPLETE

    def test_stale_quote_still_serves_as_pre_trade_risk_reference_not_a_broker_error(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """A stale quote does NOT trigger the no-price-reference BrokerError --
        it is still the best estimate for the pre-trade checks. Proven by an
        order-value violation computed off the stale last price."""
        store = PaperStore(tmp_path / "paper.sqlite", "stale-reference")
        clock = FakeClock(T0)
        broker = make_broker(
            settings, store, clock=clock, risk_limits=_permissive_limits(max_order_value=500.0)
        )
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.1))  # day0 quote

        clock.now = datetime(2024, 1, 16, 9, 16)  # day1: quote is stale
        # 10 * stale last(100) = 1000 > 500 -> the risk rule fired, meaning the
        # stale quote WAS accepted as the reference (no BrokerError raised).
        order = Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.MARKET)
        with pytest.raises(RiskViolation, match="order value"):
            broker.place_order(order)

        assert store.get_order(order.client_order_id).status == OrderStatus.REJECTED


# --------------------------------------------------------------------------
# 10c. Fill-time cash guard
# --------------------------------------------------------------------------


class TestFillTimeCashGuard:
    def test_gap_up_past_the_pre_trade_estimate_rejects_at_fill_time_and_cash_stays_untouched(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """A MARKET BUY accepted near the cash limit on a stale quote, then a
        big overnight gap-up: the actual cost at match time exceeds cash, so
        the order is REJECTED at fill time ('insufficient cash at fill'), no
        fill happens, cash is unchanged and created_at is PRESERVED (only
        updated_at/status change)."""
        store = PaperStore(tmp_path / "paper.sqlite", "fill-time-guard")
        clock = FakeClock(T0)
        broker = make_broker(settings, store, capital=10_000.0, slippage_bps=10.0, clock=clock)
        broker.on_tick(make_tick("AAA", T0, last=95.0, bid=94.9, ask=95.0))  # day0 quote

        placement_time = datetime(2024, 1, 16, 9, 16)
        clock.now = placement_time
        # estimate at stale ask: 100 * 95 * 1.001 + charges ~= 9,521 <= 10,000 -> accepted
        order = broker.place_order(Order(symbol="AAA", side=Side.BUY, qty=100, order_type=OrderType.MARKET))
        assert order.status == OrderStatus.OPEN

        # gap-up: 100 * 105 * 1.001 ~= 10,511 > 10,000 cash -> reject at fill time
        gap_tick = make_tick("AAA", datetime(2024, 1, 16, 9, 17), last=105.0, bid=104.9, ask=105.0)
        fills = broker.on_tick(gap_tick)

        assert fills == []
        stored = store.get_order(order.client_order_id)
        assert stored.status == OrderStatus.REJECTED
        assert "insufficient cash at fill" in (stored.status_message or "")
        assert stored.created_at == placement_time  # PRESERVED, not re-stamped
        assert stored.updated_at == gap_tick.ts  # stamped at the failed match
        assert store.all_fills() == []
        assert broker.get_margins().cash_available == pytest.approx(10_000.0)  # never went negative

        # the rejected order is out of the working set: a later affordable
        # tick must not resurrect it.
        cheap_tick = make_tick("AAA", datetime(2024, 1, 16, 9, 18), last=90.0, bid=89.9, ask=90.0)
        assert broker.on_tick(cheap_tick) == []
        assert store.get_order(order.client_order_id).status == OrderStatus.REJECTED


# --------------------------------------------------------------------------
# 11. Restart safety
# --------------------------------------------------------------------------


class TestRestartSafety:
    def test_restart_reconstructs_cash_equity_holdings_and_refills_resting_order_once(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "restart-strat")
        broker1 = make_broker(settings, store, capital=100_000.0, clock=FakeClock(T0))

        broker1.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.1))
        buy = broker1.place_order(Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.MARKET))
        assert buy.status == OrderStatus.COMPLETE

        resting = broker1.place_order(
            Order(symbol="AAA", side=Side.SELL, qty=4, order_type=OrderType.LIMIT, limit_price=150.0)
        )
        assert resting.status == OrderStatus.OPEN  # 150 > last(100) -> not marketable yet

        cash_before = broker1.get_margins().cash_available
        holdings_before = broker1.get_holdings()
        assert len(holdings_before) == 1
        fills_before_restart = len(store.all_fills())

        broker2 = make_broker(
            settings, store, capital=100_000.0, clock=FakeClock(datetime(2024, 1, 15, 10, 5))
        )

        assert broker2.get_margins().cash_available == pytest.approx(cash_before)
        holdings_after = broker2.get_holdings()
        assert len(holdings_after) == 1
        assert holdings_after[0].symbol == holdings_before[0].symbol
        assert holdings_after[0].qty == holdings_before[0].qty
        assert holdings_after[0].avg_price == pytest.approx(holdings_before[0].avg_price)

        # re-mark both brokers identically before comparing equity
        remark = make_tick("AAA", datetime(2024, 1, 15, 10, 5), last=105.0, bid=104.9, ask=105.1)
        broker1.on_tick(remark)
        broker2.on_tick(remark)
        assert broker2.equity() == pytest.approx(broker1.equity())

        reloaded = broker2.get_order(resting.client_order_id)
        assert reloaded.status == OrderStatus.OPEN  # the resting order survived the restart

        marketable = make_tick("AAA", datetime(2024, 1, 15, 10, 10), last=150.0, bid=149.9, ask=150.1)
        fills = broker2.on_tick(marketable)

        assert len(fills) == 1
        assert fills[0].client_order_id == resting.client_order_id
        assert fills[0].qty == 4
        assert fills[0].ts == marketable.ts
        final = broker2.get_order(resting.client_order_id)
        assert final.status == OrderStatus.COMPLETE
        assert final.filled_qty == 4
        assert len(store.all_fills()) == fills_before_restart + 1  # exactly one new fill


# --------------------------------------------------------------------------
# 12. Atomic fill + order persistence (PaperStore.record_fill_and_order)
# --------------------------------------------------------------------------


class TestAtomicFillPersistence:
    def test_record_fill_and_order_persists_both_rows_in_one_call(self, tmp_path: Path) -> None:
        store = PaperStore(tmp_path / "atomic.sqlite", "atomic-strat")
        order = Order(
            client_order_id="atomic-1",
            symbol="TCS",
            side=Side.BUY,
            qty=10,
            order_type=OrderType.MARKET,
            status=OrderStatus.OPEN,
            created_at=datetime(2024, 1, 15, 10, 0),
            updated_at=datetime(2024, 1, 15, 10, 0),
        )
        store.save_order(order)  # as place_order would have, before any fill

        order.filled_qty = 10
        order.transition(OrderStatus.COMPLETE)
        order.updated_at = datetime(2024, 1, 15, 10, 0, 1)
        fill = Fill(
            client_order_id="atomic-1",
            symbol="TCS",
            side=Side.BUY,
            qty=10,
            price=100.0,
            ts=datetime(2024, 1, 15, 10, 0, 1),
            charges=5.0,
            product=Product.CNC,
        )

        store.record_fill_and_order(fill, order)

        stored_order = store.get_order("atomic-1")
        assert stored_order is not None
        assert stored_order.status == OrderStatus.COMPLETE
        assert stored_order.filled_qty == 10
        assert store.all_fills() == [fill]

    def test_record_fill_and_order_rolls_back_both_rows_on_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        store = PaperStore(tmp_path / "atomic2.sqlite", "atomic-strat-2")
        order = Order(
            client_order_id="atomic-2",
            symbol="TCS",
            side=Side.BUY,
            qty=5,
            filled_qty=5,
            order_type=OrderType.MARKET,
            status=OrderStatus.COMPLETE,
            created_at=datetime(2024, 1, 15, 10, 0),
            updated_at=datetime(2024, 1, 15, 10, 0),
        )
        fill = Fill(
            client_order_id="atomic-2",
            symbol="TCS",
            side=Side.BUY,
            qty=5,
            price=100.0,
            ts=datetime(2024, 1, 15, 10, 0),
            charges=5.0,
            product=Product.CNC,
        )

        def boom(*args: object, **kwargs: object) -> None:
            raise RuntimeError("simulated crash mid-transaction")

        monkeypatch.setattr(store, "_upsert_order_row", boom)

        with pytest.raises(RuntimeError, match="simulated crash"):
            store.record_fill_and_order(fill, order)

        # the whole transaction rolled back: the fill row must NOT be
        # committed either, or a restart replay would double-apply it.
        assert store.all_fills() == []
        assert store.get_order("atomic-2") is None


# --------------------------------------------------------------------------
# 13. queue_for_open / place_planned
# --------------------------------------------------------------------------


class TestQueueForOpenAndPlacePlanned:
    def test_queued_order_is_pending_excluded_from_count_then_placed_at_open_fills(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "queue-strat")
        clock = FakeClock(datetime(2024, 1, 15, 15, 45))  # queued after day0's close
        broker = make_broker(settings, store, clock=clock)

        order = Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.MARKET)
        queued = broker.queue_for_open(order, on_day=DAY1)
        assert queued.status == OrderStatus.PENDING
        assert queued.created_at is None

        stored = store.get_order(order.client_order_id)
        assert stored is not None
        assert stored.status == OrderStatus.PENDING
        assert stored.created_at is None
        assert store.planned_orders(DAY1) == [stored]
        # PENDING orders are excluded from orders_placed_count on any day
        assert store.orders_placed_count(DAY0) == 0
        assert store.orders_placed_count(DAY1) == 0

        # next morning: a fresh day1 quote arrives, then the queue is placed
        placement_time = datetime(2024, 1, 16, 9, 15, 30)
        clock.now = placement_time
        day1_tick = make_tick("AAA", datetime(2024, 1, 16, 9, 15, 15), last=100.0, bid=99.9, ask=100.1)
        broker.on_tick(day1_tick)

        placed = broker.place_planned(DAY1)

        assert len(placed) == 1
        result = placed[0]
        assert result.status == OrderStatus.COMPLETE
        # created_at is stamped at the moment of PLACEMENT (exactly the
        # injected clock), i.e. the placement day -- not the day0 queue day.
        assert result.created_at == placement_time
        assert result.created_at.date() == DAY1
        assert store.all_fills()[-1].ts == placement_time
        assert store.planned_orders(DAY1) == []  # no longer pending
        assert store.orders_placed_count(DAY1) == 1
        assert store.orders_placed_count(DAY0) == 0  # queue day stays at zero


class TestPlacePlannedFaultTolerance:
    def test_middle_planned_order_risk_violation_does_not_abort_the_rest(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "planned-fault")
        clock = FakeClock(datetime(2024, 1, 15, 15, 45))
        broker = make_broker(
            settings, store, clock=clock, risk_limits=_permissive_limits(max_order_value=50_000.0)
        )
        o1 = Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.LIMIT, limit_price=100.0)
        o2 = Order(symbol="BBB", side=Side.BUY, qty=100, order_type=OrderType.LIMIT, limit_price=1_000.0)
        o3 = Order(symbol="CCC", side=Side.BUY, qty=5, order_type=OrderType.LIMIT, limit_price=100.0)
        for o in (o1, o2, o3):
            broker.queue_for_open(o, on_day=DAY1)

        clock.now = datetime(2024, 1, 16, 9, 16)
        placed = broker.place_planned(DAY1)  # must NOT raise despite o2's violation

        # o2 (100 * 1000 = 100,000 > 50,000) was skipped; the other two placed.
        assert [p.client_order_id for p in placed] == [o1.client_order_id, o3.client_order_id]
        assert store.get_order(o1.client_order_id).status == OrderStatus.OPEN
        assert store.get_order(o3.client_order_id).status == OrderStatus.OPEN
        rejected = store.get_order(o2.client_order_id)
        assert rejected.status == OrderStatus.REJECTED
        assert "order value" in (rejected.status_message or "")
        assert store.planned_orders(DAY1) == []  # nothing left pending

    def test_planned_market_order_with_no_quote_stays_pending_for_retry(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "planned-retry")
        clock = FakeClock(datetime(2024, 1, 15, 15, 45))
        broker = make_broker(settings, store, clock=clock)
        market = Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.MARKET)
        limit = Order(symbol="BBB", side=Side.BUY, qty=5, order_type=OrderType.LIMIT, limit_price=100.0)
        broker.queue_for_open(market, on_day=DAY1)
        broker.queue_for_open(limit, on_day=DAY1)

        clock.now = datetime(2024, 1, 16, 9, 15, 30)
        placed = broker.place_planned(DAY1)  # no quote for AAA yet -> BrokerError, skipped

        assert [p.client_order_id for p in placed] == [limit.client_order_id]
        assert store.get_order(market.client_order_id).status == OrderStatus.PENDING
        assert store.get_order(limit.client_order_id).status == OrderStatus.OPEN
        assert [o.client_order_id for o in store.planned_orders(DAY1)] == [market.client_order_id]

        # once a (same-day) quote exists, a retry places and fills it
        clock.now = datetime(2024, 1, 16, 9, 16)
        broker.on_tick(make_tick("AAA", datetime(2024, 1, 16, 9, 15, 45), last=100.0, bid=99.9, ask=100.1))
        retried = broker.place_planned(DAY1)

        assert [p.client_order_id for p in retried] == [market.client_order_id]
        assert store.get_order(market.client_order_id).status == OrderStatus.COMPLETE
        assert store.planned_orders(DAY1) == []

    def test_kill_switch_halts_place_planned_leaving_remaining_orders_pending(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "planned-killed")
        ks = KillSwitch(tmp_path / "KILL_SWITCH")
        clock = FakeClock(datetime(2024, 1, 15, 15, 45))
        broker = make_broker(settings, store, kill_switch=ks, clock=clock)
        o1 = Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.LIMIT, limit_price=100.0)
        o2 = Order(symbol="BBB", side=Side.BUY, qty=5, order_type=OrderType.LIMIT, limit_price=100.0)
        broker.queue_for_open(o1, on_day=DAY1)
        broker.queue_for_open(o2, on_day=DAY1)

        ks.engage("overnight halt")
        clock.now = datetime(2024, 1, 16, 9, 16)
        placed = broker.place_planned(DAY1)  # must swallow KillSwitchActive, not raise

        assert placed == []
        # the order being processed when the switch tripped is REJECTED...
        assert store.get_order(o1.client_order_id).status == OrderStatus.REJECTED
        # ...and the loop stopped: the rest stay PENDING for a later retry.
        assert store.get_order(o2.client_order_id).status == OrderStatus.PENDING
        assert [o.client_order_id for o in store.planned_orders(DAY1)] == [o2.client_order_id]


# --------------------------------------------------------------------------
# 14. Day-start equity snapshot
# --------------------------------------------------------------------------


class TestDayStartEquitySnapshot:
    def test_snapshot_written_once_before_same_tick_fill_and_survives_a_mid_day_restart(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "day-start")
        broker1 = make_broker(
            settings, store, capital=50_000.0, clock=FakeClock(datetime(2024, 1, 15, 9, 18))
        )

        # A resting LIMIT BUY placed before any quote: its fill (from the very
        # first day0 tick below) must NOT be reflected in day0's snapshot.
        broker1.place_order(
            Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.LIMIT, limit_price=100.0)
        )
        day0_tick = make_tick("AAA", datetime(2024, 1, 15, 9, 20), last=100.0, bid=99.9, ask=100.1)
        fills = broker1.on_tick(day0_tick)
        assert len(fills) == 1  # the resting order filled on this very tick

        curve = store.equity_curve()
        day0_rows = curve[[ts.date() == DAY0 for ts in curve.index]]
        assert len(day0_rows) == 1
        assert day0_rows.index[0] == datetime.combine(DAY0, MARKET_OPEN)
        assert day0_rows.iloc[0] == pytest.approx(50_000.0)  # BEFORE this tick's own fill

        buy_charges = CostModel("zerodha_2026").order_charges(Side.BUY, Product.CNC, 1_000.0).total
        cash_after_day0 = round(50_000.0 - (1_000.0 + buy_charges), 2)

        # First activity of day1: the mark IS applied before the snapshot, so
        # the day1 baseline reflects that new opening mark.
        day1_first_tick = make_tick("AAA", datetime(2024, 1, 16, 9, 20), last=110.0, bid=109.9, ask=110.1)
        broker1.on_tick(day1_first_tick)
        expected_day1_snapshot = round(cash_after_day0 + 10 * 110.0, 2)

        curve = store.equity_curve()
        day1_rows = curve[[ts.date() == DAY1 for ts in curve.index]]
        assert len(day1_rows) == 1
        assert day1_rows.iloc[0] == pytest.approx(expected_day1_snapshot)

        # more same-day activity with a big mark move must not touch the snapshot
        day1_later_tick = make_tick("AAA", datetime(2024, 1, 16, 12, 0), last=500.0, bid=499.0, ask=501.0)
        broker1.on_tick(day1_later_tick)
        curve = store.equity_curve()
        day1_rows = curve[[ts.date() == DAY1 for ts in curve.index]]
        assert len(day1_rows) == 1
        assert day1_rows.iloc[0] == pytest.approx(expected_day1_snapshot)
        assert broker1.equity() != pytest.approx(expected_day1_snapshot)  # live equity DID move

        # restart mid-day1: must recognise the existing snapshot and not
        # overwrite it on the next tick.
        broker2 = make_broker(
            settings, store, capital=50_000.0, clock=FakeClock(datetime(2024, 1, 16, 13, 0))
        )
        day1_after_restart_tick = make_tick(
            "AAA", datetime(2024, 1, 16, 14, 0), last=600.0, bid=599.0, ask=601.0
        )
        broker2.on_tick(day1_after_restart_tick)

        curve = store.equity_curve()
        day1_rows = curve[[ts.date() == DAY1 for ts in curve.index]]
        assert len(day1_rows) == 1
        assert day1_rows.iloc[0] == pytest.approx(expected_day1_snapshot)


# --------------------------------------------------------------------------
# 15. CNC vs MIS bucket semantics
# --------------------------------------------------------------------------


class TestProductBuckets:
    def test_cnc_lands_in_holdings_not_positions(self, settings: Settings, tmp_path: Path) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "bucket-cnc")
        broker = make_broker(settings, store, product=Product.CNC)
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.1))

        broker.place_order(
            Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.MARKET, product=Product.CNC)
        )

        assert len(broker.get_holdings()) == 1
        assert broker.get_positions() == []

    def test_mis_lands_in_positions_not_holdings(self, settings: Settings, tmp_path: Path) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "bucket-mis")
        broker = make_broker(settings, store, product=Product.MIS)
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.1))

        broker.place_order(
            Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.MARKET, product=Product.MIS)
        )

        assert len(broker.get_positions()) == 1
        assert broker.get_holdings() == []


# --------------------------------------------------------------------------
# 16. modify_order / cancel_order
# --------------------------------------------------------------------------


class TestModifyAndCancelOrder:
    def test_modify_limit_order_updates_fields_and_the_live_working_copy(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "modify-basic")
        broker = make_broker(settings, store)
        order = broker.place_order(
            Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.LIMIT, limit_price=90.0)
        )
        assert order.status == OrderStatus.OPEN

        modified = broker.modify_order(order.client_order_id, qty=5, limit_price=120.0)
        assert modified.qty == 5
        assert modified.limit_price == 120.0
        stored = store.get_order(order.client_order_id)
        assert stored.qty == 5
        assert stored.limit_price == 120.0

        # last=110 would NOT have crossed the original limit(90) but DOES cross
        # the modified one(120) in touch mode: proves the live working copy,
        # not just the stored row, picked up the modification.
        tick = make_tick("AAA", T0, last=110.0, bid=109.9, ask=110.1)
        fills = broker.on_tick(tick)

        assert len(fills) == 1
        assert fills[0].qty == 5
        assert fills[0].price == 120.0

    def test_modify_terminal_order_raises_order_state_error(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "modify-terminal")
        broker = make_broker(settings, store)
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.1))
        order = broker.place_order(Order(symbol="AAA", side=Side.BUY, qty=1, order_type=OrderType.MARKET))
        assert order.status == OrderStatus.COMPLETE

        with pytest.raises(OrderStateError):
            broker.modify_order(order.client_order_id, qty=2)

    def test_modify_non_limit_order_raises_broker_error(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "modify-non-limit")
        broker = make_broker(settings, store)
        # An OPEN MARKET order in the store (e.g. one resting on a stale quote)
        # must refuse modification: inject one directly to isolate the branch.
        stray = Order(
            symbol="AAA",
            side=Side.BUY,
            qty=1,
            order_type=OrderType.MARKET,
            status=OrderStatus.OPEN,
            created_at=datetime(2024, 1, 15, 10, 0),
        )
        store.save_order(stray)

        with pytest.raises(BrokerError, match="only LIMIT orders"):
            broker.modify_order(stray.client_order_id, qty=2)

    def test_modify_unknown_order_raises_broker_error(self, settings: Settings, tmp_path: Path) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "modify-unknown")
        broker = make_broker(settings, store)

        with pytest.raises(BrokerError, match="unknown order"):
            broker.modify_order("does-not-exist", qty=1)

    def test_cancel_open_limit_order_removes_it_from_the_working_set(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "cancel-basic")
        broker = make_broker(settings, store)
        order = broker.place_order(
            Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.LIMIT, limit_price=100.0)
        )
        assert order.status == OrderStatus.OPEN

        cancelled = broker.cancel_order(order.client_order_id)
        assert cancelled.status == OrderStatus.CANCELLED
        assert store.get_order(order.client_order_id).status == OrderStatus.CANCELLED

        # a tick that would have filled it, had it still been working, must not.
        tick = make_tick("AAA", T0, last=90.0, bid=89.9, ask=90.1)
        fills = broker.on_tick(tick)

        assert fills == []
        assert store.get_order(order.client_order_id).status == OrderStatus.CANCELLED

    def test_cancel_terminal_order_raises_order_state_error(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "cancel-terminal")
        broker = make_broker(settings, store)
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.1))
        order = broker.place_order(Order(symbol="AAA", side=Side.BUY, qty=1, order_type=OrderType.MARKET))
        assert order.status == OrderStatus.COMPLETE

        with pytest.raises(OrderStateError):
            broker.cancel_order(order.client_order_id)

    def test_cancel_unknown_order_raises_broker_error(self, settings: Settings, tmp_path: Path) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "cancel-unknown")
        broker = make_broker(settings, store)

        with pytest.raises(BrokerError, match="unknown order"):
            broker.cancel_order("does-not-exist")


# --------------------------------------------------------------------------
# 17. DP-charge warm-up on restart
# --------------------------------------------------------------------------


class TestDPChargeWarmUpAcrossRestart:
    def test_second_same_day_sell_after_restart_does_not_repeat_the_dp_charge(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """The DP (depository participant) charge applies once per scrip per
        settlement day, sell side only. ``_warm_charges`` must restore the
        "already sold today" bookkeeping from stored fills on restart so a
        second same-day sell of a scrip already sold before the restart is
        NOT charged DP twice. Both brokers' clocks are pinned to DAY0, so
        both sells land on the same (fully controlled) day."""
        store = PaperStore(tmp_path / "paper.sqlite", "dp-warmup")
        broker1 = make_broker(
            settings, store, capital=200_000.0, slippage_bps=0.0, clock=FakeClock(T0)
        )
        broker1.on_tick(make_tick("AAA", T0, last=100.0, bid=100.0, ask=100.0))
        broker1.place_order(Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.MARKET))
        sell1 = broker1.place_order(Order(symbol="AAA", side=Side.SELL, qty=5, order_type=OrderType.MARKET))
        assert sell1.status == OrderStatus.COMPLETE
        fill1 = store.all_fills()[-1]
        assert fill1.ts == T0

        # restart later the same day: a fresh broker over the same store must
        # warm the DP bookkeeping from the stored fills.
        restart_time = datetime(2024, 1, 15, 11, 0)
        broker2 = make_broker(
            settings, store, capital=200_000.0, slippage_bps=0.0, clock=FakeClock(restart_time)
        )
        # in-memory quotes are not persisted -- re-supply a same-day one
        broker2.on_tick(make_tick("AAA", restart_time, last=100.0, bid=100.0, ask=100.0))
        sell2 = broker2.place_order(Order(symbol="AAA", side=Side.SELL, qty=5, order_type=OrderType.MARKET))
        assert sell2.status == OrderStatus.COMPLETE
        fill2 = store.all_fills()[-1]
        assert fill2.ts == restart_time
        assert fill1.ts.date() == fill2.ts.date() == DAY0

        cost_model = CostModel("zerodha_2026")
        expected1 = cost_model.order_charges(
            Side.SELL, Product.CNC, fill1.qty * fill1.price, first_sell_of_scrip_today=True
        ).total
        expected2 = cost_model.order_charges(
            Side.SELL, Product.CNC, fill2.qty * fill2.price, first_sell_of_scrip_today=False
        ).total
        dp_amount = cost_model.schedule.delivery.dp_charge_per_sell_day

        assert fill1.charges == pytest.approx(expected1)  # first sell of the day: DP applied
        assert fill2.charges == pytest.approx(expected2)  # warmed: DP NOT re-applied
        assert expected1 - expected2 == pytest.approx(dp_amount)


# --------------------------------------------------------------------------
# 18. mark_to_market
# --------------------------------------------------------------------------


class TestMarkToMarket:
    def test_marks_valuations_without_matching_any_working_order(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "mark-to-market")
        broker = make_broker(settings, store, capital=100_000.0)
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.1))
        broker.place_order(Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.MARKET))

        # a resting SELL whose limit the new mark price would CROSS -- if
        # mark_to_market matched orders, this would fill.
        resting = broker.place_order(
            Order(symbol="AAA", side=Side.SELL, qty=10, order_type=OrderType.LIMIT, limit_price=150.0)
        )
        assert resting.status == OrderStatus.OPEN

        cash = broker.get_margins().cash_available
        fills_before = len(store.all_fills())
        equity_before = broker.equity()

        broker.mark_to_market({"AAA": 160.0})  # 160 > the 150 sell limit

        assert broker.equity() == pytest.approx(round(cash + 10 * 160.0, 2))
        assert broker.equity() != pytest.approx(equity_before)  # valuation DID move
        assert len(store.all_fills()) == fills_before  # ...but nothing matched
        assert broker.get_order(resting.client_order_id).status == OrderStatus.OPEN
        assert broker.get_margins().cash_available == pytest.approx(cash)  # cash untouched


# --------------------------------------------------------------------------
# Bonus: a full synthetic session (tests/fixtures/ticks.py) for good measure
# --------------------------------------------------------------------------


class TestSyntheticSessionIntegration:
    def test_full_synthetic_session_keeps_the_book_internally_consistent(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """Not a known-answer test: drives PaperBroker through a whole
        synthetic session (the random-walk generator used elsewhere in the
        suite) and checks invariants that must hold regardless of the random
        path: a deeply marketable resting LIMIT fills exactly once (whole
        order), cash never goes negative, and equity always equals
        cash + qty * last_mark for the one held symbol."""
        store = PaperStore(tmp_path / "paper.sqlite", "synthetic-session")
        broker = make_broker(
            settings, store, capital=1_000_000.0, clock=FakeClock(datetime(2024, 1, 15, 9, 15))
        )
        ticks = synthetic_ticks(symbol="ZZZ", day=DAY0, n=50, s0=100.0, seed=42)

        order = broker.place_order(
            Order(symbol="ZZZ", side=Side.BUY, qty=10, order_type=OrderType.LIMIT, limit_price=10_000.0)
        )
        assert order.status == OrderStatus.OPEN  # no quote yet

        total_fills: list[Fill] = []
        for tick in ticks:
            total_fills.extend(broker.on_tick(tick))
            assert broker.get_margins().cash_available >= 0.0

        assert len(total_fills) == 1  # deeply marketable limit fills exactly once, whole-order
        assert broker.get_order(order.client_order_id).status == OrderStatus.COMPLETE

        holdings = broker.get_holdings()
        assert len(holdings) == 1
        last_tick = ticks[-1]
        expected_equity = broker.get_margins().cash_available + holdings[0].qty * last_tick.last_price
        assert broker.equity() == pytest.approx(expected_equity)


# --------------------------------------------------------------------------
# 23. Modification re-validation (review fix: a modify must pass the same
#     pre-trade gates as a fresh placement — Zerodha re-validates server-side)
# --------------------------------------------------------------------------


class TestModifyOrderRevalidation:
    def _resting_limit_buy(
        self, settings: Settings, store: PaperStore, **broker_kwargs: object
    ) -> tuple[PaperBroker, Order]:
        """A broker with a same-day quote (last 100.0) and one RESTING (not
        marketable in touch mode: last 100 > limit 95) LIMIT BUY 10 @ 95."""
        broker = make_broker(settings, store, **broker_kwargs)  # type: ignore[arg-type]
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.95, ask=100.05))
        order = broker.place_order(
            Order(
                client_order_id="rest-buy",
                symbol="AAA",
                side=Side.BUY,
                qty=10,
                order_type=OrderType.LIMIT,
                limit_price=95.0,
            )
        )
        assert order.status == OrderStatus.OPEN
        return broker, order

    def test_modify_qty_past_order_value_limit_rejected_and_order_unchanged(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "modify-risk")
        broker, order = self._resting_limit_buy(
            settings, store, risk_limits=_permissive_limits(max_order_value=5_000.0)
        )

        # 100 * 95 = 9_500 > 5_000 -> the modification is rejected...
        with pytest.raises(RiskViolation, match="order value"):
            broker.modify_order("rest-buy", qty=100)

        # ...and the order keeps working EXACTLY as previously accepted.
        stored = broker.get_order("rest-buy")
        assert stored.status == OrderStatus.OPEN
        assert stored.qty == 10
        assert stored.limit_price == 95.0

        # A compliant modification still works: 50 * 95 = 4_750 <= 5_000.
        modified = broker.modify_order("rest-buy", qty=50)
        assert modified.qty == 50
        assert broker.get_order("rest-buy").qty == 50

    def test_modify_buy_qty_past_cash_rejected_but_own_reservation_excluded(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """qty -> 1_100 (value 104_500) exceeds the 100_000 capital and is
        rejected. qty -> 1_045 (value 99_275 + est. charges) fits ONLY if the
        order's own current ~951 reservation is excluded from the working-order
        commitments — the same order can't reserve cash against itself."""
        store = PaperStore(tmp_path / "paper.sqlite", "modify-cash")
        broker, _ = self._resting_limit_buy(settings, store, capital=100_000.0)

        with pytest.raises(RiskViolation, match="insufficient cash for modification"):
            broker.modify_order("rest-buy", qty=1_100)
        assert broker.get_order("rest-buy").qty == 10

        modified = broker.modify_order("rest-buy", qty=1_045)
        assert modified.qty == 1_045

    def test_modify_sell_qty_past_holdings_rejected_but_own_reservation_excluded(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "modify-oversell")
        broker = make_broker(settings, store, capital=100_000.0)
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.95, ask=100.05))
        # Hold 10 AAA, then rest a LIMIT SELL 5 @ 200 (not marketable: last < limit).
        broker.place_order(Order(symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.MARKET))
        sell = broker.place_order(
            Order(
                client_order_id="rest-sell",
                symbol="AAA",
                side=Side.SELL,
                qty=5,
                order_type=OrderType.LIMIT,
                limit_price=200.0,
            )
        )
        assert sell.status == OrderStatus.OPEN

        # 11 > 10 held: oversell, even with its own 5-share reservation excluded.
        with pytest.raises(RiskViolation, match="oversell on modification"):
            broker.modify_order("rest-sell", qty=11)
        assert broker.get_order("rest-sell").qty == 5

        # 10 == held passes ONLY because the order's own resting 5 are excluded
        # (held 10 minus OTHER working sells 0); double-counting itself would
        # leave just 5 available and wrongly reject this.
        modified = broker.modify_order("rest-sell", qty=10)
        assert modified.qty == 10


# --------------------------------------------------------------------------
# 24. Thread safety (review fix: in --schedule mode the websocket thread and
#     the APScheduler job threads share one broker; a single reentrant lock
#     must keep check-then-mutate sequences atomic)
# --------------------------------------------------------------------------


class TestThreadSafety:
    def test_concurrent_ticks_placements_and_cancels_keep_ledger_consistent(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """Three threads hammer one broker: a tick feeder (prices oscillating
        so resting limits fill from the tick thread), a placer whose limits
        rest then fill, and a churner that places-and-cancels. Afterwards the
        in-memory ledger must EXACTLY equal a fresh replay of the store (the
        durable truth), cash must never have gone negative, and every fill
        must belong to a COMPLETE order. Not a probabilistic race hunt — a
        canary: any interleaving corruption shows up as replay disagreement."""
        import threading
        from datetime import timedelta

        store = PaperStore(tmp_path / "paper.sqlite", "threads")
        broker = make_broker(settings, store, capital=1_000_000.0)
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.95, ask=100.05))

        errors: list[BaseException] = []

        def _guarded(fn: object) -> object:
            def wrapper() -> None:
                try:
                    fn()  # type: ignore[operator]
                except BaseException as exc:  # noqa: BLE001 -- surfaced via `errors`
                    errors.append(exc)

            return wrapper

        def ticker() -> None:
            for i in range(150):
                px = 100.0 + ((i % 7) - 3) * 0.05  # 99.85 .. 100.15
                broker.on_tick(
                    make_tick(
                        "AAA",
                        T0 + timedelta(seconds=i + 1),
                        last=px,
                        bid=px - 0.05,
                        ask=px + 0.05,
                    )
                )

        def placer() -> None:
            # limit 99.9: rests when last > 99.9, fills from the TICK thread
            # when the oscillation dips to 99.85/99.90.
            for i in range(50):
                broker.place_order(
                    Order(
                        client_order_id=f"buy-{i}",
                        symbol="AAA",
                        side=Side.BUY,
                        qty=5,
                        order_type=OrderType.LIMIT,
                        limit_price=99.9,
                    )
                )

        def churner() -> None:
            # limit 99.0 is never marketable on this path -> cancel always
            # races only placement/tick handling, never a fill of its own.
            for i in range(50):
                oid = f"churn-{i}"
                broker.place_order(
                    Order(
                        client_order_id=oid,
                        symbol="AAA",
                        side=Side.BUY,
                        qty=3,
                        order_type=OrderType.LIMIT,
                        limit_price=99.0,
                    )
                )
                broker.cancel_order(oid)

        threads = [
            threading.Thread(target=_guarded(fn)) for fn in (ticker, placer, churner)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60.0)
        assert not any(t.is_alive() for t in threads), "deadlock: worker thread still alive"
        assert errors == []

        assert broker.get_margins().cash_available >= 0.0

        # The durable store replay is the ground truth: a fresh broker rebuilt
        # from it must agree exactly with the live in-memory ledger.
        fresh = make_broker(settings, store, capital=1_000_000.0)
        assert fresh.get_margins().cash_available == pytest.approx(
            broker.get_margins().cash_available
        )
        assert {p.symbol: p.qty for p in fresh.get_holdings()} == {
            p.symbol: p.qty for p in broker.get_holdings()
        }

        fills = store.all_fills()
        complete = store.orders(status=OrderStatus.COMPLETE)
        assert len(fills) == len(complete)  # whole-order fills: one fill per COMPLETE order
        assert sum(f.qty for f in fills) == sum(o.qty for o in complete)
        cancelled = store.orders(status=OrderStatus.CANCELLED)
        assert len(cancelled) == 50  # every churned order ended CANCELLED, none filled


# --------------------------------------------------------------------------
# 18. Kill switch covers modify (audit fix: an engaged switch must block
#     exposure increases via modification, not just fresh placements)
# --------------------------------------------------------------------------


class TestKillSwitchBlocksModify:
    def test_modify_raises_while_engaged_and_leaves_order_working(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "ks-modify")
        ks = KillSwitch(tmp_path / "KILL_SWITCH")
        broker = make_broker(settings, store, kill_switch=ks)
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.1))
        broker.place_order(
            Order(
                client_order_id="ksm-1",
                symbol="AAA",
                side=Side.BUY,
                qty=10,
                order_type=OrderType.LIMIT,
                limit_price=95.0,
            )
        )

        ks.engage("halt")
        with pytest.raises(KillSwitchActive):
            broker.modify_order("ksm-1", qty=100)

        stored = store.get_order("ksm-1")
        assert stored.qty == 10  # untouched, still working exactly as accepted
        assert stored.status == OrderStatus.OPEN

        # Cancels must STAY allowed while engaged (they only reduce risk).
        assert broker.cancel_order("ksm-1").status == OrderStatus.CANCELLED


# --------------------------------------------------------------------------
# 19. Charge estimates carry trade_date (audit fix: estimates must price at
#     the charge schedule in force on the order/fill day)
# --------------------------------------------------------------------------


class TestChargeEstimatesCarryTradeDate:
    def test_pre_trade_and_fill_guard_estimates_pass_the_days_date(
        self, settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        store = PaperStore(tmp_path / "paper.sqlite", "chg-date")
        broker = make_broker(settings, store)
        broker.on_tick(make_tick("AAA", T0, last=100.0, bid=99.9, ask=100.1))

        recorded: list[dict] = []
        real = broker._cost_model.order_charges  # noqa: SLF001 -- spy on the seam

        def spy(*args: object, **kwargs: object):
            recorded.append(dict(kwargs))
            return real(*args, **kwargs)

        monkeypatch.setattr(broker._cost_model, "order_charges", spy)  # noqa: SLF001
        broker.place_order(
            Order(client_order_id="chg-1", symbol="AAA", side=Side.BUY, qty=10)
        )

        assert store.get_order("chg-1").status == OrderStatus.COMPLETE
        # Every estimate call that carries trade_date must carry the order
        # day; the calls without it come from the ChargeCalculator fill seam
        # (engine-owned, pinned schedule) and are out of scope here.
        dated = [k["trade_date"] for k in recorded if "trade_date" in k]
        assert dated, "no order_charges estimate carried trade_date"
        assert set(dated) == {DAY0}

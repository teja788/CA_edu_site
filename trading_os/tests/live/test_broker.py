"""Tests for live/broker.py: ZerodhaLiveBroker.

Mirrors tests/paper/test_broker.py conventions: a ``FakeClock`` injected as
``now_fn`` and pinned to a real 2024 trading day (2024-01-15, Monday), on-disk
``PaperStore`` journals under ``tmp_path``, a recording fake alerter, and
permissive ``RiskLimits(market_hours_only=False)`` so only the rule a test
explicitly overrides can trip.

Kite is ALWAYS faked (``FakeKite``): canned dict responses shaped exactly like
the real API, recording every call. No test touches the network. The one place
a real kiteconnect type is used is the token-expiry path, which asserts on a
genuine ``kiteconnect.exceptions.TokenException`` -- exactly what production
catches.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

import pytest
from kiteconnect.exceptions import TokenException

from tradingos.broker.killswitch import KillSwitch
from tradingos.broker.risk import RiskLimits
from tradingos.config.settings import Settings
from tradingos.core.alerts import TelegramAlerter
from tradingos.core.errors import (
    AuthError,
    BrokerError,
    KillSwitchActive,
    OrderStateError,
    RiskViolation,
)
from tradingos.core.models import Fill, Order, OrderStatus, OrderType, Product, Side
from tradingos.costs.model import CostModel
from tradingos.data.calendar import NSECalendar
from tradingos.live.broker import ZerodhaLiveBroker, _tag_for
from tradingos.paper.ledgerdb import PaperStore

T0 = datetime(2024, 1, 15, 10, 0)  # Monday, an NSE trading day


# --------------------------------------------------------------------------
# Fakes
# --------------------------------------------------------------------------


class FakeClock:
    def __init__(self, now: datetime = T0) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


class RecordingAlerter(TelegramAlerter):
    """A disabled TelegramAlerter that records what it was asked to send."""

    def __init__(self) -> None:
        super().__init__(None, None)
        self.fills: list[Fill] = []
        self.rejections: list[tuple[Order, str]] = []
        self.token_expiries: list[str] = []

    def alert_fill(self, fill: Fill) -> bool:
        self.fills.append(fill)
        return True

    def alert_rejection(self, order: Order, reason: str) -> bool:
        self.rejections.append((order, reason))
        return True

    def alert_token_expiry(self, message: str = "Kite access token expired") -> bool:
        self.token_expiries.append(message)
        return True


class FakeKite:
    """Stand-in for kiteconnect.KiteConnect: canned responses, call recording.

    Response shapes match the real Connect API. ``raises`` maps a method name to
    an exception to raise on the next call to it; ``fail_cancel_ids`` makes
    cancel_order raise for specific broker order ids (fault-tolerance tests).
    """

    def __init__(
        self,
        *,
        ltp_price: float = 100.0,
        margins_response: dict | None = None,
        positions_response: dict | None = None,
        holdings_response: list | None = None,
        quote_response: dict | None = None,
        orders_response: list | None = None,
        raises: dict[str, BaseException] | None = None,
        fail_cancel_ids: set[str] | None = None,
    ) -> None:
        self._ltp_price = ltp_price
        self._margins = margins_response or {
            "available": {"live_balance": 1_000_000.0, "cash": 1_000_000.0},
            "utilised": {"debits": 0.0},
        }
        self._positions = positions_response or {"net": [], "day": []}
        self._holdings = [] if holdings_response is None else holdings_response
        self._quote = quote_response or {}
        self._orders = [] if orders_response is None else orders_response
        self._raises = raises or {}
        self._fail_cancel_ids = fail_cancel_ids or set()
        self.calls: list[tuple[str, dict]] = []
        self.place_calls: list[dict] = []
        self._seq = 0

    def _maybe_raise(self, method: str) -> None:
        exc = self._raises.get(method)
        if exc is not None:
            raise exc

    def set_orders(self, rows: list[dict]) -> None:
        self._orders = rows

    # -- reads --
    def ltp(self, instruments: list[str]) -> dict:
        self.calls.append(("ltp", {"instruments": instruments}))
        self._maybe_raise("ltp")
        return {k: {"instrument_token": 1, "last_price": self._ltp_price} for k in instruments}

    def quote(self, instruments: list[str]) -> dict:
        self.calls.append(("quote", {"instruments": instruments}))
        self._maybe_raise("quote")
        return self._quote

    def margins(self, segment: str) -> dict:
        self.calls.append(("margins", {"segment": segment}))
        self._maybe_raise("margins")
        return self._margins

    def positions(self) -> dict:
        self.calls.append(("positions", {}))
        self._maybe_raise("positions")
        return self._positions

    def holdings(self) -> list:
        self.calls.append(("holdings", {}))
        self._maybe_raise("holdings")
        return self._holdings

    def orders(self) -> list:
        self.calls.append(("orders", {}))
        self._maybe_raise("orders")
        return self._orders

    # -- mutations --
    def place_order(self, **kwargs: object) -> str:
        self.calls.append(("place_order", kwargs))
        self.place_calls.append(kwargs)
        self._maybe_raise("place_order")
        self._seq += 1
        return f"KITE{self._seq}"

    def modify_order(self, **kwargs: object) -> str:
        self.calls.append(("modify_order", kwargs))
        self._maybe_raise("modify_order")
        return str(kwargs["order_id"])

    def cancel_order(self, **kwargs: object) -> str:
        self.calls.append(("cancel_order", kwargs))
        self._maybe_raise("cancel_order")
        if kwargs.get("order_id") in self._fail_cancel_ids:
            raise ValueError(f"broker refused to cancel {kwargs.get('order_id')}")
        return str(kwargs["order_id"])


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _permissive_limits(**overrides: object) -> RiskLimits:
    kwargs: dict[str, object] = dict(
        max_order_value=10_000_000.0,
        max_position_pct=1_000.0,
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
    kite: FakeKite,
    *,
    dry_run: bool = True,
    risk_limits: RiskLimits | None = None,
    kill_switch: KillSwitch | None = None,
    alerter: RecordingAlerter | None = None,
    clock: FakeClock | None = None,
) -> ZerodhaLiveBroker:
    return ZerodhaLiveBroker(
        settings,
        strategy_id=store.strategy_id,
        dry_run=dry_run,
        kite=kite,
        risk_limits=risk_limits or _permissive_limits(),
        kill_switch=kill_switch or KillSwitch(settings.kill_switch_path),
        calendar=NSECalendar(settings),
        alerter=alerter or RecordingAlerter(),
        store=store,
        now_fn=clock or FakeClock(),
    )


def _order(cid: str, **kw: object) -> Order:
    base: dict[str, object] = dict(
        client_order_id=cid, symbol="AAA", side=Side.BUY, qty=10, order_type=OrderType.MARKET
    )
    base.update(kw)
    return Order(**base)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# 1. Kite place_order kwargs mapping (exact dict equality, tag length)
# --------------------------------------------------------------------------


class TestPlaceKwargsMapping:
    def _place_dry_and_get_kwargs(
        self, settings: Settings, tmp_path: Path, order: Order
    ) -> tuple[dict, FakeKite]:
        store = PaperStore(tmp_path / "live.sqlite", "kw-" + order.client_order_id)
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=True)
        broker.place_order(order)
        assert kite.place_calls == []  # dry-run never calls the mutating API
        return broker.intended_calls[-1], kite

    def test_market_buy_kwargs(self, settings: Settings, tmp_path: Path) -> None:
        cid = "cid-mkt-buy"
        kwargs, _ = self._place_dry_and_get_kwargs(settings, tmp_path, _order(cid))
        assert kwargs == {
            "variety": "regular",
            "exchange": "NSE",
            "tradingsymbol": "AAA",
            "transaction_type": "BUY",
            "quantity": 10,
            "product": "CNC",
            "order_type": "MARKET",
            "validity": "DAY",
            "tag": _tag_for(cid),
        }

    def test_market_sell_kwargs(self, settings: Settings, tmp_path: Path) -> None:
        cid = "cid-mkt-sell"
        kwargs, _ = self._place_dry_and_get_kwargs(
            settings, tmp_path, _order(cid, side=Side.SELL, qty=7)
        )
        assert kwargs["transaction_type"] == "SELL"
        assert kwargs["order_type"] == "MARKET"
        assert kwargs["quantity"] == 7
        assert "price" not in kwargs and "trigger_price" not in kwargs

    def test_limit_buy_kwargs_includes_price(self, settings: Settings, tmp_path: Path) -> None:
        cid = "cid-lim-buy"
        order = _order(cid, order_type=OrderType.LIMIT, limit_price=95.5)
        kwargs, _ = self._place_dry_and_get_kwargs(settings, tmp_path, order)
        assert kwargs == {
            "variety": "regular",
            "exchange": "NSE",
            "tradingsymbol": "AAA",
            "transaction_type": "BUY",
            "quantity": 10,
            "product": "CNC",
            "order_type": "LIMIT",
            "validity": "DAY",
            "tag": _tag_for(cid),
            "price": 95.5,
        }

    def test_limit_sell_kwargs_includes_price(self, settings: Settings, tmp_path: Path) -> None:
        cid = "cid-lim-sell"
        order = _order(cid, side=Side.SELL, qty=5, order_type=OrderType.LIMIT, limit_price=200.0)
        kwargs, _ = self._place_dry_and_get_kwargs(settings, tmp_path, order)
        assert kwargs["transaction_type"] == "SELL"
        assert kwargs["order_type"] == "LIMIT"
        assert kwargs["price"] == 200.0

    def test_tag_is_deterministic_alnum_and_within_20_chars(self) -> None:
        tag = _tag_for("some-client-order-id")
        assert tag == hashlib.sha1(b"some-client-order-id").hexdigest()[:18]
        assert tag == _tag_for("some-client-order-id")  # deterministic
        assert len(tag) <= 20
        assert tag.isalnum()


# --------------------------------------------------------------------------
# 2. Dry-run behaviour
# --------------------------------------------------------------------------


class TestDryRun:
    def test_dry_run_journals_open_with_dry_id_and_records_intended_calls(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "dry-basic")
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=True)

        o1 = broker.place_order(_order("dry-1"))
        o2 = broker.place_order(_order("dry-2"))

        assert o1.status == OrderStatus.OPEN
        assert o1.broker_order_id == "DRY-1"
        assert o2.broker_order_id == "DRY-2"  # monotonic per instance
        assert kite.place_calls == []  # nothing sent to the broker
        assert len(broker.intended_calls) == 2
        # journalled OPEN, restart-visible
        assert store.get_order("dry-1").status == OrderStatus.OPEN
        assert store.get_order("dry-1").tag == _tag_for("dry-1")

    def test_sync_orders_is_a_noop_in_dry_run(self, settings: Settings, tmp_path: Path) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "dry-sync")
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=True)
        broker.place_order(_order("dry-1"))
        assert broker.sync_orders() == []
        assert ("orders", {}) not in kite.calls  # never even queried the broker


# --------------------------------------------------------------------------
# 3. Live placement
# --------------------------------------------------------------------------


class TestLivePlacement:
    def test_live_place_returns_kite_order_id_and_journals_open(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "live-place")
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=False, clock=FakeClock(T0))

        order = broker.place_order(_order("live-1"))

        assert order.status == OrderStatus.OPEN
        assert order.broker_order_id == "KITE1"
        assert order.created_at == T0
        assert len(kite.place_calls) == 1
        assert kite.place_calls[0]["tradingsymbol"] == "AAA"
        stored = store.get_order("live-1")
        assert stored.status == OrderStatus.OPEN
        assert stored.broker_order_id == "KITE1"


# --------------------------------------------------------------------------
# 4. Idempotency and restart safety (never double-place)
# --------------------------------------------------------------------------


class TestIdempotency:
    def test_dry_run_re_place_makes_no_second_intent(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "idem-dry")
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=True)

        first = broker.place_order(_order("idem-1"))
        again = broker.place_order(_order("idem-1"))

        assert again.status == first.status
        assert again.broker_order_id == first.broker_order_id
        assert len(broker.intended_calls) == 1  # not re-journalled

    def test_live_re_place_makes_no_second_api_call(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "idem-live")
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=False)

        first = broker.place_order(_order("idem-1"))
        again = broker.place_order(_order("idem-1"))

        assert again.broker_order_id == first.broker_order_id == "KITE1"
        assert len(kite.place_calls) == 1  # the retry never hit the API

    def test_restart_new_instance_same_journal_does_not_double_place(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "restart")
        kite1 = FakeKite()
        broker1 = make_broker(settings, store, kite1, dry_run=False)
        broker1.place_order(_order("restart-1"))
        assert len(kite1.place_calls) == 1

        # Fresh process: new broker, new client, SAME journal.
        kite2 = FakeKite()
        broker2 = make_broker(settings, store, kite2, dry_run=False)
        replaced = broker2.place_order(_order("restart-1"))

        assert replaced.broker_order_id == "KITE1"  # the original id, from the journal
        assert kite2.place_calls == []  # crucially, no second placement


# --------------------------------------------------------------------------
# 5. Kill switch
# --------------------------------------------------------------------------


class TestKillSwitch:
    def test_engaged_kill_switch_rejects_and_touches_no_api(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "kill")
        ks = KillSwitch(tmp_path / "KILL_SWITCH")
        ks.engage("manual halt")
        kite = FakeKite()
        alerter = RecordingAlerter()
        broker = make_broker(settings, store, kite, dry_run=False, kill_switch=ks, alerter=alerter)

        with pytest.raises(KillSwitchActive, match="manual halt"):
            broker.place_order(_order("kill-1"))

        assert kite.calls == []  # kill switch is checked before any Kite call
        stored = store.get_order("kill-1")
        assert stored.status == OrderStatus.REJECTED
        assert "manual halt" in (stored.status_message or "")
        assert len(alerter.rejections) == 1


# --------------------------------------------------------------------------
# 6. Pre-trade risk violation
# --------------------------------------------------------------------------


class TestRiskViolation:
    def test_max_order_value_rejects_persists_and_alerts_without_placing(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "risk")
        kite = FakeKite()
        alerter = RecordingAlerter()
        broker = make_broker(
            settings,
            store,
            kite,
            dry_run=False,
            alerter=alerter,
            risk_limits=_permissive_limits(max_order_value=100.0),
        )
        order = _order("risk-1", order_type=OrderType.LIMIT, limit_price=1_000.0)

        with pytest.raises(RiskViolation, match="order value"):
            broker.place_order(order)

        assert kite.place_calls == []  # never placed
        stored = store.get_order("risk-1")
        assert stored.status == OrderStatus.REJECTED
        assert "order value" in (stored.status_message or "")
        assert len(alerter.rejections) == 1


# --------------------------------------------------------------------------
# 7. Token expiry -> alert + AuthError
# --------------------------------------------------------------------------


class TestTokenExpiry:
    def test_token_exception_on_place_alerts_and_raises_autherror_without_journalling(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "tok-place")
        kite = FakeKite(raises={"place_order": TokenException("token invalid")})
        alerter = RecordingAlerter()
        broker = make_broker(settings, store, kite, dry_run=False, alerter=alerter)

        with pytest.raises(AuthError, match="token"):
            broker.place_order(_order("tok-1"))

        assert len(alerter.token_expiries) == 1
        # A transient token expiry must NOT burn the order as REJECTED.
        assert store.get_order("tok-1") is None

    def test_token_exception_on_a_read_alerts_and_raises_autherror(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "tok-read")
        kite = FakeKite(raises={"margins": TokenException("token invalid")})
        alerter = RecordingAlerter()
        broker = make_broker(settings, store, kite, dry_run=False, alerter=alerter)

        with pytest.raises(AuthError, match="token"):
            broker.get_margins()

        assert len(alerter.token_expiries) == 1


# --------------------------------------------------------------------------
# 8. Reconciliation (sync_orders)
# --------------------------------------------------------------------------


class TestSyncOrders:
    def _place_four(self, broker: ZerodhaLiveBroker) -> dict[str, Order]:
        return {
            "complete": broker.place_order(_order("s-complete")),
            "rejected": broker.place_order(_order("s-rejected")),
            "cancelled": broker.place_order(_order("s-cancelled")),
            "partial": broker.place_order(_order("s-partial")),
        }

    def _orders_response(self, placed: dict[str, Order]) -> list[dict]:
        ts = datetime(2024, 1, 15, 10, 0, 5)
        return [
            {
                "order_id": placed["complete"].broker_order_id,
                "tag": placed["complete"].tag,
                "status": "COMPLETE",
                "filled_quantity": 10,
                "quantity": 10,
                "average_price": 101.0,
                "product": "CNC",
                "order_timestamp": ts,
                "status_message": None,
            },
            {
                "order_id": placed["rejected"].broker_order_id,
                "tag": placed["rejected"].tag,
                "status": "REJECTED",
                "filled_quantity": 0,
                "quantity": 10,
                "average_price": 0.0,
                "product": "CNC",
                "order_timestamp": ts,
                "status_message": "insufficient margin",
            },
            {
                "order_id": placed["cancelled"].broker_order_id,
                "tag": placed["cancelled"].tag,
                "status": "CANCELLED",
                "filled_quantity": 0,
                "quantity": 10,
                "average_price": 0.0,
                "product": "CNC",
                "order_timestamp": ts,
                "status_message": "cancelled by user",
            },
            {
                "order_id": placed["partial"].broker_order_id,
                "tag": placed["partial"].tag,
                "status": "OPEN",
                "filled_quantity": 3,
                "quantity": 10,
                "average_price": 100.5,
                "product": "CNC",
                "order_timestamp": ts,
                "status_message": None,
            },
        ]

    def test_sync_maps_statuses_updates_fills_and_alerts(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "sync")
        kite = FakeKite()
        alerter = RecordingAlerter()
        broker = make_broker(settings, store, kite, dry_run=False, alerter=alerter)
        placed = self._place_four(broker)
        kite.set_orders(self._orders_response(placed))

        changed = broker.sync_orders()

        assert {o.client_order_id for o in changed} == {
            "s-complete",
            "s-rejected",
            "s-cancelled",
            "s-partial",
        }
        assert store.get_order("s-complete").status == OrderStatus.COMPLETE
        assert store.get_order("s-complete").filled_qty == 10
        assert store.get_order("s-rejected").status == OrderStatus.REJECTED
        assert store.get_order("s-cancelled").status == OrderStatus.CANCELLED
        assert store.get_order("s-partial").status == OrderStatus.PARTIAL
        assert store.get_order("s-partial").filled_qty == 3

        # Exactly one Fill (on COMPLETE), with a cost-model ESTIMATE for charges.
        fills = store.all_fills()
        assert len(fills) == 1
        fill = fills[0]
        assert fill.client_order_id == "s-complete"
        assert fill.qty == 10
        assert fill.price == 101.0
        assert fill.ts == datetime(2024, 1, 15, 10, 0, 5)
        expected_charges = CostModel("zerodha_2026").order_charges(
            Side.BUY, Product.CNC, 10 * 101.0
        ).total
        assert fill.charges == expected_charges

        assert len(alerter.fills) == 1
        assert len(alerter.rejections) == 2  # rejected + cancelled both alert_rejection

    def test_sync_is_idempotent_no_duplicate_fill_on_second_call(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "sync-idem")
        kite = FakeKite()
        alerter = RecordingAlerter()
        broker = make_broker(settings, store, kite, dry_run=False, alerter=alerter)
        placed = self._place_four(broker)
        kite.set_orders(self._orders_response(placed))

        broker.sync_orders()
        second = broker.sync_orders()  # same broker state -> nothing changes

        assert second == []  # terminal orders skipped; partial unchanged
        assert len(store.all_fills()) == 1  # NOT double-recorded
        assert len(alerter.fills) == 1

    def test_sync_maps_open_with_no_fill_to_open(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "sync-open")
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=False)
        placed = broker.place_order(_order("s-open"))
        kite.set_orders(
            [
                {
                    "order_id": placed.broker_order_id,
                    "tag": placed.tag,
                    "status": "TRIGGER PENDING",  # an OPEN-ish status
                    "filled_quantity": 0,
                    "quantity": 10,
                    "average_price": 0.0,
                    "product": "CNC",
                    "order_timestamp": datetime(2024, 1, 15, 10, 0, 5),
                }
            ]
        )
        assert broker.sync_orders() == []  # OPEN -> OPEN, no change
        assert store.get_order("s-open").status == OrderStatus.OPEN


# --------------------------------------------------------------------------
# 9. cancel_all_open
# --------------------------------------------------------------------------


class TestCancelAllOpen:
    def test_cancels_only_working_orders(self, settings: Settings, tmp_path: Path) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "cancel-all")
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=False)
        o1 = broker.place_order(_order("c-1"))
        o2 = broker.place_order(_order("c-2"))
        # A terminal (COMPLETE) order injected directly must be left untouched.
        done = Order(
            client_order_id="c-done",
            symbol="AAA",
            side=Side.BUY,
            qty=1,
            order_type=OrderType.MARKET,
            broker_order_id="KITE-DONE",
            status=OrderStatus.COMPLETE,
            created_at=T0,
        )
        store.save_order(done)

        cancelled = broker.cancel_all_open()

        assert {o.client_order_id for o in cancelled} == {"c-1", "c-2"}
        assert store.get_order("c-1").status == OrderStatus.CANCELLED
        assert store.get_order("c-2").status == OrderStatus.CANCELLED
        assert store.get_order("c-done").status == OrderStatus.COMPLETE
        cancel_ids = {kw["order_id"] for name, kw in kite.calls if name == "cancel_order"}
        assert cancel_ids == {o1.broker_order_id, o2.broker_order_id}

    def test_is_fault_tolerant_one_failed_cancel_does_not_abort_the_rest(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "cancel-fault")
        broker0 = make_broker(settings, store, FakeKite(), dry_run=False)
        o1 = broker0.place_order(_order("cf-1"))
        o2 = broker0.place_order(_order("cf-2"))

        # A kite whose cancel fails for o2's broker id only.
        kite = FakeKite(fail_cancel_ids={o2.broker_order_id})
        broker = make_broker(settings, store, kite, dry_run=False)

        cancelled = broker.cancel_all_open()  # must NOT raise

        assert {o.client_order_id for o in cancelled} == {"cf-1"}
        assert store.get_order("cf-1").status == OrderStatus.CANCELLED
        assert store.get_order("cf-2").status == OrderStatus.OPEN  # failed cancel left working
        assert o1.broker_order_id  # (silence unused-var lint intent)


# --------------------------------------------------------------------------
# 10. modify / cancel single order
# --------------------------------------------------------------------------


class TestModifyCancel:
    def test_dry_run_modify_updates_journal_only(self, settings: Settings, tmp_path: Path) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "mod-dry")
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=True)
        broker.place_order(_order("m-1", order_type=OrderType.LIMIT, limit_price=90.0))

        modified = broker.modify_order("m-1", qty=5, limit_price=120.0)

        assert modified.qty == 5
        assert modified.limit_price == 120.0
        assert store.get_order("m-1").qty == 5
        assert [name for name, _ in kite.calls if name == "modify_order"] == []  # no API

    def test_live_cancel_calls_kite_and_marks_cancelled(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "cancel-live")
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=False)
        order = broker.place_order(_order("cl-1", order_type=OrderType.LIMIT, limit_price=90.0))

        cancelled = broker.cancel_order("cl-1")

        assert cancelled.status == OrderStatus.CANCELLED
        assert ("cancel_order", {"variety": "regular", "order_id": order.broker_order_id}) in kite.calls

    def test_modify_unknown_order_raises_broker_error(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "mod-unknown")
        broker = make_broker(settings, store, FakeKite(), dry_run=True)
        with pytest.raises(BrokerError, match="unknown order"):
            broker.modify_order("nope", qty=1)

    def test_cancel_terminal_order_raises_order_state_error(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "cancel-terminal")
        broker = make_broker(settings, store, FakeKite(), dry_run=True)
        done = Order(
            client_order_id="ct-1",
            symbol="AAA",
            side=Side.BUY,
            qty=1,
            order_type=OrderType.MARKET,
            status=OrderStatus.COMPLETE,
            created_at=T0,
        )
        store.save_order(done)
        with pytest.raises(OrderStateError):
            broker.cancel_order("ct-1")


# --------------------------------------------------------------------------
# 11. Read-side mappings
# --------------------------------------------------------------------------


class TestReadMappings:
    def test_get_holdings_includes_t1_quantity(self, settings: Settings, tmp_path: Path) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "holdings")
        kite = FakeKite(
            holdings_response=[
                {
                    "tradingsymbol": "INFY",
                    "quantity": 10,
                    "t1_quantity": 5,
                    "average_price": 1_400.0,
                    "last_price": 1_500.0,
                }
            ]
        )
        broker = make_broker(settings, store, kite, dry_run=True)
        holdings = broker.get_holdings()
        assert len(holdings) == 1
        assert holdings[0].symbol == "INFY"
        assert holdings[0].qty == 15  # 10 settled + 5 T1
        assert holdings[0].last_price == 1_500.0

    def test_get_positions_maps_net_book(self, settings: Settings, tmp_path: Path) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "positions")
        kite = FakeKite(
            positions_response={
                "net": [
                    {
                        "tradingsymbol": "TCS",
                        "quantity": 8,
                        "average_price": 3_000.0,
                        "last_price": 3_100.0,
                        "product": "MIS",
                    }
                ],
                "day": [],
            }
        )
        broker = make_broker(settings, store, kite, dry_run=True)
        positions = broker.get_positions()
        assert len(positions) == 1
        assert positions[0].symbol == "TCS"
        assert positions[0].qty == 8
        assert positions[0].last_price == 3_100.0

    def test_margins_prefers_live_balance(self, settings: Settings, tmp_path: Path) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "margins-lb")
        kite = FakeKite(
            margins_response={
                "available": {"live_balance": 7_000.0, "cash": 5_000.0},
                "utilised": {"debits": 250.0},
            }
        )
        broker = make_broker(settings, store, kite, dry_run=True)
        margins = broker.get_margins()
        assert margins.cash_available == 7_000.0
        assert margins.used == 250.0

    def test_margins_falls_back_to_cash_and_zero_debits(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "margins-cash")
        kite = FakeKite(
            margins_response={"available": {"cash": 5_000.0}, "utilised": {}}
        )
        broker = make_broker(settings, store, kite, dry_run=True)
        margins = broker.get_margins()
        assert margins.cash_available == 5_000.0  # no live_balance -> cash
        assert margins.used == 0.0  # no debits -> 0

    def test_get_quote_maps_depth_and_volume(self, settings: Settings, tmp_path: Path) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "quote")
        kite = FakeKite(
            quote_response={
                "NSE:AAA": {
                    "last_price": 100.0,
                    "volume": 12345,
                    "last_trade_time": datetime(2024, 1, 15, 10, 0, 0),
                    "depth": {
                        "buy": [{"price": 99.9, "quantity": 10}],
                        "sell": [{"price": 100.1, "quantity": 8}],
                    },
                }
            }
        )
        broker = make_broker(settings, store, kite, dry_run=True)
        quotes = broker.get_quote(["AAA"])
        assert quotes["AAA"].last_price == 100.0
        assert quotes["AAA"].bid == 99.9
        assert quotes["AAA"].ask == 100.1
        assert quotes["AAA"].volume == 12345
        assert quotes["AAA"].ts == datetime(2024, 1, 15, 10, 0, 0)

    def test_equity_is_cash_plus_marked_holdings_and_positions(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "equity")
        kite = FakeKite(
            margins_response={"available": {"live_balance": 10_000.0}, "utilised": {"debits": 0.0}},
            holdings_response=[
                {"tradingsymbol": "INFY", "quantity": 10, "t1_quantity": 0,
                 "average_price": 100.0, "last_price": 150.0}
            ],
            positions_response={
                "net": [{"tradingsymbol": "TCS", "quantity": 5, "average_price": 200.0,
                         "last_price": 220.0}],
                "day": [],
            },
        )
        broker = make_broker(settings, store, kite, dry_run=True)
        # 10_000 cash + 10*150 (INFY) + 5*220 (TCS) = 12_600
        assert broker.equity() == pytest.approx(12_600.0)

    def test_stream_ticks_not_implemented(self, settings: Settings, tmp_path: Path) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "stream")
        broker = make_broker(settings, store, FakeKite(), dry_run=True)
        with pytest.raises(NotImplementedError, match="TickStreamer"):
            broker.stream_ticks(["AAA"], lambda tick: None)


# --------------------------------------------------------------------------
# 12. Settings.live_db_path
# --------------------------------------------------------------------------


class TestSettingsLiveDbPath:
    def test_live_db_path_is_under_data_dir(self, tmp_path: Path) -> None:
        s = Settings(data_dir=tmp_path / "data", artifacts_dir=tmp_path / "artifacts", _env_file=None)
        assert s.live_db_path == (tmp_path / "data" / "live.sqlite")

    def test_live_and_paper_db_paths_are_distinct(self, settings: Settings) -> None:
        assert settings.live_db_path != settings.paper_db_path


# --------------------------------------------------------------------------
# 16. Modification re-validation (review fix: a modify must pass the same
#     pre-trade risk gates as a fresh placement -- our self-imposed limits
#     must not be bypassable by inflating qty after acceptance)
# --------------------------------------------------------------------------


class TestModifyOrderRevalidation:
    def _resting_limit_buy(
        self, settings: Settings, tmp_path: Path, *, risk_limits: RiskLimits
    ) -> tuple[ZerodhaLiveBroker, FakeKite]:
        store = PaperStore(tmp_path / "live.sqlite", "modify-risk")
        kite = FakeKite(ltp_price=100.0)
        broker = make_broker(settings, store, kite, dry_run=False, risk_limits=risk_limits)
        broker.place_order(
            _order("rest-buy", order_type=OrderType.LIMIT, limit_price=95.0, qty=10)
        )
        return broker, kite

    def test_modify_qty_past_order_value_limit_rejected_and_order_unchanged(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        broker, kite = self._resting_limit_buy(
            settings, tmp_path, risk_limits=_permissive_limits(max_order_value=5_000.0)
        )
        n_modify_calls_before = len([c for c, _ in kite.calls if c == "modify_order"])

        # 100 * 95 = 9_500 > 5_000 -> rejected BEFORE any kite.modify_order call...
        with pytest.raises(RiskViolation, match="order value"):
            broker.modify_order("rest-buy", qty=100)

        # ...the journal row is untouched and no modify API call was made.
        stored = broker.get_order("rest-buy")
        assert stored.qty == 10
        assert stored.limit_price == 95.0
        assert stored.status == OrderStatus.OPEN
        assert (
            len([c for c, _ in kite.calls if c == "modify_order"]) == n_modify_calls_before
        )

        # A compliant modification still goes through: 50 * 95 = 4_750 <= 5_000.
        modified = broker.modify_order("rest-buy", qty=50)
        assert modified.qty == 50
        assert len([c for c, _ in kite.calls if c == "modify_order"]) == 1

    def test_dry_run_modify_is_also_revalidated(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "modify-risk-dry")
        kite = FakeKite(ltp_price=100.0)
        broker = make_broker(
            settings,
            store,
            kite,
            dry_run=True,
            risk_limits=_permissive_limits(max_order_value=5_000.0),
        )
        broker.place_order(
            _order("rest-buy", order_type=OrderType.LIMIT, limit_price=95.0, qty=10)
        )

        with pytest.raises(RiskViolation, match="order value"):
            broker.modify_order("rest-buy", qty=100)
        assert broker.get_order("rest-buy").qty == 10

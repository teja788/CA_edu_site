"""Order-flow safety regression tests for live/broker.py (audit fix wave).

Covers the failure modes found by the paper/live order-flow audit:

1. the place-vs-journal crash window (write-ahead journal + tag-based
   crash-recovery reconciliation: a crash anywhere around the
   ``kite.place_order`` call must never lead to a double order OR a silently
   dropped order),
2. ambiguous placement failures (an exception does not mean "not placed"),
3. the cancel/fill race (a locally-CANCELLED order that actually filled),
4. partial fills learned only at a terminal state,
5. dry-run intents blocking / polluting a real live session,
6. kill-switch coverage of ``modify_order``,
7. charge-estimate correctness (``trade_date`` + first-sell-of-day DP dedup).

Reuses the ``FakeKite`` / ``FakeClock`` / ``RecordingAlerter`` / ``make_broker``
/ ``_order`` seam from ``tests/live/test_broker.py`` (imported, not
duplicated). Kite is always faked; no test touches the network.

``SimulatedCrash`` subclasses ``BaseException`` (not ``Exception``) on
purpose: the broker's placement error handling catches ``Exception``, so a
``SimulatedCrash`` raised from inside ``kite.place_order`` unwinds straight
through ``place_order`` exactly like a process death -- nothing after the API
call runs, which is precisely the crash window under test.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from live.test_broker import (  # noqa: E402 -- test seam reuse
    T0,
    FakeKite,
    RecordingAlerter,
    _order,
    make_broker,
)
from tradingos.broker.killswitch import KillSwitch
from tradingos.config.settings import Settings
from tradingos.core.errors import BrokerError, KillSwitchActive, OrderStateError
from tradingos.core.models import Order, OrderStatus, OrderType, Side
from tradingos.live.broker import _tag_for
from tradingos.paper.ledgerdb import PaperStore


class SimulatedCrash(BaseException):
    """Process death mid-flow. Deliberately NOT an Exception subclass -- see
    module docstring."""


def _complete_row(order: Order, *, filled: int, price: float, status: str = "COMPLETE") -> dict:
    return {
        "order_id": order.broker_order_id,
        "tag": order.tag,
        "tradingsymbol": order.symbol,
        "transaction_type": order.side.value,
        "status": status,
        "filled_quantity": filled,
        "quantity": order.qty,
        "average_price": price,
        "product": "CNC",
        "order_timestamp": datetime(2024, 1, 15, 10, 0, 5),
        "status_message": None,
    }


# --------------------------------------------------------------------------
# 1. The place-vs-journal crash window (finding #1, CRITICAL)
# --------------------------------------------------------------------------


class TestPlaceJournalCrashWindow:
    def test_intent_is_journalled_before_the_kite_call(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """A crash BETWEEN kite.place_order succeeding and the journal write
        must still leave a (write-ahead) journal row -- the row that blocks a
        blind re-place on restart."""
        store = PaperStore(tmp_path / "live.sqlite", "cw-wal")
        kite = FakeKite(register_placements=True, crash_after_place=SimulatedCrash())
        broker = make_broker(settings, store, kite, dry_run=False)

        with pytest.raises(SimulatedCrash):
            broker.place_order(_order("cw-1"))

        assert len(kite.place_calls) == 1  # the order IS live at the broker
        row = store.get_order("cw-1")
        assert row is not None, "no write-ahead journal row: a restart would re-place"
        assert row.status == OrderStatus.OPEN
        assert row.broker_order_id is None  # outcome never learned = unconfirmed
        assert row.tag == _tag_for("cw-1")

    def test_restart_after_crash_post_kite_adopts_instead_of_replacing(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """THE double-order regression: crash after Kite accepted, restart,
        retry the same client_order_id -> exactly ONE order at the broker."""
        store = PaperStore(tmp_path / "live.sqlite", "cw-adopt")
        kite = FakeKite(register_placements=True, crash_after_place=SimulatedCrash())
        broker1 = make_broker(settings, store, kite, dry_run=False)
        with pytest.raises(SimulatedCrash):
            broker1.place_order(_order("cw-2"))
        assert len(kite.place_calls) == 1

        # Fresh process: new broker, SAME journal, SAME Kite account state.
        broker2 = make_broker(settings, store, kite, dry_run=False)

        # Startup recovery resolved the unconfirmed row against the order book.
        recovered = store.get_order("cw-2")
        assert recovered.broker_order_id == "KITE1"
        assert recovered.status == OrderStatus.OPEN

        # And the scheduler's retry of the same order must NOT place again.
        replaced = broker2.place_order(_order("cw-2"))
        assert replaced.broker_order_id == "KITE1"
        assert len(kite.place_calls) == 1  # still exactly one placement

    def test_restart_after_crash_pre_kite_reverts_to_pending_and_places_once(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """Crash after the write-ahead save but BEFORE the request reached
        Kite: restart must confirm absence at the broker, roll the row back to
        PENDING, and the retry must place exactly one real order."""
        store = PaperStore(tmp_path / "live.sqlite", "cw-revert")
        kite = FakeKite(register_placements=True, raises={"place_order": SimulatedCrash()})
        broker1 = make_broker(settings, store, kite, dry_run=False)
        with pytest.raises(SimulatedCrash):
            broker1.place_order(_order("cw-3"))
        assert store.get_order("cw-3").status == OrderStatus.OPEN  # unconfirmed

        kite.clear_raises()  # the outage is over
        broker2 = make_broker(settings, store, kite, dry_run=False)

        # Startup recovery: tag absent from the order book -> back to PENDING.
        assert store.get_order("cw-3").status == OrderStatus.PENDING

        placed = broker2.place_order(_order("cw-3"))
        assert placed.status == OrderStatus.OPEN
        assert placed.broker_order_id == "KITE1"
        # Exactly one order ever existed at the broker.
        assert len(kite.kite_rows_for_tests()) == 1

    def test_startup_with_unreadable_order_book_keeps_blocking_a_blind_replace(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """If the order book cannot be read at startup, the unconfirmed row
        must stay OPEN (never guessed) and a re-place of that id must raise
        rather than hit kite.place_order."""
        store = PaperStore(tmp_path / "live.sqlite", "cw-unreadable")
        store.save_order(
            Order(
                client_order_id="cw-4",
                symbol="AAA",
                side=Side.BUY,
                qty=10,
                order_type=OrderType.MARKET,
                status=OrderStatus.OPEN,
                broker_order_id=None,
                tag=_tag_for("cw-4"),
                created_at=T0,
            )
        )
        kite = FakeKite(raises={"orders": ValueError("api down")})
        broker = make_broker(settings, store, kite, dry_run=False)  # must not raise

        assert store.get_order("cw-4").status == OrderStatus.OPEN  # untouched

        with pytest.raises(BrokerError):
            broker.place_order(_order("cw-4"))
        assert kite.place_calls == []  # never blindly re-placed

        # Once the book is readable (and empty), sync resolves it to PENDING.
        kite.clear_raises()
        changed = broker.sync_orders()
        assert [o.client_order_id for o in changed] == ["cw-4"]
        assert store.get_order("cw-4").status == OrderStatus.PENDING


# --------------------------------------------------------------------------
# 2. Ambiguous placement failures (finding #2)
# --------------------------------------------------------------------------


class TestAmbiguousPlaceFailure:
    def test_exception_after_broker_accepted_adopts_and_does_not_reject(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """A timeout-style exception AFTER Kite accepted the order must not
        journal REJECTED (the order is live!) -- the broker resolves by tag
        and adopts the real order."""
        store = PaperStore(tmp_path / "live.sqlite", "amb-adopt")
        kite = FakeKite(
            register_placements=True, crash_after_place=RuntimeError("connection reset")
        )
        alerter = RecordingAlerter()
        broker = make_broker(settings, store, kite, dry_run=False, alerter=alerter)

        placed = broker.place_order(_order("amb-1"))

        assert placed.status == OrderStatus.OPEN
        assert placed.broker_order_id == "KITE1"
        assert alerter.rejections == []
        assert store.get_order("amb-1").broker_order_id == "KITE1"
        assert len(kite.place_calls) == 1

    def test_confirmed_absent_failure_rejects_alerts_and_raises(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """A failure whose tag is confirmed absent from the order book is a
        genuine rejection: journalled REJECTED, alerted, raised (the
        pre-existing contract)."""
        store = PaperStore(tmp_path / "live.sqlite", "amb-reject")
        kite = FakeKite(raises={"place_order": ValueError("insufficient margin")})
        alerter = RecordingAlerter()
        broker = make_broker(settings, store, kite, dry_run=False, alerter=alerter)

        with pytest.raises(BrokerError, match="insufficient margin"):
            broker.place_order(_order("amb-2"))

        stored = store.get_order("amb-2")
        assert stored.status == OrderStatus.REJECTED
        assert "insufficient margin" in (stored.status_message or "")
        assert len(alerter.rejections) == 1

    def test_unreadable_order_book_after_failure_leaves_unconfirmed_not_rejected(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """Placement raised AND the order book is unreadable: the outcome is
        unknown, so the row must stay OPEN/unconfirmed (NOT REJECTED, NOT
        retried blindly) until reconciliation can decide."""
        store = PaperStore(tmp_path / "live.sqlite", "amb-unknown")
        kite = FakeKite(
            raises={"place_order": ValueError("reset"), "orders": ValueError("down")}
        )
        alerter = RecordingAlerter()
        broker = make_broker(settings, store, kite, dry_run=False, alerter=alerter)

        with pytest.raises(BrokerError, match="NOT be blindly re-placed"):
            broker.place_order(_order("amb-3"))

        stored = store.get_order("amb-3")
        assert stored.status == OrderStatus.OPEN
        assert stored.broker_order_id is None
        assert alerter.rejections == []  # never burned as REJECTED on a guess


# --------------------------------------------------------------------------
# 3. Cancel/fill race (finding #3)
# --------------------------------------------------------------------------


class TestCancelFillRace:
    def test_sync_corrects_local_cancel_that_actually_filled(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "race-fill")
        kite = FakeKite()
        alerter = RecordingAlerter()
        broker = make_broker(settings, store, kite, dry_run=False, alerter=alerter)
        order = broker.place_order(_order("race-1"))
        broker.cancel_order("race-1")
        assert store.get_order("race-1").status == OrderStatus.CANCELLED

        # ...but the broker filled it before the cancel took effect.
        kite.set_orders([_complete_row(order, filled=10, price=101.0)])
        changed = broker.sync_orders()

        assert [o.client_order_id for o in changed] == ["race-1"]
        stored = store.get_order("race-1")
        assert stored.status == OrderStatus.COMPLETE
        assert stored.filled_qty == 10
        fills = store.all_fills()
        assert len(fills) == 1
        assert fills[0].qty == 10 and fills[0].price == 101.0
        assert len(alerter.fills) == 1

        # Idempotent: a second sync must not re-record the fill.
        assert broker.sync_orders() == []
        assert len(store.all_fills()) == 1

    def test_sync_records_partial_fill_learned_on_locally_cancelled_order(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "race-partial")
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=False)
        order = broker.place_order(_order("race-2"))
        broker.cancel_order("race-2")

        kite.set_orders([_complete_row(order, filled=4, price=100.5, status="CANCELLED")])
        broker.sync_orders()

        stored = store.get_order("race-2")
        assert stored.status == OrderStatus.CANCELLED
        assert stored.filled_qty == 4
        fills = store.all_fills()
        assert len(fills) == 1
        assert fills[0].qty == 4 and fills[0].price == 100.5

        assert broker.sync_orders() == []
        assert len(store.all_fills()) == 1


# --------------------------------------------------------------------------
# 4. Partial fill then terminal (finding #4)
# --------------------------------------------------------------------------


class TestPartialFillThenTerminal:
    def test_cancelled_at_broker_with_partial_fill_records_the_filled_part(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "pt-cancel")
        kite = FakeKite()
        alerter = RecordingAlerter()
        broker = make_broker(settings, store, kite, dry_run=False, alerter=alerter)
        order = broker.place_order(_order("pt-1"))

        kite.set_orders([_complete_row(order, filled=3, price=100.5, status="CANCELLED")])
        broker.sync_orders()

        stored = store.get_order("pt-1")
        assert stored.status == OrderStatus.CANCELLED
        assert stored.filled_qty == 3
        fills = store.all_fills()
        assert len(fills) == 1, "the 3 filled shares are real money and must be journalled"
        assert fills[0].qty == 3 and fills[0].price == 100.5
        assert len(alerter.fills) == 1
        assert len(alerter.rejections) == 1  # the cancellation still alerts

        assert broker.sync_orders() == []
        assert len(store.all_fills()) == 1

    def test_partial_seen_working_then_cancelled_records_exactly_one_fill(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """OPEN -> PARTIAL(3) (no fill journalled while working) -> CANCELLED(3):
        the terminal sync must record the 3 shares exactly once."""
        store = PaperStore(tmp_path / "live.sqlite", "pt-two-step")
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=False)
        order = broker.place_order(_order("pt-2"))

        kite.set_orders([_complete_row(order, filled=3, price=100.5, status="OPEN")])
        broker.sync_orders()
        assert store.get_order("pt-2").status == OrderStatus.PARTIAL
        assert store.all_fills() == []  # not journalled while still working

        kite.set_orders([_complete_row(order, filled=3, price=100.5, status="CANCELLED")])
        broker.sync_orders()

        stored = store.get_order("pt-2")
        assert stored.status == OrderStatus.CANCELLED
        fills = store.all_fills()
        assert len(fills) == 1
        assert fills[0].qty == 3

        assert broker.sync_orders() == []
        assert len(store.all_fills()) == 1


# --------------------------------------------------------------------------
# 5. Dry-run rehearsal vs the real session (finding #5)
# --------------------------------------------------------------------------


class TestDryRunThenLive:
    def test_live_place_supersedes_a_dry_run_intent(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """A morning dry-run rehearsal journals the intent as OPEN/DRY-n; the
        real session for the same client_order_id must still place it (the
        old idempotency gate silently returned the DRY row -> zero real
        orders for the day)."""
        store = PaperStore(tmp_path / "live.sqlite", "dry-live")
        broker_dry = make_broker(settings, store, FakeKite(), dry_run=True)
        rehearsed = broker_dry.place_order(_order("dl-1"))
        assert rehearsed.broker_order_id == "DRY-1"

        kite_live = FakeKite()
        broker_live = make_broker(settings, store, kite_live, dry_run=False)
        placed = broker_live.place_order(_order("dl-1"))

        assert placed.status == OrderStatus.OPEN
        assert placed.broker_order_id == "KITE1"
        assert len(kite_live.place_calls) == 1
        # And the supersede is itself idempotent.
        again = broker_live.place_order(_order("dl-1"))
        assert again.broker_order_id == "KITE1"
        assert len(kite_live.place_calls) == 1

    def test_planned_orders_can_include_dry_consumed_rows(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "dry-queue")
        day = date(2024, 1, 15)
        store.save_order(
            Order(
                client_order_id="q-pending",
                symbol="AAA",
                side=Side.BUY,
                qty=5,
                order_type=OrderType.MARKET,
            ),
            planned_for=day,
        )
        store.save_order(
            Order(
                client_order_id="q-dry",
                symbol="BBB",
                side=Side.BUY,
                qty=5,
                order_type=OrderType.MARKET,
                status=OrderStatus.OPEN,
                broker_order_id="DRY-7",
                created_at=T0,
            ),
            planned_for=day,
        )

        default = {o.client_order_id for o in store.planned_orders(day)}
        assert default == {"q-pending"}
        with_dry = {
            o.client_order_id for o in store.planned_orders(day, include_dry_placed=True)
        }
        assert with_dry == {"q-pending", "q-dry"}

    def test_live_cancel_of_a_dry_intent_never_hits_kite(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "dry-cancel")
        broker_dry = make_broker(settings, store, FakeKite(), dry_run=True)
        broker_dry.place_order(_order("dc-1"))

        kite_live = FakeKite()
        broker_live = make_broker(settings, store, kite_live, dry_run=False)
        cancelled = broker_live.cancel_order("dc-1")

        assert cancelled.status == OrderStatus.CANCELLED
        assert [c for c, _ in kite_live.calls if c == "cancel_order"] == []


# --------------------------------------------------------------------------
# 6. Kill switch gaps: modify (finding #6) and never-placed guards (#8)
# --------------------------------------------------------------------------


class TestModifyCancelGuards:
    def test_modify_is_blocked_while_the_kill_switch_is_engaged(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "ks-modify")
        ks = KillSwitch(tmp_path / "KILL_SWITCH")
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=False, kill_switch=ks)
        broker.place_order(_order("ksm-1", order_type=OrderType.LIMIT, limit_price=95.0))

        ks.engage("halt")
        with pytest.raises(KillSwitchActive):
            broker.modify_order("ksm-1", qty=100)

        stored = store.get_order("ksm-1")
        assert stored.qty == 10  # untouched, still working as accepted
        assert [c for c, _ in kite.calls if c == "modify_order"] == []

        # Cancels must STAY allowed while engaged (they only reduce risk).
        cancelled = broker.cancel_order("ksm-1")
        assert cancelled.status == OrderStatus.CANCELLED

    def test_modify_of_a_never_placed_order_raises_instead_of_calling_kite(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "np-modify")
        day = date(2024, 1, 15)
        store.save_order(
            Order(
                client_order_id="np-1",
                symbol="AAA",
                side=Side.BUY,
                qty=10,
                order_type=OrderType.LIMIT,
                limit_price=95.0,
            ),
            planned_for=day,
        )
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=False)

        with pytest.raises(OrderStateError, match="not .*placed at the broker"):
            broker.modify_order("np-1", qty=20)
        assert [c for c, _ in kite.calls if c == "modify_order"] == []

    def test_cancel_of_a_pending_planned_order_is_journal_only(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "np-cancel")
        day = date(2024, 1, 15)
        store.save_order(
            Order(
                client_order_id="np-2",
                symbol="AAA",
                side=Side.BUY,
                qty=10,
                order_type=OrderType.MARKET,
            ),
            planned_for=day,
        )
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=False)

        cancelled = broker.cancel_order("np-2")

        assert cancelled.status == OrderStatus.CANCELLED
        assert [c for c, _ in kite.calls if c == "cancel_order"] == []

    def test_cancel_of_an_unconfirmed_order_resolves_by_tag_first(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """Cancelling an unconfirmed write-ahead row must consult the order
        book: found -> adopt the broker id and cancel it for real; absent ->
        journal-only cancel."""
        store = PaperStore(tmp_path / "live.sqlite", "unc-cancel")
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=False)
        # Injected AFTER construction so startup recovery does not resolve it.
        store.save_order(
            Order(
                client_order_id="uc-1",
                symbol="AAA",
                side=Side.BUY,
                qty=10,
                order_type=OrderType.MARKET,
                status=OrderStatus.OPEN,
                broker_order_id=None,
                tag=_tag_for("uc-1"),
                created_at=T0,
            )
        )
        kite.set_orders(
            [
                {
                    "order_id": "KITE99",
                    "tag": _tag_for("uc-1"),
                    "tradingsymbol": "AAA",
                    "transaction_type": "BUY",
                    "status": "OPEN",
                    "filled_quantity": 0,
                    "quantity": 10,
                    "average_price": 0.0,
                    "product": "CNC",
                    "order_timestamp": None,
                    "status_message": None,
                }
            ]
        )

        cancelled = broker.cancel_order("uc-1")

        assert cancelled.status == OrderStatus.CANCELLED
        cancel_calls = [kw for c, kw in kite.calls if c == "cancel_order"]
        assert cancel_calls == [{"variety": "regular", "order_id": "KITE99"}]


# --------------------------------------------------------------------------
# 7. Charge-estimate correctness (finding #9 / task item 3)
# --------------------------------------------------------------------------


class TestSyncFillChargeEstimates:
    def test_trade_date_and_first_sell_dedup_flow_into_the_cost_model(
        self, settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "charges")
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=False)
        s1 = broker.place_order(_order("chg-1", side=Side.SELL, qty=5))
        s2 = broker.place_order(_order("chg-2", side=Side.SELL, qty=5))
        kite.set_orders(
            [
                _complete_row(s1, filled=5, price=100.0),
                _complete_row(s2, filled=5, price=100.0),
            ]
        )

        recorded: list[dict] = []
        real = broker._cost_model.order_charges  # noqa: SLF001 -- spy on the seam

        def spy(*args: object, **kwargs: object):
            recorded.append(dict(kwargs))
            return real(*args, **kwargs)

        monkeypatch.setattr(broker._cost_model, "order_charges", spy)  # noqa: SLF001
        broker.sync_orders()

        fills = store.all_fills()
        assert len(fills) == 2
        assert len(recorded) == 2
        fill_day = date(2024, 1, 15)
        assert [k.get("trade_date") for k in recorded] == [fill_day, fill_day]
        # DP charge applies to the FIRST sell of the scrip that day only.
        assert [k.get("first_sell_of_scrip_today") for k in recorded] == [True, False]
        assert fills[0].charges > fills[1].charges  # the DP delta is real money

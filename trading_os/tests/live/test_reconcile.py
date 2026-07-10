"""Tests for live/reconcile.py: reconcile_orders / reconcile_positions / reconcile_once.

Reuses the ``FakeKite`` / ``FakeClock`` / ``RecordingAlerter`` / ``make_broker`` /
``_order`` / ``_permissive_limits`` test seam from ``tests/live/test_broker.py``
(imported, not duplicated -- that file is never modified here). Kite is always
faked; no test touches the network.
"""

from __future__ import annotations

from pathlib import Path

from live.test_broker import (
    FakeKite,
    RecordingAlerter,
    _order,
    make_broker,
)
from tradingos.config.settings import Settings
from tradingos.core.models import OrderStatus
from tradingos.live.reconcile import Mismatch, reconcile_once, reconcile_orders, reconcile_positions
from tradingos.paper.ledgerdb import PaperStore


class RiskRecordingAlerter(RecordingAlerter):
    """RecordingAlerter, plus recording of alert_risk calls (test_broker.py's
    RecordingAlerter doesn't need those, so we extend it here rather than
    touching that file)."""

    def __init__(self) -> None:
        super().__init__()
        self.risk_alerts: list[str] = []

    def alert_risk(self, message: str) -> bool:
        self.risk_alerts.append(message)
        return True


def _kite_row(order, **overrides: object) -> dict:
    """A kite.orders() row matching ``order`` exactly, with overrides applied."""
    row: dict[str, object] = {
        "order_id": order.broker_order_id,
        "tag": order.tag,
        "tradingsymbol": order.symbol,
        "transaction_type": order.side.value,
        "status": "OPEN",
        "filled_quantity": 0,
        "quantity": order.qty,
        "average_price": 0.0,
        "product": "CNC",
        "order_timestamp": None,
        "status_message": None,
    }
    row.update(overrides)
    return row


# --------------------------------------------------------------------------
# reconcile_orders
# --------------------------------------------------------------------------


class TestReconcileOrdersStatusQuo:
    def test_matching_order_book_yields_no_mismatches(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "quo")
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=False)
        order = broker.place_order(_order("quo-1"))
        kite.set_orders([_kite_row(order)])  # same symbol/side/qty, still OPEN

        assert reconcile_orders(broker) == []


class TestReconcileOrdersMissingAtBroker:
    def test_open_journal_order_absent_from_kite_book_flags_missing(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "missing")
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=False)
        order = broker.place_order(_order("miss-1"))
        kite.set_orders([])  # broker has no record of it at all

        mismatches = reconcile_orders(broker)

        assert len(mismatches) == 1
        m = mismatches[0]
        assert m.kind == "missing_at_broker"
        assert m.client_order_id == order.client_order_id
        assert m.symbol == "AAA"
        assert order.broker_order_id in m.detail


class TestReconcileOrdersQtyDrift:
    def test_tag_matched_row_with_different_quantity_flags_qty_drift(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "qtydrift")
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=False)
        order = broker.place_order(_order("qd-1", qty=10))
        kite.set_orders([_kite_row(order, quantity=5)])  # broker thinks qty=5

        mismatches = reconcile_orders(broker)

        assert len(mismatches) == 1
        m = mismatches[0]
        assert m.kind == "qty_drift"
        assert m.client_order_id == "qd-1"
        assert m.symbol == "AAA"
        assert "qty=10" in m.detail and "5" in m.detail

    def test_qty_drift_matched_by_tag_when_order_id_unknown(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """Defensive-fallback matching: sync_orders (and reconcile) join by
        broker_order_id first, tag second -- exercise the tag-only path."""
        store = PaperStore(tmp_path / "live.sqlite", "qtydrift-tag")
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=False)
        order = broker.place_order(_order("qd-2", qty=10))
        row = _kite_row(order, order_id="SOME-OTHER-ID", quantity=3)
        kite.set_orders([row])

        mismatches = reconcile_orders(broker)

        assert len(mismatches) == 1
        assert mismatches[0].kind == "qty_drift"
        assert mismatches[0].client_order_id == "qd-2"


class TestReconcileOrdersUnattributedRowsIgnored:
    def test_kite_row_matching_no_journal_order_is_not_flagged(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        """A kite order that isn't ours (different order_id/tag entirely) must
        NOT be flagged as unknown_at_broker -- see module docstring: tags are
        opaque hashes, so lookup-miss attribution is meaningless."""
        store = PaperStore(tmp_path / "live.sqlite", "foreign")
        kite = FakeKite()
        broker = make_broker(settings, store, kite, dry_run=False)
        kite.set_orders(
            [
                {
                    "order_id": "SOMEONE-ELSES-ORDER",
                    "tag": "not-ours-at-all-12",
                    "tradingsymbol": "ZZZ",
                    "transaction_type": "BUY",
                    "status": "OPEN",
                    "filled_quantity": 0,
                    "quantity": 100,
                    "average_price": 0.0,
                    "product": "CNC",
                    "order_timestamp": None,
                    "status_message": None,
                }
            ]
        )

        assert reconcile_orders(broker) == []


class TestReconcileOrdersSyncFirst:
    def test_sync_orders_runs_first_so_a_completed_order_does_not_also_surface(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "syncfirst")
        kite = FakeKite()
        alerter = RiskRecordingAlerter()
        broker = make_broker(settings, store, kite, dry_run=False, alerter=alerter)
        order = broker.place_order(_order("sf-1", qty=10))
        kite.set_orders(
            [_kite_row(order, status="COMPLETE", filled_quantity=10, average_price=101.0)]
        )

        mismatches = reconcile_orders(broker)

        # sync_orders already journalled it COMPLETE -- no status_drift left over.
        assert mismatches == []
        assert broker.get_order("sf-1").status == OrderStatus.COMPLETE
        assert len(alerter.fills) == 1  # the fill sync_orders recorded


# --------------------------------------------------------------------------
# reconcile_positions
# --------------------------------------------------------------------------


class TestReconcilePositions:
    def test_lower_broker_qty_flags_position_drift(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "pos-lower")
        kite = FakeKite(
            holdings_response=[
                {
                    "tradingsymbol": "AAA",
                    "quantity": 5,
                    "t1_quantity": 0,
                    "average_price": 100.0,
                    "last_price": 110.0,
                }
            ]
        )
        broker = make_broker(settings, store, kite, dry_run=False)

        mismatches = reconcile_positions(broker, {"AAA": 10})

        assert mismatches == [
            Mismatch(
                kind="position_drift",
                client_order_id=None,
                symbol="AAA",
                detail="expected qty=10 vs broker qty=5",
            )
        ]

    def test_extra_symbol_at_broker_flags_position_drift(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "pos-extra")
        kite = FakeKite(
            holdings_response=[
                {
                    "tradingsymbol": "AAA",
                    "quantity": 10,
                    "t1_quantity": 0,
                    "average_price": 100.0,
                    "last_price": 110.0,
                },
                {
                    "tradingsymbol": "BBB",
                    "quantity": 3,
                    "t1_quantity": 0,
                    "average_price": 50.0,
                    "last_price": 55.0,
                },
            ]
        )
        broker = make_broker(settings, store, kite, dry_run=False)

        mismatches = reconcile_positions(broker, {"AAA": 10})

        assert mismatches == [
            Mismatch(
                kind="position_drift",
                client_order_id=None,
                symbol="BBB",
                detail="expected qty=0 vs broker qty=3",
            )
        ]

    def test_symbol_missing_at_broker_flags_position_drift(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "pos-missing")
        kite = FakeKite()  # empty holdings and positions
        broker = make_broker(settings, store, kite, dry_run=False)

        mismatches = reconcile_positions(broker, {"AAA": 10})

        assert mismatches == [
            Mismatch(
                kind="position_drift",
                client_order_id=None,
                symbol="AAA",
                detail="expected qty=10 vs broker qty=0",
            )
        ]

    def test_matching_positions_yield_no_mismatch(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "pos-ok")
        kite = FakeKite(
            holdings_response=[
                {
                    "tradingsymbol": "AAA",
                    "quantity": 10,
                    "t1_quantity": 0,
                    "average_price": 100.0,
                    "last_price": 110.0,
                }
            ]
        )
        broker = make_broker(settings, store, kite, dry_run=False)

        assert reconcile_positions(broker, {"AAA": 10}) == []


# --------------------------------------------------------------------------
# dry-run short-circuit
# --------------------------------------------------------------------------


class TestDryRunShortCircuit:
    def test_reconcile_once_is_a_noop_with_no_kite_calls_in_dry_run(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "dry")
        kite = FakeKite()
        alerter = RiskRecordingAlerter()
        broker = make_broker(settings, store, kite, dry_run=True, alerter=alerter)
        broker.place_order(_order("dry-1"))  # journalled locally only; itself makes read calls
        calls_before_reconcile = len(kite.calls)

        result = reconcile_once(broker, expected_positions={"AAA": 10}, alerter=alerter)

        assert result == []
        # reconcile_once itself must not touch Kite at all in dry-run -- no new calls.
        assert kite.calls[calls_before_reconcile:] == []
        assert alerter.risk_alerts == []


# --------------------------------------------------------------------------
# reconcile_once: consolidated alert
# --------------------------------------------------------------------------


class TestReconcileOnceConsolidatedAlert:
    def test_multiple_mismatches_produce_exactly_one_alert(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "consolidated")
        kite = FakeKite()
        alerter = RiskRecordingAlerter()
        broker = make_broker(settings, store, kite, dry_run=False, alerter=alerter)

        # (1) missing_at_broker
        missing = broker.place_order(_order("c-missing"))
        # (2) qty_drift
        drifted = broker.place_order(_order("c-drift", qty=10))
        kite.set_orders([_kite_row(drifted, quantity=1)])
        # (3) position_drift, via expected_positions

        mismatches = reconcile_once(broker, expected_positions={"AAA": 999}, alerter=alerter)

        kinds = {m.kind for m in mismatches}
        assert "missing_at_broker" in kinds
        assert "qty_drift" in kinds
        assert "position_drift" in kinds
        assert len(mismatches) == 3

        assert len(alerter.risk_alerts) == 1  # ONE consolidated alert, not one per mismatch
        message = alerter.risk_alerts[0]
        assert "3 reconciliation mismatch" in message
        assert missing.client_order_id in message
        assert drifted.client_order_id in message

    def test_no_mismatches_sends_no_alert(self, settings: Settings, tmp_path: Path) -> None:
        store = PaperStore(tmp_path / "live.sqlite", "clean")
        kite = FakeKite()
        alerter = RiskRecordingAlerter()
        broker = make_broker(settings, store, kite, dry_run=False, alerter=alerter)
        order = broker.place_order(_order("clean-1"))
        kite.set_orders([_kite_row(order)])

        mismatches = reconcile_once(broker, alerter=alerter)

        assert mismatches == []
        assert alerter.risk_alerts == []

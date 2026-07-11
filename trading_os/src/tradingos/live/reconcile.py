"""Phase 6 order / position reconciliation loop.

Polls the broker's Kite order book (and, when asked, its holdings+positions)
and diffs them against tradingos' own journal / the strategy's believed
state, surfacing whatever ``ZerodhaLiveBroker.sync_orders`` cannot fix on its
own as a :class:`Mismatch`. This module is a *detection* layer only -- it
never mutates orders or positions. Every mismatch is logged at ERROR and,
when an ``alerter`` is supplied, folded into ONE consolidated
``alert_risk`` message so a badly-drifted book cannot flood Telegram with
one alert per row.

Attribution caveat (read before touching the order-matching logic below):
Kite order *tags* are the only join key back to our journal (see
``live/broker.py``'s tag scheme, ``sha1(client_order_id).hexdigest()[:18]``).
Tags are opaque hashes, so a kite order-book row that matches NEITHER a
journal ``broker_order_id`` NOR a journal ``tag`` cannot be safely attributed
to this strategy -- it may belong to a different ``strategy_id`` sharing the
same Zerodha account, or be an order placed by hand through the Kite app, or
anything else outside the platform's view. Such rows are deliberately NOT
flagged (there is no ``"unknown_at_broker"`` mismatch emitted by this
module today, even though it is a valid :class:`Mismatch.kind` value in the
contract, reserved for a future scheme that can attribute more precisely).
Only kite rows that DO match one of our own journal orders (by
``broker_order_id`` or ``tag``) but disagree with it on symbol/side/qty are
surfaced, as ``"qty_drift"`` -- that disagreement IS attributable to us.

dry-run: ``ZerodhaLiveBroker`` in dry-run never sends anything to Kite, so
there is nothing at the broker to reconcile against. Both
``reconcile_orders`` and ``reconcile_positions`` short-circuit to ``[]``
without issuing a single Kite call, keyed off the broker's public
``dry_run`` property. This module also calls the broker's private
``_map_status`` to reuse the exact Kite-status -> ``OrderStatus`` mapping
``sync_orders`` itself uses, rather than keeping a second copy of that
mapping that could silently drift out of sync.
"""

from __future__ import annotations

from dataclasses import dataclass

from tradingos.core.alerts import TelegramAlerter
from tradingos.core.logging import get_logger
from tradingos.core.models import Order, OrderStatus
from tradingos.live.broker import ZerodhaLiveBroker
from tradingos.paper.ledgerdb import DRY_ORDER_ID_PREFIX

logger = get_logger(__name__)


@dataclass(frozen=True)
class Mismatch:
    """One detected disagreement between the journal / strategy state and
    what the broker actually reports."""

    kind: str  # "status_drift" | "missing_at_broker" | "unknown_at_broker" | "qty_drift" | "position_drift"
    client_order_id: str | None
    symbol: str | None
    detail: str  # human-readable, includes both sides' values


def _is_dry_run(broker: ZerodhaLiveBroker) -> bool:
    """Dry-run detection via the broker's public ``dry_run`` property
    (``getattr`` so a minimal test double without the property still works)."""
    return bool(getattr(broker, "dry_run", False))


def _working_orders_by_key(orders: list[Order]) -> tuple[dict[str, Order], dict[str, Order]]:
    """(by broker_order_id, by tag) maps over every journal order that has one
    (terminal or not -- callers filter as needed)."""
    by_broker_id = {o.broker_order_id: o for o in orders if o.broker_order_id}
    by_tag = {o.tag: o for o in orders if o.tag}
    return by_broker_id, by_tag


def reconcile_orders(broker: ZerodhaLiveBroker) -> list[Mismatch]:
    """Reconcile the journal against the live Kite order book.

    First calls ``broker.sync_orders()`` -- that resolves ordinary status
    drift by updating the journal (recording fills, alerting on rejections)
    for anything it can match by ``broker_order_id`` or ``tag``. This
    function then looks at what sync cannot fix: journal orders that
    disappeared from the broker entirely, kite rows that disagree with their
    matched journal order on symbol/side/qty, and matched pairs whose
    statuses still disagree after sync ran.
    """
    if _is_dry_run(broker):
        logger.info("reconcile_orders: DRY-RUN, nothing exists at the broker to reconcile")
        return []

    broker.sync_orders()  # fixes what it can; changes are reflected in get_orders() below

    kite_rows = broker.kite_orders()
    journal = broker.get_orders()

    kite_by_broker_id = {str(row.get("order_id")): row for row in kite_rows if row.get("order_id")}
    kite_by_tag = {row.get("tag"): row for row in kite_rows if row.get("tag")}

    mismatches: list[Mismatch] = []

    # 1. missing_at_broker -- a journal order we still believe is working
    # (OPEN/PARTIAL) has no matching row anywhere in the kite book. This is
    # the dangerous direction: we think an order is live, the broker has no
    # record of it.
    for order in journal:
        if order.status not in (OrderStatus.OPEN, OrderStatus.PARTIAL):
            continue
        if str(order.broker_order_id or "").startswith(DRY_ORDER_ID_PREFIX):
            # A dry-run rehearsal's journalled intent: nothing was ever sent
            # to the broker, so its absence from the kite book is expected,
            # not drift.
            continue
        found = order.broker_order_id in kite_by_broker_id or (
            order.tag is not None and order.tag in kite_by_tag
        )
        if not found:
            mismatches.append(
                Mismatch(
                    kind="missing_at_broker",
                    client_order_id=order.client_order_id,
                    symbol=order.symbol,
                    detail=(
                        f"journal status={order.status.value} broker_order_id="
                        f"{order.broker_order_id!r} tag={order.tag!r} not found in "
                        f"kite.orders() ({len(kite_rows)} rows)"
                    ),
                )
            )

    # 2. qty_drift / status_drift -- kite rows attributable to us (matched by
    # broker_order_id first, tag as a defensive fallback, mirroring
    # sync_orders's own matching order).
    by_broker_id, by_tag = _working_orders_by_key(journal)
    for row in kite_rows:
        order = by_broker_id.get(str(row.get("order_id")))
        if order is None:
            order = by_tag.get(row.get("tag"))
        if order is None:
            # Not attributable to this strategy's journal -- see module
            # docstring on why this is NOT flagged as "unknown_at_broker".
            continue

        kite_symbol = row.get("tradingsymbol")
        kite_side = row.get("transaction_type")
        kite_qty = row.get("quantity")
        disagrees = (
            (kite_symbol is not None and kite_symbol != order.symbol)
            or (kite_side is not None and kite_side != order.side.value)
            or (kite_qty is not None and int(kite_qty) != order.qty)
        )
        if disagrees:
            mismatches.append(
                Mismatch(
                    kind="qty_drift",
                    client_order_id=order.client_order_id,
                    symbol=order.symbol,
                    detail=(
                        f"journal symbol={order.symbol!r} side={order.side.value!r} "
                        f"qty={order.qty} vs kite symbol={kite_symbol!r} "
                        f"side={kite_side!r} qty={kite_qty!r}"
                    ),
                )
            )
            continue  # a qty/side/symbol mismatch makes a status comparison meaningless

        filled = int(row.get("filled_quantity", 0) or 0)
        kite_status = broker._map_status(row.get("status"), filled)  # noqa: SLF001
        if kite_status != order.status:
            mismatches.append(
                Mismatch(
                    kind="status_drift",
                    client_order_id=order.client_order_id,
                    symbol=order.symbol,
                    detail=(
                        f"journal status={order.status.value} vs kite status="
                        f"{row.get('status')!r} (mapped={kite_status.value}) after sync"
                    ),
                )
            )

    return mismatches


def reconcile_positions(broker: ZerodhaLiveBroker, expected: dict[str, int]) -> list[Mismatch]:
    """Reconcile ``expected`` (symbol -> qty the strategy believes it holds,
    computed by the caller) against the broker's actual holdings + positions,
    summed per symbol. A symbol present on only one side is treated as
    expected/actual qty 0 on the other."""
    if _is_dry_run(broker):
        logger.info("reconcile_positions: DRY-RUN, nothing exists at the broker to reconcile")
        return []

    actual: dict[str, int] = {}
    for pos in (*broker.get_holdings(), *broker.get_positions()):
        actual[pos.symbol] = actual.get(pos.symbol, 0) + pos.qty

    mismatches: list[Mismatch] = []
    for symbol in sorted(set(expected) | set(actual)):
        exp_qty = expected.get(symbol, 0)
        act_qty = actual.get(symbol, 0)
        if exp_qty != act_qty:
            mismatches.append(
                Mismatch(
                    kind="position_drift",
                    client_order_id=None,
                    symbol=symbol,
                    detail=f"expected qty={exp_qty} vs broker qty={act_qty}",
                )
            )
    return mismatches


def reconcile_once(
    broker: ZerodhaLiveBroker,
    expected_positions: dict[str, int] | None = None,
    alerter: TelegramAlerter | None = None,
) -> list[Mismatch]:
    """Run one reconciliation pass: always ``reconcile_orders``, plus
    ``reconcile_positions`` when ``expected_positions`` is given. Every
    mismatch is logged at ERROR; if any are found and ``alerter`` is given, a
    SINGLE consolidated ``alert_risk`` message lists all of them (never one
    alert per mismatch, so a drifted book cannot flood Telegram)."""
    mismatches = reconcile_orders(broker)
    if expected_positions is not None:
        mismatches = mismatches + reconcile_positions(broker, expected_positions)

    for m in mismatches:
        logger.error(
            "reconcile mismatch: kind=%s client_order_id=%s symbol=%s detail=%s",
            m.kind,
            m.client_order_id,
            m.symbol,
            m.detail,
        )

    if mismatches and alerter is not None:
        lines = [
            f"- [{m.kind}] symbol={m.symbol or '-'} client_order_id={m.client_order_id or '-'}: "
            f"{m.detail}"
            for m in mismatches
        ]
        message = f"{len(mismatches)} reconciliation mismatch(es):\n" + "\n".join(lines)
        alerter.alert_risk(message)

    return mismatches


__all__ = ["Mismatch", "reconcile_orders", "reconcile_positions", "reconcile_once"]

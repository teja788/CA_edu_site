"""Pure normalization helpers for the Zerodha live broker adapter.

Keeping broker-protocol mapping here makes the safety-critical orchestration in
``live.broker`` easier to review while leaving the broker's public API intact.
"""

from __future__ import annotations

import hashlib
from datetime import datetime

from tradingos.core.models import OrderStatus
from tradingos.core.timeutils import to_naive_ist

_TERMINAL_KITE_STATUS: dict[str, OrderStatus] = {
    "COMPLETE": OrderStatus.COMPLETE,
    "REJECTED": OrderStatus.REJECTED,
    "CANCELLED": OrderStatus.CANCELLED,
    "CANCELED": OrderStatus.CANCELLED,
}


def tag_for(client_order_id: str) -> str:
    """Return the deterministic, Kite-compatible reconciliation tag."""
    return hashlib.sha1(client_order_id.encode("utf-8")).hexdigest()[:18]


def map_status(kite_status: object, filled_qty: int) -> OrderStatus:
    """Map a Kite status to the conservative internal order status."""
    status = str(kite_status or "").upper()
    terminal = _TERMINAL_KITE_STATUS.get(status)
    if terminal is not None:
        return terminal
    return OrderStatus.PARTIAL if filled_qty > 0 else OrderStatus.OPEN


def optional_float(value: object) -> float | None:
    """Coerce a numeric Kite field, treating zero and missing as absent."""
    if value is None or value == 0:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def parse_timestamp(value: object) -> datetime | None:
    """Parse an SDK or string timestamp into a timezone-naive IST value."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return to_naive_ist(value)
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        try:
            return to_naive_ist(datetime.fromisoformat(value))
        except ValueError:
            return None
    return None


def is_token_exception(exc: BaseException) -> bool:
    """Return whether an exception represents an invalid Kite access token."""
    try:
        from kiteconnect.exceptions import TokenException
    except Exception:  # pragma: no cover -- kiteconnect is normally installed
        return type(exc).__name__ == "TokenException"
    return isinstance(exc, TokenException)

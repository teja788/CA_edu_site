"""Shared data models: bars, orders, fills, positions, trades.

All modules import these; none redefine their own. Order lifecycle:

    PENDING -> OPEN -> PARTIAL -> COMPLETE
                  \\-> COMPLETE
    PENDING/OPEN/PARTIAL -> CANCELLED | REJECTED

Timestamps are timezone-naive and interpreted as IST (Asia/Kolkata) everywhere;
see docs/assumptions.md.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from tradingos.core.errors import OrderStateError

# Canonical OHLCV column order for polars/pandas frames throughout the platform.
OHLCV_COLUMNS = ["ts", "open", "high", "low", "close", "volume"]


class Timeframe(enum.StrEnum):
    # values match Kite Connect historical API interval names
    DAY = "day"
    MINUTE = "minute"


class Side(enum.StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class Product(enum.StrEnum):
    CNC = "CNC"  # delivery
    MIS = "MIS"  # intraday


class OrderType(enum.StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"  # stop-loss limit
    SL_M = "SL-M"  # stop-loss market


class OrderStatus(enum.StrEnum):
    PENDING = "PENDING"  # created locally, not yet accepted
    OPEN = "OPEN"  # accepted, working
    PARTIAL = "PARTIAL"  # partially filled
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

    @property
    def is_terminal(self) -> bool:
        return self in (OrderStatus.COMPLETE, OrderStatus.CANCELLED, OrderStatus.REJECTED)


_ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.OPEN, OrderStatus.CANCELLED, OrderStatus.REJECTED},
    OrderStatus.OPEN: {
        OrderStatus.PARTIAL,
        OrderStatus.COMPLETE,
        OrderStatus.CANCELLED,
        OrderStatus.REJECTED,
    },
    OrderStatus.PARTIAL: {
        OrderStatus.PARTIAL,
        OrderStatus.COMPLETE,
        OrderStatus.CANCELLED,
        OrderStatus.REJECTED,
    },
    OrderStatus.COMPLETE: set(),
    OrderStatus.CANCELLED: set(),
    OrderStatus.REJECTED: set(),
}


def validate_transition(current: OrderStatus, new: OrderStatus) -> None:
    """Raise OrderStateError if current -> new is not a legal transition."""
    if new not in _ALLOWED_TRANSITIONS[current]:
        raise OrderStateError(f"illegal order state transition {current.value} -> {new.value}")


def new_client_order_id() -> str:
    return uuid.uuid4().hex[:16]


class Order(BaseModel):
    """A single order. `client_order_id` is ours (idempotency key);
    `broker_order_id` is assigned by the broker once accepted."""

    client_order_id: str = Field(default_factory=new_client_order_id)
    broker_order_id: str | None = None
    symbol: str
    exchange: str = "NSE"
    side: Side
    qty: int = Field(gt=0)
    filled_qty: int = 0
    order_type: OrderType = OrderType.MARKET
    product: Product = Product.CNC
    limit_price: float | None = None
    trigger_price: float | None = None
    status: OrderStatus = OrderStatus.PENDING
    status_message: str | None = None
    strategy_id: str | None = None
    tag: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def transition(self, new_status: OrderStatus, message: str | None = None) -> None:
        validate_transition(self.status, new_status)
        self.status = new_status
        if message is not None:
            self.status_message = message

    @property
    def remaining_qty(self) -> int:
        return self.qty - self.filled_qty


class Fill(BaseModel):
    """One execution. `charges` is the all-in transaction cost for this fill
    (computed by the cost model), in rupees."""

    client_order_id: str
    symbol: str
    side: Side
    qty: int = Field(gt=0)
    price: float = Field(gt=0)
    ts: datetime
    charges: float = 0.0
    product: Product = Product.CNC


class Position(BaseModel):
    """Net position in one symbol. qty > 0 long, < 0 short (MIS only)."""

    symbol: str
    qty: int = 0
    avg_price: float = 0.0
    product: Product = Product.CNC
    realized_pnl: float = 0.0
    last_price: float | None = None

    @property
    def market_value(self) -> float:
        return (self.last_price or self.avg_price) * self.qty

    @property
    def unrealized_pnl(self) -> float:
        if self.last_price is None:
            return 0.0
        return (self.last_price - self.avg_price) * self.qty


class Quote(BaseModel):
    symbol: str
    last_price: float
    bid: float | None = None
    ask: float | None = None
    volume: int | None = None
    ts: datetime | None = None


class Margins(BaseModel):
    cash_available: float
    used: float = 0.0


class Trade(BaseModel):
    """A closed round trip, for analytics."""

    symbol: str
    qty: int
    entry_ts: datetime
    exit_ts: datetime
    entry_price: float
    exit_price: float
    entry_costs: float = 0.0
    exit_costs: float = 0.0
    exit_reason: str = ""
    strategy_id: str | None = None

    @property
    def gross_pnl(self) -> float:
        return (self.exit_price - self.entry_price) * self.qty

    @property
    def costs(self) -> float:
        return self.entry_costs + self.exit_costs

    @property
    def net_pnl(self) -> float:
        return self.gross_pnl - self.costs

    @property
    def holding_days(self) -> float:
        return (self.exit_ts - self.entry_ts).total_seconds() / 86400.0


class Tick(BaseModel):
    """Minimal live tick used by paper trading."""

    symbol: str
    instrument_token: int
    ts: datetime
    last_price: float
    bid: float | None = None
    ask: float | None = None
    volume: int | None = None

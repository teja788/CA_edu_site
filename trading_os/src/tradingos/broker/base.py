"""Broker abstraction. BacktestBroker, PaperBroker and ZerodhaLiveBroker all
implement this interface, so a strategy graduates backtest -> paper -> live
with a config change only.

The engine package must NOT import concrete brokers (only this interface);
concrete brokers live in tradingos.paper / tradingos.live.
"""

from __future__ import annotations

import abc
from collections.abc import Callable

from tradingos.core.models import Margins, Order, Position, Quote, Tick

TickCallback = Callable[[Tick], None]


class Broker(abc.ABC):
    """Common order/position API. Implementations must be idempotent on
    place_order for the same client_order_id (never double-place)."""

    @abc.abstractmethod
    def place_order(self, order: Order) -> Order:
        """Submit an order. Returns the order with broker_order_id/status set.
        Must raise RiskViolation/KillSwitchActive rather than silently drop."""

    @abc.abstractmethod
    def modify_order(
        self,
        client_order_id: str,
        qty: int | None = None,
        limit_price: float | None = None,
        trigger_price: float | None = None,
    ) -> Order:
        ...

    @abc.abstractmethod
    def cancel_order(self, client_order_id: str) -> Order:
        ...

    @abc.abstractmethod
    def get_order(self, client_order_id: str) -> Order:
        ...

    @abc.abstractmethod
    def get_orders(self) -> list[Order]:
        """All orders known for the current session/day."""

    @abc.abstractmethod
    def get_positions(self) -> list[Position]:
        """Intraday/net positions (MIS and unsettled CNC)."""

    @abc.abstractmethod
    def get_holdings(self) -> list[Position]:
        """Settled delivery holdings."""

    @abc.abstractmethod
    def get_margins(self) -> Margins:
        ...

    @abc.abstractmethod
    def get_quote(self, symbols: list[str]) -> dict[str, Quote]:
        ...

    def stream_ticks(self, symbols: list[str], callback: TickCallback) -> None:
        """Subscribe to live ticks. Backtest broker raises NotImplementedError."""
        raise NotImplementedError(f"{type(self).__name__} does not stream ticks")

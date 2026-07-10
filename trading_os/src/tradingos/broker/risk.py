"""Pre-trade risk limits and the stateless checker that enforces them.

Every rule raises :class:`~tradingos.core.errors.RiskViolation` (or the
kill-switch's subclass thereof, checked separately by
:class:`~tradingos.broker.killswitch.KillSwitch`) naming the rule, the
observed value and the configured limit. All limits are *inclusive-pass*:
a value exactly at the limit passes, only a value strictly over the limit
is a violation — except where the semantics below explicitly say otherwise
(orders-per-day is checked against orders already accepted today, so
``orders_today == max_orders_per_day`` is itself already a violation: one
more order would be the (max+1)-th).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from tradingos.config.settings import Settings
from tradingos.core.errors import RiskViolation
from tradingos.core.models import Order, Side
from tradingos.core.timeutils import MARKET_CLOSE, MARKET_OPEN, is_market_hours, now_ist
from tradingos.data.calendar import NSECalendar


@dataclass(frozen=True)
class RiskLimits:
    max_order_value: float
    max_position_pct: float  # of current equity, per symbol, post-order
    max_daily_loss: float  # rupees; breach when day_start_equity - equity_now > this
    max_orders_per_day: int
    restricted_symbols: frozenset[str] = frozenset()
    market_hours_only: bool = True

    @classmethod
    def from_settings(
        cls,
        settings: Settings,
        *,
        restricted_symbols: Iterable[str] = (),
        market_hours_only: bool = True,
    ) -> RiskLimits:
        return cls(
            max_order_value=settings.max_order_value,
            max_position_pct=settings.max_position_pct,
            max_daily_loss=settings.max_daily_loss,
            max_orders_per_day=settings.max_orders_per_day,
            restricted_symbols=frozenset(restricted_symbols),
            market_hours_only=market_hours_only,
        )


class PreTradeRiskChecker:
    """Stateless: caller supplies current state. Each rule raises RiskViolation with a
    message naming the rule, the observed value and the limit. Check order: restricted
    symbol → market hours/trading day → orders-per-day → order value → daily loss →
    position %. All limits are inclusive-pass (violation only when strictly over)."""

    def __init__(self, limits: RiskLimits, calendar: NSECalendar | None = None) -> None:
        self.limits = limits
        self.calendar = calendar or NSECalendar()

    def check(
        self,
        order: Order,
        *,
        price: float,
        equity: float,
        positions: dict[str, int],
        orders_today: int,
        day_start_equity: float,
        now: datetime | None = None,
    ) -> None:
        limits = self.limits

        # 1. restricted symbol
        if order.symbol in limits.restricted_symbols:
            raise RiskViolation(
                f"restricted symbol: {order.symbol!r} is on the restricted list "
                f"({sorted(limits.restricted_symbols)})"
            )

        # 2. market hours / trading day
        if limits.market_hours_only:
            ts = now if now is not None else now_ist()
            if not self.calendar.is_trading_day(ts.date()):
                raise RiskViolation(f"market hours: {ts.date()} is not an NSE trading day")
            if not is_market_hours(ts):
                raise RiskViolation(
                    f"market hours: {ts.time()} is outside session hours "
                    f"{MARKET_OPEN}-{MARKET_CLOSE}"
                )

        # 3. orders per day
        if orders_today >= limits.max_orders_per_day:
            raise RiskViolation(
                f"orders per day: {orders_today} orders already placed today "
                f">= limit {limits.max_orders_per_day}"
            )

        # 4. order value
        order_value = order.qty * price
        if order_value > limits.max_order_value:
            raise RiskViolation(
                f"order value: {order_value} > limit {limits.max_order_value}"
            )

        # 5. daily loss (BUYs only; SELLs de-risk and always pass this rule)
        if order.side == Side.BUY:
            loss_so_far = day_start_equity - equity
            if loss_so_far > limits.max_daily_loss:
                raise RiskViolation(
                    f"daily loss: {loss_so_far} > limit {limits.max_daily_loss}"
                )

        # 6. position % of equity, post-order (BUYs only)
        if order.side == Side.BUY:
            if equity <= 0:
                raise RiskViolation(
                    f"position pct: equity {equity} <= 0, cannot size a new position"
                )
            existing_qty = positions.get(order.symbol, 0)
            projected_value = (existing_qty + order.qty) * price
            position_pct = projected_value / equity
            if position_pct > limits.max_position_pct:
                raise RiskViolation(
                    f"position pct: {position_pct:.6f} > limit {limits.max_position_pct} "
                    f"(symbol={order.symbol}, projected_value={projected_value}, equity={equity})"
                )

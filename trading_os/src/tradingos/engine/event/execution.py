"""Fill simulation for the event-driven engine.

Two collaborators live here:

* :class:`ChargeCalculator` — the single seam between the engine and
  :class:`~tradingos.costs.model.CostModel`. It also owns the *first sell of a
  scrip per day* bookkeeping the DP charge depends on: the DP charge applies
  once per scrip per settlement day, so a symbol sold twice in one day is
  charged DP only on the first sell. State rolls over automatically when the
  execution timestamp crosses into a new calendar day.

* :class:`FillSimulator` — turns a working order book into fills against one
  bar. Model (conservative; long-only CNC):

    - **MARKET** fills at the reference price (``open`` for next-open timing,
      ``close`` for same-close) moved *against* the trader by slippage: a BUY
      pays ``price * (1 + slip)``, a SELL receives ``price * (1 - slip)``.
    - **LIMIT** fills only when the bar trades through the limit: a BUY fills if
      ``low <= limit`` at ``min(reference, limit)``; a SELL fills if
      ``high >= limit`` at ``max(reference, limit)``. No extra slippage — the
      limit already bounds the price.
    - **Volume participation**: at most ``floor(max_participation * volume)``
      shares of a symbol may trade in one bar (summed across orders on that
      symbol). Any unfilled remainder STAYS WORKING and is retried on later bars
      until filled or cancelled by the next rebalance (cancel-and-replace).

Sell orders are processed before buys within a bar so proceeds from a rebalance
are available to fund the same bar's purchases (no intraday settlement model).
"""

from __future__ import annotations

import math
from datetime import date, datetime

import pandas as pd

from tradingos.core.errors import ConfigError
from tradingos.core.logging import get_logger
from tradingos.core.models import Fill, Order, OrderStatus, OrderType, Product, Side
from tradingos.costs.model import CostModel

logger = get_logger(__name__)


def _round_price(x: float) -> float:
    """Round an execution price to the paisa (tick-size rounding not modelled)."""
    return round(x, 2)


class ChargeCalculator:
    """Computes per-fill charges and tracks per-day DP applicability."""

    def __init__(self, cost_model: CostModel, product: Product) -> None:
        self._cost = cost_model
        self._product = product
        self._sold_today: set[str] = set()
        self._day: date | None = None

    def _roll_day(self, ts: datetime) -> None:
        d = pd.Timestamp(ts).date()
        if d != self._day:
            self._day = d
            self._sold_today.clear()

    def charges(self, side: Side, symbol: str, value: float, ts: datetime) -> float:
        """All-in charges (rupees) for one executed order of ``value`` turnover.

        ``ts`` is the execution timestamp of the fill; its DATE is forwarded to
        :meth:`CostModel.order_charges` as ``trade_date`` so the order is priced
        at the charge schedule in force on that bar date, not at the pinned
        (latest) schedule.
        """
        self._roll_day(ts)
        first_sell = True
        if side == Side.SELL:
            first_sell = symbol not in self._sold_today
        breakdown = self._cost.order_charges(
            side,
            self._product,
            value,
            first_sell_of_scrip_today=first_sell,
            trade_date=self._day,
        )
        if side == Side.SELL:
            self._sold_today.add(symbol)
        return breakdown.total


class FillSimulator:
    """Executes a working order book against a single bar."""

    def __init__(
        self,
        charges: ChargeCalculator,
        slippage_bps: float,
        max_participation: float,
        product: Product,
    ) -> None:
        self._charges = charges
        self._slip = slippage_bps / 10_000.0
        self._max_participation = max_participation
        self._product = product

    def _exec_price(self, order: Order, bar: pd.Series, basis: str) -> float | None:
        """Reference execution price for ``order`` against ``bar``.

        ``basis`` selects the reference price used for market orders and as the
        fallback for crossed limits: "open" (next-open timing) or "close"
        (same-close timing). Returns ``None`` when a limit is not crossed.
        """
        ref = float(bar["open"] if basis == "open" else bar["close"])
        high = float(bar["high"])
        low = float(bar["low"])

        if order.order_type == OrderType.MARKET:
            if order.side == Side.BUY:
                return _round_price(ref * (1.0 + self._slip))
            return _round_price(ref * (1.0 - self._slip))

        if order.order_type == OrderType.LIMIT:
            limit = order.limit_price
            if limit is None:
                raise ConfigError(f"LIMIT order {order.client_order_id} has no limit_price")
            if order.side == Side.BUY:
                if low <= limit:
                    return _round_price(min(ref, limit))
                return None
            if high >= limit:
                return _round_price(max(ref, limit))
            return None

        raise ConfigError(f"unsupported order type in backtest: {order.order_type}")

    def execute(
        self, orders: list[Order], bars: dict[str, pd.Series], fill_ts: datetime, basis: str = "open"
    ) -> list[Fill]:
        """Execute every working order that has a bar this period.

        Mutates order state (``filled_qty`` and OPEN/PARTIAL/COMPLETE
        transitions) and returns the fills produced. Orders whose symbol has no
        bar, whose limit is not crossed, or that are blocked by the participation
        cap, are left untouched (they stay working).
        """
        fills: list[Fill] = []
        # Shared per-symbol participation budget for this bar (sells first, then
        # deterministic by symbol so runs are reproducible).
        budget: dict[str, int] = {}
        ordered = sorted(orders, key=lambda o: (o.side != Side.SELL, o.symbol))

        for order in ordered:
            if order.status not in (OrderStatus.OPEN, OrderStatus.PARTIAL):
                continue
            bar = bars.get(order.symbol)
            if bar is None:
                continue
            price = self._exec_price(order, bar, basis)
            if price is None:
                continue

            volume = int(bar["volume"])
            cap = int(math.floor(self._max_participation * volume))
            used = budget.get(order.symbol, 0)
            available = max(0, cap - used)
            fill_qty = min(order.remaining_qty, available)
            if fill_qty <= 0:
                continue

            value = fill_qty * price
            charges = self._charges.charges(order.side, order.symbol, value, fill_ts)
            fills.append(
                Fill(
                    client_order_id=order.client_order_id,
                    symbol=order.symbol,
                    side=order.side,
                    qty=fill_qty,
                    price=price,
                    ts=fill_ts,
                    charges=charges,
                    product=self._product,
                )
            )
            budget[order.symbol] = used + fill_qty
            order.filled_qty += fill_qty
            if order.remaining_qty == 0:
                order.transition(OrderStatus.COMPLETE)
            elif order.status == OrderStatus.OPEN:
                order.transition(OrderStatus.PARTIAL)
        return fills


__all__ = ["ChargeCalculator", "FillSimulator"]

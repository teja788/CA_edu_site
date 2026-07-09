"""Portfolio ledger for the event-driven engine.

The Ledger is the single source of truth for cash, open positions and realised
P&L during a simulation. Contracts it upholds:

* **Cash is money.** Every mutation rounds cash to the paisa (2 dp) so the
  running balance never accumulates binary-float dust. A BUY debits
  ``qty * price + charges``; a SELL credits ``qty * price - charges``.
* **Costs are tracked, never folded into price.** ``avg_price`` is the pure
  entry VWAP; transaction charges accumulate separately in ``total_costs`` and
  are apportioned pro-rata onto emitted :class:`~tradingos.core.models.Trade`
  round trips. This keeps the gross/net-equity identity exact:
  ``gross_equity == net_equity + cumulative_costs`` (see engine.py).
* **Average-cost accounting.** Adding to a position re-derives the VWAP; a
  (partial or full) sell realises P&L against that VWAP and emits a Trade for
  the sold quantity with a pro-rata share of the lot's entry costs.

Equity is ``cash + Σ qty * mark`` — marks are the last price seen for each held
symbol (updated by the engine at every bar close), so a held symbol with no bar
on a given day simply keeps its previous mark.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from tradingos.core.logging import get_logger
from tradingos.core.models import Fill, Position, Side, Trade

logger = get_logger(__name__)


def _paisa(x: float) -> float:
    """Round a rupee amount to the paisa (2 dp)."""
    return round(x, 2)


@dataclass
class _Lot:
    """Open-lot bookkeeping needed to emit Trade round trips.

    ``entry_ts`` is the timestamp the position was first opened from flat;
    ``entry_cost_total`` is the running (buy-side) charge attributable to the
    still-open quantity — reduced pro-rata as the position is sold down.
    """

    entry_ts: datetime
    entry_cost_total: float = 0.0


class Ledger:
    """Cash + positions + realised P&L for one backtest run."""

    def __init__(self, capital: float, strategy_id: str | None = None) -> None:
        self._initial_capital = _paisa(capital)
        self.cash: float = _paisa(capital)
        self.positions: dict[str, Position] = {}
        self.total_costs: float = 0.0
        self._lots: dict[str, _Lot] = {}
        self._strategy_id = strategy_id

    # -- introspection ------------------------------------------------------

    def holdings(self) -> dict[str, int]:
        """Symbol -> signed quantity for every non-flat position."""
        return {s: p.qty for s, p in self.positions.items() if p.qty != 0}

    def entry_ts_map(self) -> dict[str, datetime]:
        """Symbol -> lot entry timestamp for every held symbol."""
        return {s: lot.entry_ts for s, lot in self._lots.items()}

    def mark(self, symbol: str, price: float) -> None:
        """Update the last-seen price used to mark a held symbol to market."""
        pos = self.positions.get(symbol)
        if pos is not None:
            pos.last_price = price

    def equity(self, marks: dict[str, float] | None = None) -> float:
        """Net equity = cash + Σ qty * mark.

        ``marks`` overrides the per-position last price where provided; symbols
        absent from ``marks`` fall back to their stored last price (then, only if
        never marked, the entry VWAP).
        """
        total = self.cash
        for sym, pos in self.positions.items():
            mark = None if marks is None else marks.get(sym)
            if mark is None:
                mark = pos.last_price if pos.last_price is not None else pos.avg_price
            total += pos.qty * mark
        return _paisa(total)

    # -- mutation -----------------------------------------------------------

    def apply_fill(self, fill: Fill, reason: str = "") -> Trade | None:
        """Apply one execution to the ledger.

        Returns a :class:`Trade` when the fill (partially or fully) closes a
        long position, else ``None``. ``reason`` becomes the trade's
        ``exit_reason`` (e.g. "rebalance", "trailing_stop", "delisted").
        """
        if fill.side == Side.BUY:
            return self._apply_buy(fill)
        return self._apply_sell(fill, reason)

    def _apply_buy(self, fill: Fill) -> None:
        pos = self.positions.get(fill.symbol)
        if pos is None:
            pos = Position(symbol=fill.symbol, product=fill.product)
            self.positions[fill.symbol] = pos

        self.cash = _paisa(self.cash - (fill.qty * fill.price + fill.charges))
        self.total_costs = _paisa(self.total_costs + fill.charges)

        new_qty = pos.qty + fill.qty
        # Average-cost VWAP over the still-open long quantity.
        pos.avg_price = (pos.qty * pos.avg_price + fill.qty * fill.price) / new_qty
        pos.qty = new_qty
        if pos.last_price is None:
            pos.last_price = fill.price

        lot = self._lots.get(fill.symbol)
        if lot is None:
            self._lots[fill.symbol] = _Lot(entry_ts=fill.ts, entry_cost_total=fill.charges)
        else:
            lot.entry_cost_total += fill.charges
        return None

    def _apply_sell(self, fill: Fill, reason: str) -> Trade | None:
        pos = self.positions.get(fill.symbol)
        if pos is None or pos.qty <= 0:
            # No long to reduce — CNC has no shorting, so this is a defensive
            # guard; log loudly and drop the fill rather than fabricate a short.
            logger.warning("sell fill for %s with no open long — ignored", fill.symbol)
            return None

        qty = min(fill.qty, pos.qty)
        if qty < fill.qty:
            logger.warning(
                "sell fill for %s exceeds held qty (%d > %d) — clipped",
                fill.symbol,
                fill.qty,
                pos.qty,
            )

        self.cash = _paisa(self.cash + (qty * fill.price - fill.charges))
        self.total_costs = _paisa(self.total_costs + fill.charges)
        pos.realized_pnl += (fill.price - pos.avg_price) * qty

        lot = self._lots[fill.symbol]
        entry_cost_alloc = _paisa(lot.entry_cost_total * (qty / pos.qty))
        lot.entry_cost_total = _paisa(lot.entry_cost_total - entry_cost_alloc)

        trade = Trade(
            symbol=fill.symbol,
            qty=qty,
            entry_ts=lot.entry_ts,
            exit_ts=fill.ts,
            entry_price=pos.avg_price,
            exit_price=fill.price,
            entry_costs=entry_cost_alloc,
            exit_costs=fill.charges,
            exit_reason=reason,
            strategy_id=self._strategy_id,
        )

        pos.qty -= qty
        if pos.qty == 0:
            del self.positions[fill.symbol]
            del self._lots[fill.symbol]
        return trade


__all__ = ["Ledger"]

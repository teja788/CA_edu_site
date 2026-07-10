"""Paper-trading broker: a Zerodha-style simulated broker driven by live or
synthetic ticks.

:class:`PaperBroker` implements the abstract :class:`~tradingos.broker.base.Broker`
interface so a strategy graduates backtest -> paper -> live with a config change
only. All money math is delegated to
:class:`~tradingos.engine.event.portfolio.Ledger` (the single source of cash /
position / avg-cost accounting) and all transaction charges to
:class:`~tradingos.engine.event.execution.ChargeCalculator` (the only seam onto
:class:`~tradingos.costs.model.CostModel`). The broker itself never adjusts cash
or average price.

Modelling assumptions (accuracy-relevant; see also docs/assumptions.md):

* **Whole-order fills only.** Paper does not model partial fills / volume
  participation -- an order either fills in full against a matching quote or
  stays working. (The backtest engine models participation; paper does not,
  because a single last-traded tick carries no reliable resting-depth signal.)
* **No T+1 settlement.** A CNC buy can be sold the same day. Zerodha would block
  this (delivery shares settle T+1); paper allows it. Position/holding buckets
  follow the product only (see ``get_positions``/``get_holdings``).
* **Slippage on MARKET only.** A market BUY pays ``(ask or last) * (1 + slip)``,
  a market SELL receives ``(bid or last) * (1 - slip)``. LIMIT orders fill at the
  limit price exactly with no extra slippage (the limit already bounds price).
* **Immediate matching requires a SAME-DAY quote.** An order placed while the
  last known quote is stale (from a previous session -- e.g. a planned order
  placed at 09:15 before the day's first tick) is accepted OPEN and matches on
  the day's first tick for its symbol instead. Filling a market order against
  yesterday's close would be systematically wrong across overnight gaps; the
  first tick of the day IS the paper analogue of "at the open", mirroring the
  backtest's signals-at-close-of-T -> fill-at-T+1-open convention. A stale
  quote is still used as the *estimate* for pre-trade risk/cash checks (the
  best reference available pre-open).
* **Fill-time cash guard.** Because a gap can carry a fill above its pre-trade
  estimate, a BUY whose actual cost exceeds available cash at match time is
  REJECTED then (like a real margin shortfall) -- the ledger can never go
  negative.
* **Long-only CNC.** Selling more than held is rejected pre-trade (no shorting),
  mirroring the Ledger's own guard. Working orders reserve what they commit:
  the cash check is against cash minus working-BUY commitments (limit value
  for a LIMIT, latest-quote estimate for a resting MARKET, plus estimated
  charges), the oversell guard against holdings minus resting SELL quantity --
  mirroring Zerodha, which blocks funds/stock at placement.
* **SL / SL-M unsupported.** Stop orders are rejected at placement (status
  message "not supported in paper"), without raising -- paper has no intrabar
  path to trigger a stop from a single last-traded tick.
* **Idempotency.** ``place_order`` for a ``client_order_id`` already stored in a
  *non-PENDING* state returns the stored order unchanged. A stored PENDING order
  is a previously *queued* order (see ``queue_for_open``) and is placed normally.

Thread safety: every public entry point takes one reentrant lock -- in
``--schedule`` mode the websocket thread (``on_tick``) and the APScheduler job
threads (``place_planned``, ``mark_to_market``, ``snapshot``) share this
broker, and the check-then-mutate sequences (cash check -> fill, oversell
check -> place) must never interleave.

Restart safety: on construction the broker replays ``store.all_fills()`` through
a fresh ``Ledger(capital, strategy_id)`` (charges are read from each stored Fill
and are NOT recomputed), warms the ChargeCalculator's per-day DP bookkeeping,
restores the working order book (OPEN / PARTIAL orders) and remembers which days
already carry a day-start equity snapshot. This broker only ever persists an
order once it is accepted (OPEN), completed, cancelled or rejected, and queued
orders always carry a ``planned_for`` date, so a PENDING row with
``planned_for=None`` cannot arise from its own writes -- the working set restored
on restart is therefore exactly the OPEN and PARTIAL orders.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Mapping
from datetime import date, datetime
from typing import Literal

from tradingos.broker.base import Broker, TickCallback
from tradingos.broker.killswitch import KillSwitch
from tradingos.broker.risk import PreTradeRiskChecker, RiskLimits
from tradingos.config.settings import Settings
from tradingos.core.alerts import TelegramAlerter
from tradingos.core.errors import BrokerError, KillSwitchActive, OrderStateError, RiskViolation
from tradingos.core.logging import get_logger
from tradingos.core.models import (
    Fill,
    Margins,
    Order,
    OrderStatus,
    OrderType,
    Position,
    Product,
    Quote,
    Side,
    Tick,
)
from tradingos.core.timeutils import MARKET_OPEN, now_ist, session_bounds
from tradingos.costs.model import CostModel
from tradingos.data.calendar import NSECalendar
from tradingos.engine.event.execution import ChargeCalculator
from tradingos.engine.event.portfolio import Ledger
from tradingos.paper.ledgerdb import PaperStore

logger = get_logger(__name__)


class PaperBroker(Broker):
    """Simulated broker on live/synthetic ticks. Restart-safe: on construction,
    replays ``store.all_fills()`` through a fresh ``Ledger(capital, strategy_id)``
    and reloads the working order book (OPEN / PARTIAL) from the store."""

    def __init__(
        self,
        settings: Settings,
        *,
        strategy_id: str,
        capital: float,
        cost_schedule: str = "zerodha_2026",
        product: Product = Product.CNC,
        slippage_bps: float | None = None,
        limit_fill_mode: Literal["touch", "cross"] = "touch",
        risk_limits: RiskLimits | None = None,
        kill_switch: KillSwitch | None = None,
        calendar: NSECalendar | None = None,
        alerter: TelegramAlerter | None = None,
        store: PaperStore | None = None,
        enforce_market_hours: bool = True,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        self._settings = settings
        self._strategy_id = strategy_id
        self._capital = capital
        self._product = product
        self._limit_fill_mode = limit_fill_mode
        self._enforce_market_hours = enforce_market_hours
        # Injectable clock (tests pin it); everything time-stamped by this
        # broker reads the SAME clock, including the quote-freshness rule.
        self._now = now_fn or now_ist

        self._store = store or PaperStore(settings.paper_db_path, strategy_id)
        self._cost_model = CostModel(cost_schedule)
        # Slippage: explicit bps override, else the schedule's non-large-cap default.
        if slippage_bps is None:
            slippage_bps = self._cost_model.slippage_bps(is_large_cap=False)
        self._slippage_bps = slippage_bps
        self._slip = slippage_bps / 10_000.0
        self._charges = ChargeCalculator(self._cost_model, product)
        self._calendar = calendar or NSECalendar(settings)
        self._kill_switch = kill_switch or KillSwitch.from_settings(settings)
        self._alerter = alerter or TelegramAlerter.from_settings(settings)
        # enforce_market_hours only governs the DEFAULT risk limits; an explicit
        # RiskLimits is respected verbatim (its own market_hours_only wins).
        self._risk = PreTradeRiskChecker(
            risk_limits
            or RiskLimits.from_settings(settings, market_hours_only=enforce_market_hours),
            self._calendar,
        )

        self._quotes: dict[str, Quote] = {}
        self._open_orders: dict[str, Order] = {}
        self._ledger = Ledger(capital, strategy_id)
        self._day_start_done: set[date] = set()
        # In --schedule mode the websocket thread (on_tick) and the APScheduler
        # job threads (place_planned / mark_to_market / snapshot) hit this
        # broker concurrently; one reentrant lock serializes every public entry
        # point so check-then-mutate sequences (cash check -> fill, oversell
        # check -> place) can never interleave across threads. Reentrant
        # because place_planned calls place_order under the same lock.
        self._lock = threading.RLock()

        self._replay()

    # -- restart replay ----------------------------------------------------

    def _replay(self) -> None:
        fills = self._store.all_fills()  # ordered by ts, id
        for fill in fills:
            # Charges live on the stored Fill; apply_fill must NOT recompute them.
            self._ledger.apply_fill(fill)
        self._warm_charges(fills)
        self._reload_open_orders()
        self._seed_day_start_done()

    def _warm_charges(self, fills: list[Fill]) -> None:
        """Prime the ChargeCalculator's first-sell-of-day DP bookkeeping after a
        replay, WITHOUT recomputing any charge.

        This is the single, deliberate place we touch ChargeCalculator internals.
        The DP charge applies once per scrip per settlement day; the calculator
        tracks which scrips have already been sold *today*. On restart the ledger
        is rebuilt from stored fills, so we must restore that "already sold today"
        set for the most recent fill day -- otherwise a later same-day SELL of a
        scrip already sold before the restart would wrongly re-apply DP. Fills on
        an earlier day are irrelevant: the calculator rolls (and clears) its set
        as soon as a fill on a newer day arrives.
        """
        if not fills:
            return
        last_day = fills[-1].ts.date()
        sold_today = {
            f.symbol for f in fills if f.side == Side.SELL and f.ts.date() == last_day
        }
        self._charges._day = last_day  # noqa: SLF001 -- documented warm-up (see docstring)
        self._charges._sold_today = sold_today  # noqa: SLF001

    def _reload_open_orders(self) -> None:
        for status in (OrderStatus.OPEN, OrderStatus.PARTIAL):
            for order in self._store.orders(status=status):
                self._open_orders[order.client_order_id] = order

    def _seed_day_start_done(self) -> None:
        # A day-start snapshot is written at the session open (09:15). Recognise
        # existing ones so a mid-day restart never overwrites the day's baseline.
        curve = self._store.equity_curve()
        for ts in curve.index:
            if ts.time() == MARKET_OPEN:
                self._day_start_done.add(ts.date())

    # -- pricing / matching -------------------------------------------------

    def _match_price(self, order: Order, quote: Quote) -> float | None:
        """Execution price for ``order`` against ``quote`` (paisa-rounded), or
        None if a LIMIT order is not marketable at the current quote."""
        last = quote.last_price
        if order.order_type == OrderType.MARKET:
            if order.side == Side.BUY:
                ref = quote.ask if quote.ask is not None else last
                return round(ref * (1.0 + self._slip), 2)
            ref = quote.bid if quote.bid is not None else last
            return round(ref * (1.0 - self._slip), 2)

        # LIMIT -- fills at the limit exactly, no slippage.
        limit = order.limit_price
        if limit is None:  # defensive; Order validation should prevent this
            return None
        if order.side == Side.BUY:
            trigger = last if last is not None else quote.ask
            if trigger is None:
                return None
            crossed = trigger <= limit if self._limit_fill_mode == "touch" else trigger < limit
            return round(limit, 2) if crossed else None

        trigger = last if last is not None else quote.bid
        if trigger is None:
            return None
        crossed = trigger >= limit if self._limit_fill_mode == "touch" else trigger > limit
        return round(limit, 2) if crossed else None

    def _reserved_cash(self, exclude: str | None = None) -> float:
        """Cash committed to working BUY orders. A resting LIMIT reserves its
        limit value (it can only fill at <= limit, so the reservation always
        covers the fill); a resting MARKET (waiting for a fresh quote) reserves
        its estimate at the latest known quote -- an estimate that can be
        outrun by a gap, which is why ``_fill_order`` re-checks cash at match
        time. Estimated charges are included in both cases. ``exclude`` drops
        one order's own reservation (used when re-validating a modification of
        that order)."""
        total = 0.0
        for o in self._open_orders.values():
            if o.side != Side.BUY or o.client_order_id == exclude:
                continue
            if o.limit_price is not None:
                ref = o.limit_price
            else:
                quote = self._quotes.get(o.symbol)
                if quote is None:  # cannot arise: placement requires a reference
                    continue
                ask = quote.ask if quote.ask is not None else quote.last_price
                ref = ask * (1.0 + self._slip)
            value = (o.qty - o.filled_qty) * ref
            total += value + self._cost_model.order_charges(
                Side.BUY, self._product, value
            ).total
        return total

    def _reserved_qty(self, symbol: str, exclude: str | None = None) -> int:
        """Shares of ``symbol`` committed to working SELL orders (unfilled qty).
        ``exclude`` drops one order's own reservation (modification re-check)."""
        return sum(
            o.qty - o.filled_qty
            for o in self._open_orders.values()
            if o.side == Side.SELL and o.symbol == symbol and o.client_order_id != exclude
        )

    def _estimated_buy_price(self, order: Order, quote: Quote | None) -> float:
        """The price a BUY fill would use -- identical to ``_match_price`` for a
        BUY, used by the pre-trade cash check so the estimate matches the fill."""
        if order.order_type == OrderType.LIMIT and order.limit_price is not None:
            return round(order.limit_price, 2)
        # MARKET -- a quote is guaranteed here (no-quote market orders never reach
        # the cash check: they fail the price-reference guard first).
        assert quote is not None
        ref = quote.ask if quote.ask is not None else quote.last_price
        return round(ref * (1.0 + self._slip), 2)

    def _fill_order(self, order: Order, quote: Quote, ts: datetime) -> Fill | None:
        """Attempt a whole-order fill of ``order`` against ``quote`` at ``ts``.

        Returns the Fill on success (ledger updated, order COMPLETE, fill+order
        persisted, alert fired) or None if a LIMIT order is not yet marketable.
        """
        price = self._match_price(order, quote)
        if price is None:
            return None
        qty = order.qty
        value = qty * price  # price is paisa-rounded before valuation
        # Fill-time cash guard: a gap between placement (estimate) and match
        # can carry a BUY's cost above the pre-trade check. Reject like a real
        # margin shortfall rather than let the ledger go negative.
        if order.side == Side.BUY:
            est = round(value + self._cost_model.order_charges(Side.BUY, self._product, value).total, 2)
            if est - self._ledger.cash > 0.005:
                msg = (
                    f"insufficient cash at fill: need {est:.2f} for {qty} {order.symbol}, "
                    f"have {self._ledger.cash:.2f} (price moved past the pre-trade estimate)"
                )
                # NOT _reject: created_at must stay the placement time.
                order.transition(OrderStatus.REJECTED, msg)
                order.updated_at = ts
                self._store.save_order(order)
                self._open_orders.pop(order.client_order_id, None)
                self._alerter.alert_rejection(order, msg)
                return None
        charges = self._charges.charges(order.side, order.symbol, value, ts)
        fill = Fill(
            client_order_id=order.client_order_id,
            symbol=order.symbol,
            side=order.side,
            qty=qty,
            price=price,
            ts=ts,
            charges=charges,
            product=self._product,
        )
        self._ledger.apply_fill(fill)  # the ONLY cash/position mutation
        order.filled_qty = qty
        order.transition(OrderStatus.COMPLETE)
        order.updated_at = self._now()
        # One transaction: a persisted fill with a stale OPEN order row would
        # double-apply on restart (replay + re-fill of the reloaded order).
        self._store.record_fill_and_order(fill, order)
        self._open_orders.pop(order.client_order_id, None)
        self._alerter.alert_fill(fill)
        return fill

    def _reject(self, order: Order, message: str, now: datetime) -> None:
        """Persist ``order`` REJECTED with ``message`` and fire the alert. Stamps
        created_at at rejection time so the order counts (conservatively) toward
        the day's order tally. Caller decides whether to raise."""
        order.created_at = now
        order.updated_at = now
        order.transition(OrderStatus.REJECTED, message)
        self._store.save_order(order)
        self._alerter.alert_rejection(order, message)

    # -- day-start equity snapshot -----------------------------------------

    def _maybe_snapshot_day_start(self, day: date) -> None:
        """Lazily persist the day's opening equity (at 09:15) exactly once, before
        any of that day's fills mutate the ledger -- the max_daily_loss basis."""
        if day in self._day_start_done:
            return
        ts = session_bounds(day)[0]  # 09:15 of that day
        self._store.snapshot_equity(ts, self._ledger.equity(), self._ledger.cash)
        self._day_start_done.add(day)

    # -- Broker interface ---------------------------------------------------

    def place_order(self, order: Order) -> Order:
        with self._lock:
            return self._place_order_locked(order)

    def _place_order_locked(self, order: Order) -> Order:
        # (1) idempotency -- a stored, non-PENDING order is a true re-place.
        stored = self._store.get_order(order.client_order_id)
        if stored is not None and stored.status != OrderStatus.PENDING:
            return stored

        now = self._now()
        today = now.date()
        # Establish the day's baseline equity before anything mutates the ledger;
        # the daily-loss risk rule reads it back below.
        self._maybe_snapshot_day_start(today)

        # (2) kill switch
        try:
            self._kill_switch.check()
        except KillSwitchActive as exc:
            self._reject(order, str(exc), now)
            raise

        # SL / SL-M are not supported in paper -> REJECTED, no exception.
        if order.order_type in (OrderType.SL, OrderType.SL_M):
            self._reject(order, "not supported in paper", now)
            return order

        # Price reference for the risk check: limit price, else last quote.
        quote = self._quotes.get(order.symbol)
        if order.limit_price is not None:
            ref_price: float | None = order.limit_price
        elif quote is not None:
            ref_price = quote.last_price
        else:
            ref_price = None
        if ref_price is None:
            raise BrokerError(
                f"no price reference for {order.symbol}: MARKET order placed before any "
                f"quote is known"
            )

        # (3) pre-trade risk
        orders_today = self._store.orders_placed_count(today)
        day_start_equity = self._store.day_start_equity(today)
        if day_start_equity is None:
            day_start_equity = self._capital
        try:
            self._risk.check(
                order,
                price=ref_price,
                equity=self._ledger.equity(),
                positions=self._ledger.holdings(),
                orders_today=orders_today,
                day_start_equity=day_start_equity,
                now=now,
            )
        except RiskViolation as exc:
            self._reject(order, str(exc), now)
            raise

        # (4) BUY cash check / SELL oversell guard, both net of what working
        # (resting) orders have already committed -- several resting LIMIT BUYs
        # can never jointly overspend cash, nor resting SELLs jointly oversell.
        if order.side == Side.BUY:
            fill_price = self._estimated_buy_price(order, quote)
            value = order.qty * fill_price
            est_charges = self._cost_model.order_charges(Side.BUY, self._product, value).total
            est_cost = round(value + est_charges, 2)
            available = round(self._ledger.cash - self._reserved_cash(), 2)
            if est_cost > available:
                msg = (
                    f"insufficient cash: need {est_cost:.2f} for {order.qty} {order.symbol}, "
                    f"available {available:.2f} (cash {self._ledger.cash:.2f} minus "
                    f"working-order reservations)"
                )
                self._reject(order, msg, now)
                raise RiskViolation(msg)
        else:
            held = self._ledger.holdings().get(order.symbol, 0)
            available_qty = held - self._reserved_qty(order.symbol)
            if order.qty > available_qty:
                msg = (
                    f"oversell: {order.qty} {order.symbol} > available {available_qty} "
                    f"(held {held} minus working SELL orders; long-only CNC)"
                )
                self._reject(order, msg, now)
                raise RiskViolation(msg)

        # (5) accept: stamp submission time, transition, persist, try to match.
        order.created_at = now
        order.updated_at = now
        order.transition(OrderStatus.OPEN)
        self._store.save_order(order)
        self._open_orders[order.client_order_id] = order

        # Immediate match only against a SAME-DAY quote: a stale (overnight)
        # quote must not price a fill -- the order rests and matches on the
        # day's first tick instead (see module docstring).
        if quote is not None and quote.ts.date() == now.date():
            self._fill_order(order, quote, now)
        return order

    def _validate_modification(self, order: Order, new_qty: int, new_limit: float) -> None:
        """Re-run the pre-trade gates on a modified order -- risk rules, then
        the BUY cash check / SELL oversell guard with the order's OWN current
        reservation excluded from the working-order commitments (it is being
        replaced, not added). Zerodha re-validates modifications server-side;
        without this, a small accepted order could be inflated past every
        limit. Raises RiskViolation; the caller leaves the order untouched.
        The orders-per-day rule is deliberately passed 0: a modification is
        not a new placement and must not burn (or trip) the day's tally."""
        now = self._now()
        today = now.date()
        candidate = order.model_copy()
        candidate.qty = new_qty
        candidate.limit_price = new_limit
        day_start_equity = self._store.day_start_equity(today)
        if day_start_equity is None:
            day_start_equity = self._capital
        self._risk.check(
            candidate,
            price=new_limit,
            equity=self._ledger.equity(),
            positions=self._ledger.holdings(),
            orders_today=0,
            day_start_equity=day_start_equity,
            now=now,
        )
        if order.side == Side.BUY:
            value = new_qty * round(new_limit, 2)
            est_charges = self._cost_model.order_charges(Side.BUY, self._product, value).total
            est_cost = round(value + est_charges, 2)
            available = round(
                self._ledger.cash - self._reserved_cash(exclude=order.client_order_id), 2
            )
            if est_cost > available:
                raise RiskViolation(
                    f"insufficient cash for modification: need {est_cost:.2f} for "
                    f"{new_qty} {order.symbol}, available {available:.2f} (cash "
                    f"{self._ledger.cash:.2f} minus other working-order reservations)"
                )
        else:
            held = self._ledger.holdings().get(order.symbol, 0)
            available_qty = held - self._reserved_qty(order.symbol, exclude=order.client_order_id)
            if new_qty > available_qty:
                raise RiskViolation(
                    f"oversell on modification: {new_qty} {order.symbol} > available "
                    f"{available_qty} (held {held} minus other working SELL orders)"
                )

    def modify_order(
        self,
        client_order_id: str,
        qty: int | None = None,
        limit_price: float | None = None,
        trigger_price: float | None = None,
    ) -> Order:
        with self._lock:
            order = self._open_orders.get(client_order_id) or self._store.get_order(
                client_order_id
            )
            if order is None:
                raise BrokerError(f"unknown order {client_order_id!r}")
            if order.status.is_terminal:
                raise OrderStateError(f"cannot modify a {order.status.value} order")
            if order.order_type != OrderType.LIMIT:
                raise BrokerError("only LIMIT orders can be modified in paper")
            new_qty = qty if qty is not None else order.qty
            new_limit = limit_price if limit_price is not None else order.limit_price
            if new_limit is None:  # defensive; LIMIT orders always carry one
                raise BrokerError("LIMIT order has no limit price to modify against")
            # Violation -> raises here, before any mutation: the order keeps
            # working exactly as previously accepted (Zerodha semantics).
            self._validate_modification(order, new_qty, new_limit)
            order.qty = new_qty
            if limit_price is not None:
                order.limit_price = limit_price
            if trigger_price is not None:
                order.trigger_price = trigger_price
            order.updated_at = self._now()
            self._store.save_order(order)
            # Keep the working-set object in sync so the next tick re-checks the match.
            if client_order_id in self._open_orders:
                self._open_orders[client_order_id] = order
            return order

    def cancel_order(self, client_order_id: str) -> Order:
        with self._lock:
            order = self._open_orders.get(client_order_id) or self._store.get_order(
                client_order_id
            )
            if order is None:
                raise BrokerError(f"unknown order {client_order_id!r}")
            if order.status.is_terminal:
                raise OrderStateError(f"cannot cancel a {order.status.value} order")
            order.transition(OrderStatus.CANCELLED)
            order.updated_at = self._now()
            self._store.save_order(order)
            self._open_orders.pop(client_order_id, None)
            return order

    def get_order(self, client_order_id: str) -> Order:
        order = self._store.get_order(client_order_id)
        if order is None:
            raise BrokerError(f"unknown order {client_order_id!r}")
        return order

    def get_orders(self) -> list[Order]:
        return self._store.orders()

    def _ledger_positions(self) -> list[Position]:
        with self._lock:
            return [p for p in self._ledger.positions.values() if p.qty != 0]

    def get_positions(self) -> list[Position]:
        # Zerodha semantics: CNC delivery lands in holdings, not the intraday
        # positions book. MIS is the reverse.
        return [] if self._product == Product.CNC else self._ledger_positions()

    def get_holdings(self) -> list[Position]:
        return self._ledger_positions() if self._product == Product.CNC else []

    def get_margins(self) -> Margins:
        with self._lock:
            return Margins(cash_available=self._ledger.cash, used=0.0)

    def get_quote(self, symbols: list[str]) -> dict[str, Quote]:
        with self._lock:
            return {s: self._quotes[s] for s in symbols if s in self._quotes}

    def stream_ticks(self, symbols: list[str], callback: TickCallback) -> None:
        raise NotImplementedError(
            "PaperBroker does not stream ticks; wire a TickStreamer to on_tick instead"
        )

    # -- tick / quote entry point ------------------------------------------

    def on_tick(self, tick: Tick) -> list[Fill]:
        """The quote/match entry point. Updates the last-known quote, marks the
        ledger, lazily snapshots the day's opening equity (before this tick's
        fills), then fills any working orders for the tick's symbol."""
        with self._lock:
            quote = Quote(
                symbol=tick.symbol,
                last_price=tick.last_price,
                bid=tick.bid,
                ask=tick.ask,
                volume=tick.volume,
                ts=tick.ts,
            )
            self._quotes[tick.symbol] = quote
            self._ledger.mark(tick.symbol, tick.last_price)
            self._maybe_snapshot_day_start(tick.ts.date())

            fills: list[Fill] = []
            working = [
                o
                for o in self._open_orders.values()
                if o.symbol == tick.symbol
                and o.status in (OrderStatus.OPEN, OrderStatus.PARTIAL)
            ]
            for order in working:
                fill = self._fill_order(order, quote, tick.ts)
                if fill is not None:
                    fills.append(fill)
            return fills

    # -- equity / snapshots -------------------------------------------------

    def equity(self) -> float:
        with self._lock:
            return self._ledger.equity()

    def snapshot(self, now: datetime | None = None) -> None:
        with self._lock:
            ts = now if now is not None else self._now()
            self._store.snapshot_equity(ts, self._ledger.equity(), self._ledger.cash)

    # -- planned (next-open) queue -----------------------------------------

    def queue_for_open(self, order: Order, on_day: date) -> Order:
        """Persist ``order`` as a planned (PENDING) order for ``on_day``.

        created_at is intentionally cleared: a queued order must count toward the
        day it is actually placed (``place_planned``), not the day it was queued
        -- ``PaperStore.orders_placed_count`` filters on created_at.
        """
        with self._lock:
            order.created_at = None
            order.updated_at = self._now()
            self._store.save_order(order, planned_for=on_day)
            return order

    def place_planned(self, day: date) -> list[Order]:
        """Place every order queued for ``day``. Per-order fault tolerant: one
        rejected/unplaceable order must never abort the rest of the open.

        - ``RiskViolation`` -> that order is already persisted REJECTED; skip it.
        - ``BrokerError`` (e.g. MARKET with no quote known yet) -> the order
          stays PENDING and a later ``place_planned`` call retries it.
        - ``KillSwitchActive`` -> stop entirely; the remaining orders stay
          PENDING for a retry after the switch disengages.

        Returns the orders actually run through ``place_order`` (including
        pre-trade-rejected ones, which don't raise out of here)."""
        placed: list[Order] = []
        with self._lock:
            planned = self._store.planned_orders(day)
        for order in planned:
            try:
                placed.append(self.place_order(order))
            except KillSwitchActive as exc:
                logger.warning("place_planned(%s) halted: %s", day.isoformat(), exc)
                break
            except RiskViolation as exc:
                logger.warning(
                    "planned order %s rejected pre-trade: %s", order.client_order_id, exc
                )
            except BrokerError as exc:
                logger.warning(
                    "planned order %s left PENDING for retry: %s", order.client_order_id, exc
                )
        return placed

    def mark_to_market(self, prices: Mapping[str, float]) -> None:
        """Mark position valuations (Ledger.mark) WITHOUT any order matching --
        the session-close path uses this to value equity at the day's official
        closes even when no tick was seen (e.g. a report-only run)."""
        with self._lock:
            for symbol, price in prices.items():
                self._ledger.mark(symbol, price)


__all__ = ["PaperBroker"]

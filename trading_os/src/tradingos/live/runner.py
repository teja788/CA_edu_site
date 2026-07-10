"""Live trading session runner: session-open placement of queued orders,
session-close rebalance evaluation + next-open queueing, and the cron
scheduler (open / close / reconciliation) that drives all three automatically.

Design mirrors :class:`~tradingos.paper.runner.PaperSessionRunner` closely --
same session-open / session-close split, the same
:func:`~tradingos.engine.event.strategy_runtime.evaluate_targets` pipeline
bound to a :class:`~tradingos.engine.dataview.DataView` pinned to the day's
15:30 close, the same SELLs-then-BUYs delta ordering with deterministic
``client_order_id``\\ s, and the same stale-planned-order cancellation on a
close re-run. Two things differ because :class:`~tradingos.live.broker.ZerodhaLiveBroker`
is a thinner adapter than :class:`~tradingos.paper.broker.PaperBroker`:

* **The runner owns the planned-order queue.** ``PaperBroker`` has
  ``queue_for_open`` / ``place_planned`` built in; ``ZerodhaLiveBroker`` does
  not (Zerodha itself has no notion of "queued for tomorrow's open"). Both
  brokers journal to the *same* :class:`~tradingos.paper.ledgerdb.PaperStore`
  schema, so this runner reads/writes the planned-order queue
  (``PaperStore.save_order(planned_for=...)`` / ``PaperStore.planned_orders``)
  directly, and replicates ``PaperBroker.place_planned``'s per-order fault
  tolerance itself in :meth:`~LiveSessionRunner.on_session_open`.
* **No EOD / divergence report.** Paper trading owns the backtest-vs-paper
  divergence narrative (``paper/eod.py``); live trading's job in this phase is
  correctness of the order flow (Phase 6 acceptance: a dry-run session shows
  the correct intended orders), not a second P&L report. ``on_session_close``
  therefore returns the queued orders, not a report path.

Cancelling stale planned orders on a close re-run is journal-only: a planned
order that has not yet reached :meth:`~LiveSessionRunner.on_session_open` was
NEVER sent to Kite (it has no ``broker_order_id``), so it is transitioned to
CANCELLED directly on the store row rather than through
``broker.cancel_order`` -- calling that would (in live, non-dry-run mode)
build a ``cancel_order`` kwargs referencing a ``None`` order id and actually
hit the Kite API for an order the broker never placed. See
:meth:`~LiveSessionRunner._cancel_stale_planned`.

Reconciliation (comparing the journal against ``kite.orders()`` for mismatches
beyond what ``sync_orders`` itself catches) is delegated to
``tradingos.live.reconcile.reconcile_once`` -- a module built in parallel with
this one -- via the lazy, monkeypatchable indirection
:func:`_reconcile_once`, so this module never hard-imports it and this
module's own tests never need it to exist.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from tradingos.config.schemas import StrategyConfig
from tradingos.config.settings import Settings
from tradingos.core.alerts import TelegramAlerter
from tradingos.core.errors import BrokerError, KillSwitchActive, RiskViolation
from tradingos.core.logging import get_logger
from tradingos.core.models import Order, OrderStatus, OrderType, Position, Side
from tradingos.core.timeutils import IST, now_ist, session_bounds
from tradingos.data.calendar import NSECalendar
from tradingos.data.store import BarStore
from tradingos.engine.base import StaticUniverseResolver
from tradingos.engine.dataview import DataView, MarketData, SignalStore
from tradingos.engine.event.strategy_runtime import evaluate_targets
from tradingos.live.broker import ZerodhaLiveBroker
from tradingos.paper.ledgerdb import PaperStore

logger = get_logger(__name__)

# Same rationale as paper/runner.py: after 15:30 (MARKET_CLOSE) so a data sync
# job has a window to land the day's closing bars before the rebalance
# evaluates them.
_CLOSE_JOB_HOUR = 15
_CLOSE_JOB_MINUTE = 35

_TAG_REBALANCE = "rebalance"


def _reconcile_once(broker: ZerodhaLiveBroker, alerter: TelegramAlerter) -> list[object]:
    """Lazy indirection onto ``tradingos.live.reconcile.reconcile_once``.

    Imported here (not at module scope) so this module never hard-depends on
    ``tradingos.live.reconcile`` -- a module built in parallel with this one.
    A dedicated module-level function (rather than an inline import in the job
    wrapper) so tests can monkeypatch this single seam regardless of whether
    the real module exists yet."""
    from tradingos.live.reconcile import reconcile_once

    return reconcile_once(broker, alerter=alerter)


class LiveSessionRunner:
    """Drives one strategy's live session: place the day's queued orders at
    the open, evaluate the rebalance and queue tomorrow's delta orders at the
    close, and (via :meth:`build_scheduler`) do both automatically -- plus a
    periodic reconciliation pass -- on trading days."""

    def __init__(
        self,
        settings: Settings,
        config: StrategyConfig,
        broker: ZerodhaLiveBroker,
        *,
        calendar: NSECalendar,
        store: PaperStore,
        alerter: TelegramAlerter | None = None,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        self._settings = settings
        self._config = config
        self._broker = broker
        self._calendar = calendar
        self._store = store
        # Used only by the reconciliation cron job (reconcile_once's alerter
        # kwarg); the broker owns its own alerter for order-flow alerts.
        self._alerter = alerter or TelegramAlerter.from_settings(settings)
        # Injectable clock (tests pin it) for the queue-mechanics timestamps
        # this runner writes itself (see _queue_for_open / _cancel_stale_planned).
        self._now = now_fn or now_ist

    # -- session open ---------------------------------------------------

    def on_session_open(self, day: date) -> list[Order]:
        """Place every order queued (by a prior :meth:`on_session_close`) for
        ``day``'s open, reading the queue directly off the journal store (see
        module docstring -- ``ZerodhaLiveBroker`` has no queue of its own).

        Same per-order fault tolerance as ``PaperBroker.place_planned``:

        - ``KillSwitchActive`` -> halt the whole batch; the remaining orders
          stay PENDING for a retry once the switch disengages.
        - ``RiskViolation`` -> the order is already persisted REJECTED by the
          broker; skip it and continue with the rest.
        - ``BrokerError`` (e.g. no quote yet, or a transient broker failure)
          -> the order stays PENDING for a later retry.

        Returns the orders actually run through ``place_order`` (including
        pre-trade-rejected ones, which don't raise out of here)."""
        planned = self._store.planned_orders(day)
        placed: list[Order] = []
        for order in planned:
            try:
                result = self._broker.place_order(order)
            except KillSwitchActive as exc:
                logger.warning("session open %s halted: %s", day.isoformat(), exc)
                break
            except RiskViolation as exc:
                logger.warning(
                    "planned order %s rejected pre-trade: %s", order.client_order_id, exc
                )
                continue
            except BrokerError as exc:
                logger.warning(
                    "planned order %s left PENDING for retry: %s", order.client_order_id, exc
                )
                continue
            placed.append(result)
            logger.info(
                "session open %s: placed %s %s %d %s -> %s",
                day.isoformat(),
                result.client_order_id,
                result.side.value,
                result.qty,
                result.symbol,
                result.status.value,
            )
        return placed

    # -- session close ----------------------------------------------------

    def on_session_close(self, day: date) -> list[Order]:
        """Sync the day's fills from Kite, evaluate rebalance targets off
        that day's completed bars (identical point-in-time-safe pipeline to
        paper -- see module docstring), queue the delta orders for the next
        trading day's open, and return them.

        No EOD / divergence report is produced here (see module docstring)."""
        self._broker.sync_orders()  # pick up the day's fills before pricing holdings

        positions = self._current_positions()
        current_holdings = {p.symbol: p.qty for p in positions}

        data = self._load_market_data()
        targets = self._evaluate_targets(day, data, current_holdings)

        next_day = self._calendar.next_trading_day(day)
        orders = self._diff_orders(targets, current_holdings, next_day)
        self._cancel_stale_planned(next_day, {o.client_order_id for o in orders})
        if orders:
            for order in orders:
                self._queue_for_open(order, next_day)
                logger.info(
                    "session close %s: queued %s %s %d %s for %s open",
                    day.isoformat(),
                    order.client_order_id,
                    order.side.value,
                    order.qty,
                    order.symbol,
                    next_day.isoformat(),
                )
        else:
            logger.info(
                "session close %s: holdings already match targets, nothing queued",
                day.isoformat(),
            )
        return orders

    # -- planned (next-open) queue, owned by the runner --------------------

    def _queue_for_open(self, order: Order, on_day: date) -> None:
        """Persist ``order`` as a planned (PENDING) order for ``on_day``, in
        the SAME journal store the broker journals live orders to.

        ``created_at`` is cleared: a queued order must count toward the day
        it is actually placed (:meth:`on_session_open`), not the day it was
        queued -- mirrors ``PaperBroker.queue_for_open`` /
        ``PaperStore.orders_placed_count``."""
        order.created_at = None
        order.updated_at = self._now()
        self._store.save_order(order, planned_for=on_day)

    def _cancel_stale_planned(self, next_day: date, new_ids: set[str]) -> None:
        """Cancel this runner's still-PENDING planned orders for ``next_day``
        that the freshly computed target set no longer wants.

        A close-job re-run (e.g. after a data re-sync changed the targets)
        would otherwise leave the FIRST run's queue entries live. Scoped to
        ``tag == "rebalance"`` -- orders queued by anything other than this
        runner are never touched.

        This cancels via a direct store transition, NOT ``broker.cancel_order``:
        a still-PENDING planned order was never sent to Kite (no
        ``broker_order_id`` was ever assigned), so routing it through the
        broker's cancel path would -- in live, non-dry-run mode -- build a
        ``cancel_order`` call referencing a ``None`` order id and actually hit
        the Kite API for an order the broker never placed. Transitioning the
        journal row directly is correct and touches no API."""
        for stale in self._store.planned_orders(next_day):
            if stale.tag != _TAG_REBALANCE or stale.client_order_id in new_ids:
                continue
            stale.transition(OrderStatus.CANCELLED)
            stale.updated_at = self._now()
            self._store.save_order(stale)
            logger.info(
                "session close: cancelled stale planned order %s (%s %d %s no longer "
                "in the target delta for %s) -- journal-only, never sent to the broker",
                stale.client_order_id,
                stale.side.value,
                stale.qty,
                stale.symbol,
                next_day.isoformat(),
            )

    def _current_positions(self) -> list[Position]:
        # Zerodha semantics split CNC (holdings) from MIS (positions); pulling
        # both means this works unmodified for either product.
        return [*self._broker.get_holdings(), *self._broker.get_positions()]

    def _load_market_data(self) -> MarketData:
        """Load bar data exactly as ``cli/backtest_cmds.py`` / ``paper/runner.py``
        do (same universe-symbol resolution, adjusted prices, full history for
        indicator warm-up)."""
        bar_store = BarStore(self._settings)
        load_symbols: set[str] = set(self._config.universe.symbols or [])
        if not load_symbols:
            load_symbols = set(bar_store.symbols(self._config.timeframe))
        for fspec in self._config.filters:
            routed = fspec.params.get("symbol")
            if routed:
                load_symbols.add(str(routed))

        return bar_store.load_market_data(
            sorted(load_symbols), self._config.timeframe, start=None, end=None, adjusted=True
        )

    def _evaluate_targets(
        self, day: date, data: MarketData, current_holdings: dict[str, int]
    ) -> dict[str, int]:
        """Build a DataView bound to ``day`` 15:30 over pre-loaded ``data`` and
        delegate to ``evaluate_targets`` -- the exact same pipeline the
        backtest engine and paper trading use."""
        latest_idx = data.union_index()
        if latest_idx.empty or latest_idx.max().date() < day:
            latest_desc = (
                "no data at all" if latest_idx.empty else latest_idx.max().date().isoformat()
            )
            logger.warning(
                "STALE DATA: %s has no %s bar in the store dated %s (latest available: %s) -- "
                "rebalance targets are being computed from stale data; data sync is a "
                "separate concern -- proceeding anyway",
                self._config.name,
                self._config.timeframe.value,
                day.isoformat(),
                latest_desc,
            )

        resolver = StaticUniverseResolver()
        signals = SignalStore(data)
        dv = DataView(data, signals, session_bounds(day)[1])
        warnings: list[str] = []
        equity = self._broker.equity()
        targets = evaluate_targets(
            self._config, dv, resolver, data, current_holdings, equity, warnings
        )
        for w in [*warnings, *resolver.warnings]:
            logger.warning(w)
        return targets

    def _diff_orders(
        self, targets: dict[str, int], current_holdings: dict[str, int], next_day: date
    ) -> list[Order]:
        """Delta orders: SELLs first, then BUYs, each group sorted by symbol
        (deterministic queue order, deterministic client_order_ids)."""
        symbols = sorted(set(targets) | set(current_holdings))
        sells: list[Order] = []
        buys: list[Order] = []
        for symbol in symbols:
            delta = targets.get(symbol, 0) - current_holdings.get(symbol, 0)
            if delta < 0:
                sells.append(self._build_order(symbol, Side.SELL, -delta, next_day))
            elif delta > 0:
                buys.append(self._build_order(symbol, Side.BUY, delta, next_day))
        return [*sells, *buys]

    def _build_order(self, symbol: str, side: Side, qty: int, next_day: date) -> Order:
        return Order(
            client_order_id=f"{self._config.name}-{next_day.isoformat()}-{symbol}-{side.value}",
            symbol=symbol,
            side=side,
            qty=qty,
            order_type=OrderType.MARKET,
            product=self._config.costs.product,
            strategy_id=self._config.name,
            tag=_TAG_REBALANCE,
        )

    # -- scheduler ----------------------------------------------------------

    def build_scheduler(self) -> BackgroundScheduler:
        """A ``BackgroundScheduler`` with three Mon-Fri IST cron jobs: 09:15-09:25
        each minute (session open, retried because the first firing can beat
        the broker having any usable quote), 15:35 (session close, after a
        data-sync job has a window to land the day's closing bars), and every
        5 minutes across the trading session (reconciliation -- the job body
        itself gates the exact 09:15-15:30 window so a single simple cron
        expression suffices). Not started -- the caller starts/shuts it down
        (see ``cli/live_cmds.py``)."""
        scheduler = BackgroundScheduler(timezone=IST)
        scheduler.add_job(
            self._run_open_job,
            CronTrigger(day_of_week="mon-fri", hour=9, minute="15-25", timezone=IST),
            id=f"{self._config.name}-session-open",
            name=f"{self._config.name} session open",
        )
        scheduler.add_job(
            self._run_close_job,
            CronTrigger(
                day_of_week="mon-fri",
                hour=_CLOSE_JOB_HOUR,
                minute=_CLOSE_JOB_MINUTE,
                timezone=IST,
            ),
            id=f"{self._config.name}-session-close",
            name=f"{self._config.name} session close",
        )
        scheduler.add_job(
            self._run_reconcile_job,
            CronTrigger(day_of_week="mon-fri", hour="9-15", minute="*/5", timezone=IST),
            id=f"{self._config.name}-reconcile",
            name=f"{self._config.name} reconciliation",
        )
        return scheduler

    def _run_open_job(self, now: datetime | None = None) -> None:
        """The scheduler's 09:15 callback. A non-trading day is a logged
        no-op; any exception is logged and swallowed -- a bad open must never
        kill the scheduler. ``now`` is overridable for tests."""
        day = (now or now_ist()).date()
        if not self._calendar.is_trading_day(day):
            logger.info("session open %s skipped: not an NSE trading day", day.isoformat())
            return
        try:
            self.on_session_open(day)
        except Exception:
            logger.exception("session open job failed for %s", day.isoformat())

    def _run_close_job(self, now: datetime | None = None) -> None:
        """The scheduler's 15:35 callback. Same no-op / exception-swallowing
        contract as :meth:`_run_open_job`."""
        day = (now or now_ist()).date()
        if not self._calendar.is_trading_day(day):
            logger.info("session close %s skipped: not an NSE trading day", day.isoformat())
            return
        try:
            self.on_session_close(day)
        except Exception:
            logger.exception("session close job failed for %s", day.isoformat())

    def _run_reconcile_job(self, now: datetime | None = None) -> None:
        """The scheduler's every-5-minutes callback. A non-trading day, or a
        firing outside the 09:15-15:30 session window (the cron expression
        itself is coarser than that -- see :meth:`build_scheduler`), is a
        silent no-op. Any exception (including
        ``tradingos.live.reconcile`` not existing yet) is logged and
        swallowed -- reconciliation must never kill the scheduler."""
        ts = now or now_ist()
        day = ts.date()
        if not self._calendar.is_trading_day(day):
            return
        open_ts, close_ts = session_bounds(day)
        if not (open_ts <= ts <= close_ts):
            return
        try:
            mismatches = _reconcile_once(self._broker, self._alerter)
            if mismatches:
                logger.warning(
                    "reconciliation: %d mismatch(es) found for %s",
                    len(mismatches),
                    self._config.name,
                )
        except Exception:
            logger.exception("reconciliation job failed for %s", self._config.name)


__all__ = ["LiveSessionRunner"]

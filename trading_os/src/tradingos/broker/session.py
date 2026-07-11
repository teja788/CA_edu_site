"""Shared session-runner skeleton for paper and live trading.

:class:`~tradingos.paper.runner.PaperSessionRunner` and
:class:`~tradingos.live.runner.LiveSessionRunner` drive the exact same daily
rhythm: place the planned orders at the session open, evaluate the rebalance
off the day's completed bars at the close (via
:func:`~tradingos.engine.event.strategy_runtime.evaluate_targets` — the same
point-in-time-safe pipeline the backtest engine uses), diff targets against
holdings into SELLs-then-BUYs delta orders with deterministic
``client_order_id``\\ s, queue them for the next trading day, and do all of it
automatically on Mon–Fri IST cron jobs that no-op on non-trading days and
swallow exceptions (a bad session must never kill the scheduler).

:class:`BaseSessionRunner` owns that broker-agnostic skeleton; what actually
differs between paper and live stays in the subclasses as template methods —
how a planned order is queued (:meth:`~BaseSessionRunner._queue_planned`), how
a stale planned order is cancelled
(:meth:`~BaseSessionRunner._cancel_stale_planned`), the whole of
``on_session_open`` / ``on_session_close`` (their broker interactions differ
structurally), and any extra cron jobs
(:meth:`~BaseSessionRunner._add_scheduler_jobs`, live's reconciliation pass).

Import rules: this module sits in ``broker/`` (the interface layer) and
imports engine, data and the shared journal schema
(:class:`~tradingos.paper.ledgerdb.PaperStore` — the store both concrete
runners already share); it never imports a concrete broker, and ``engine``
never imports this module (hard rule 7). Each subclass supplies its own
module logger via the ``_logger`` class attribute so session events keep
logging under ``tradingos.paper.runner`` / ``tradingos.live.runner`` exactly
as before the extraction.
"""

from __future__ import annotations

import abc
import logging
from datetime import date, datetime
from typing import ClassVar, Generic, TypeVar

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from tradingos.config.schemas import StrategyConfig
from tradingos.config.settings import Settings
from tradingos.core.models import Order, OrderType, Position, Side
from tradingos.core.timeutils import IST, now_ist, session_bounds
from tradingos.data.calendar import NSECalendar
from tradingos.data.store import BarStore
from tradingos.engine.base import StaticUniverseResolver
from tradingos.engine.dataview import DataView, MarketData, SignalStore
from tradingos.engine.event.strategy_runtime import evaluate_targets
from tradingos.paper.ledgerdb import PaperStore

# After 15:30 (MARKET_CLOSE) so a data sync job has a window to land the day's
# closing bars before the rebalance evaluates them.
CLOSE_JOB_HOUR = 15
CLOSE_JOB_MINUTE = 35

# Orders queued by a session runner's rebalance carry this tag; stale-planned
# cancellation is scoped to it so orders queued by anything else are never
# touched.
TAG_REBALANCE = "rebalance"

#: The concrete broker a runner drives. Unconstrained on purpose: the two
#: runners use broker surfaces beyond ``broker.base.Broker`` (``equity()``,
#: paper's planned queue, live's ``sync_orders``), so the base only pins the
#: shared calls and each subclass binds its own concrete type.
BrokerT = TypeVar("BrokerT")


class BaseSessionRunner(abc.ABC, Generic[BrokerT]):
    """Session-scheduling skeleton shared by the paper and live runners."""

    #: Subclass module's logger — see module docstring (log records keep their
    #: pre-extraction logger names).
    _logger: ClassVar[logging.Logger]

    def __init__(
        self,
        settings: Settings,
        config: StrategyConfig,
        broker: BrokerT,
        *,
        calendar: NSECalendar,
        store: PaperStore,
    ) -> None:
        self._settings = settings
        self._config = config
        self._broker = broker
        self._calendar = calendar
        self._store = store

    # -- session open / close (broker interactions differ structurally) ----

    @abc.abstractmethod
    def on_session_open(self, day: date) -> list[Order]:
        """Place every order queued (by a prior :meth:`on_session_close`) for
        ``day``'s open; returns what was run through ``place_order``."""

    @abc.abstractmethod
    def on_session_close(self, day: date) -> object:
        """Evaluate the rebalance off ``day``'s completed bars and queue the
        delta orders for the next trading day's open. Subclasses narrow the
        return type (paper: the EOD report path; live: the queued orders)."""

    # -- planned (next-open) queue mechanics, broker-specific ---------------

    @abc.abstractmethod
    def _queue_planned(self, order: Order, on_day: date) -> None:
        """Persist ``order`` as planned for ``on_day``'s open (paper: the
        broker owns the queue; live: the runner writes the journal itself)."""

    @abc.abstractmethod
    def _cancel_stale_planned(self, next_day: date, new_ids: set[str]) -> None:
        """Cancel this runner's still-PENDING planned orders for ``next_day``
        that the freshly computed target set no longer wants. A close-job
        re-run (e.g. after a data re-sync changed the targets) would otherwise
        leave the FIRST run's queue entries live. Scoped to
        ``tag == TAG_REBALANCE``."""

    # -- shared close mechanics ---------------------------------------------

    def _queue_rebalance_delta(
        self, day: date, targets: dict[str, int], current_holdings: dict[str, int]
    ) -> list[Order]:
        """Diff ``targets`` against holdings, cancel stale planned orders the
        new delta no longer wants, queue the delta for the next trading day's
        open, and return it."""
        next_day = self._calendar.next_trading_day(day)
        orders = self._diff_orders(targets, current_holdings, next_day)
        self._cancel_stale_planned(next_day, {o.client_order_id for o in orders})
        if orders:
            for order in orders:
                self._queue_planned(order, next_day)
                self._logger.info(
                    "session close %s: queued %s %s %d %s for %s open",
                    day.isoformat(),
                    order.client_order_id,
                    order.side.value,
                    order.qty,
                    order.symbol,
                    next_day.isoformat(),
                )
        else:
            self._logger.info(
                "session close %s: holdings already match targets, nothing queued",
                day.isoformat(),
            )
        return orders

    def _current_positions(self) -> list[Position]:
        # Zerodha semantics split CNC (holdings) from MIS (positions); the
        # broker's own product decides which bucket is populated -- pulling
        # both means this works unmodified for either product.
        return [*self._broker.get_holdings(), *self._broker.get_positions()]

    def _load_market_data(self) -> MarketData:
        """Load bar data exactly as ``cli/backtest_cmds.py`` does (same
        universe-symbol resolution, adjusted prices, full history for
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
        self,
        day: date,
        data: MarketData,
        current_holdings: dict[str, int],
        equity: float | None = None,
    ) -> dict[str, int]:
        """Build a DataView bound to ``day`` 15:30 over pre-loaded ``data`` and
        delegate to ``evaluate_targets`` -- the exact same point-in-time-safe
        pipeline the backtest engine uses.

        ``equity`` lets a caller reuse an already-fetched equity value (live's
        close-snapshot read); ``None`` reads it from the broker here."""
        latest_idx = data.union_index()
        if latest_idx.empty or latest_idx.max().date() < day:
            latest_desc = (
                "no data at all" if latest_idx.empty else latest_idx.max().date().isoformat()
            )
            self._logger.warning(
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
        if equity is None:
            equity = self._broker.equity()
        targets = evaluate_targets(
            self._config, dv, resolver, data, current_holdings, equity, warnings
        )
        for w in [*warnings, *resolver.warnings]:
            self._logger.warning(w)
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
            tag=TAG_REBALANCE,
        )

    # -- scheduler ----------------------------------------------------------

    def build_scheduler(self) -> BackgroundScheduler:
        """A ``BackgroundScheduler`` with two Mon-Fri IST cron jobs -- 09:15-09:25
        each minute (session open, retried because the first firing can beat
        the day's first ticks / the broker having any usable quote;
        ``on_session_open`` implementations are idempotent) and 15:35 (session
        close, after a data-sync job has a window to land the day's closing
        bars) -- plus any subclass extras (:meth:`_add_scheduler_jobs`; live
        adds a reconciliation pass). Not started -- the caller starts/shuts it
        down (see ``cli/paper_cmds.py`` / ``cli/live_cmds.py``)."""
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
                hour=CLOSE_JOB_HOUR,
                minute=CLOSE_JOB_MINUTE,
                timezone=IST,
            ),
            id=f"{self._config.name}-session-close",
            name=f"{self._config.name} session close",
        )
        self._add_scheduler_jobs(scheduler)
        return scheduler

    def _add_scheduler_jobs(self, scheduler: BackgroundScheduler) -> None:
        """Hook for subclass-specific cron jobs. Default: none."""

    def _run_open_job(self, now: datetime | None = None) -> None:
        """The scheduler's 09:15 callback. A non-trading day is a logged
        no-op; any exception is logged and swallowed -- a bad open must never
        kill the scheduler. ``now`` is overridable for tests; the scheduler
        itself always calls this with no arguments (i.e. real wall-clock
        time)."""
        day = (now or now_ist()).date()
        if not self._calendar.is_trading_day(day):
            self._logger.info("session open %s skipped: not an NSE trading day", day.isoformat())
            return
        try:
            self.on_session_open(day)
        except Exception:
            self._logger.exception("session open job failed for %s", day.isoformat())

    def _run_close_job(self, now: datetime | None = None) -> None:
        """The scheduler's 15:35 callback. Same no-op / exception-swallowing
        contract as :meth:`_run_open_job` -- a failed close must not kill the
        scheduler."""
        day = (now or now_ist()).date()
        if not self._calendar.is_trading_day(day):
            self._logger.info("session close %s skipped: not an NSE trading day", day.isoformat())
            return
        try:
            self.on_session_close(day)
        except Exception:
            self._logger.exception("session close job failed for %s", day.isoformat())


__all__ = [
    "CLOSE_JOB_HOUR",
    "CLOSE_JOB_MINUTE",
    "TAG_REBALANCE",
    "BaseSessionRunner",
]

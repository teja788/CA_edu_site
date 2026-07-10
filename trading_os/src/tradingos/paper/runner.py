"""Paper trading session runner: session-open order placement, session-close
rebalance + EOD report, and the cron scheduler that drives both automatically.

Design: :class:`PaperSessionRunner` is deliberately a thin shell over three
individually-testable methods (:meth:`on_session_open`, :meth:`on_session_close`,
:meth:`build_scheduler`). It does NOT own a :class:`~tradingos.paper.ticks.TickStreamer`
-- wiring live ticks into :meth:`~tradingos.paper.broker.PaperBroker.on_tick` is
the CLI's job (``cli/paper_cmds.py``), so this module has no live-network
surface and can be tested entirely offline.

Rebalance evaluation reuses :func:`tradingos.engine.event.strategy_runtime.evaluate_targets`
verbatim -- the exact same point-in-time-safe pipeline the backtest engine
uses -- so paper trading can never silently drift from the pipeline the
backtest validated. Bar data is loaded from the
:class:`~tradingos.data.store.BarStore` exactly as ``cli/backtest_cmds.py``
does (same universe-symbol resolution), and the evaluation
:class:`~tradingos.engine.dataview.DataView` is bound to that day's 15:30
close -- the look-ahead guard (see ``engine/dataview.py``) then makes that
day's own daily bar (and nothing later) visible, mirroring the backtest's
"signals at close of T" timing. No new financial math lives here; sizing and
selection are entirely delegated to ``evaluate_targets``.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from tradingos.config.schemas import StrategyConfig
from tradingos.config.settings import Settings
from tradingos.core.logging import get_logger
from tradingos.core.models import Order, OrderType, Position, Side, Tick
from tradingos.core.timeutils import IST, now_ist, session_bounds
from tradingos.data.calendar import NSECalendar
from tradingos.data.store import BarStore
from tradingos.engine.base import StaticUniverseResolver
from tradingos.engine.dataview import DataView, MarketData, SignalStore
from tradingos.engine.event.strategy_runtime import evaluate_targets
from tradingos.paper.broker import PaperBroker
from tradingos.paper.eod import run_eod
from tradingos.paper.ledgerdb import PaperStore

logger = get_logger(__name__)

# After 15:30 (MARKET_CLOSE) so a data sync job has a window to land the day's
# closing bars before the rebalance evaluates them.
_CLOSE_JOB_HOUR = 15
_CLOSE_JOB_MINUTE = 35


class PaperSessionRunner:
    """Drives one strategy's paper session: place the day's planned orders at
    the open, rebalance + write the EOD report at the close, and (via
    :meth:`build_scheduler`) do both automatically on trading days."""

    def __init__(
        self,
        settings: Settings,
        config: StrategyConfig,
        broker: PaperBroker,
        *,
        calendar: NSECalendar,
        store: PaperStore,
        reference_run_dir: Path | None = None,
    ) -> None:
        self._settings = settings
        self._config = config
        self._broker = broker
        self._calendar = calendar
        self._store = store
        self._reference_run_dir = reference_run_dir

    # -- session open ---------------------------------------------------

    def on_session_open(self, day: date) -> list[Order]:
        """Place every order queued (by a prior :meth:`on_session_close`) for
        ``day``'s open. Returns exactly what the broker placed -- including
        any that were rejected pre-trade, since ``place_planned`` calls
        ``place_order`` directly and a rejection does not raise there."""
        orders = self._broker.place_planned(day)
        for order in orders:
            logger.info(
                "session open %s: placed %s %s %d %s -> %s",
                day.isoformat(),
                order.client_order_id,
                order.side.value,
                order.qty,
                order.symbol,
                order.status.value,
            )
        return orders

    def prime_open_quotes(self, day: date) -> int:
        """Feed ``day``'s official bar OPEN for every relevant symbol (planned
        orders + current holdings) to the broker as a synthetic 09:15 tick.

        This is what lets a *tickless* session (``paper run --once``, no live
        stream) fill its planned orders: the bar open is the day's first tick,
        so orders fill at the same open±slippage the backtest's next-open
        convention uses. Symbols without a bar for ``day`` (not yet synced)
        are skipped with a WARNING — their planned orders stay PENDING.
        Returns the number of quotes fed."""
        symbols = {o.symbol for o in self._store.planned_orders(day)}
        symbols |= {p.symbol for p in self._current_positions()}
        if not symbols:
            return 0

        data = self._load_market_data()
        open_ts = session_bounds(day)[0]
        fed = 0
        for symbol in sorted(symbols):
            if symbol not in data.symbols:
                logger.warning("prime_open_quotes: no data at all for %s", symbol)
                continue
            frame = data.full_frame(symbol)
            rows = frame[frame.index.date == day]  # first bar of `day` (daily or minute)
            if rows.empty:
                logger.warning(
                    "prime_open_quotes: no %s bar for %s on %s (data not synced?) -- "
                    "its planned orders stay PENDING",
                    self._config.timeframe.value,
                    symbol,
                    day.isoformat(),
                )
                continue
            self._broker.on_tick(
                Tick(
                    symbol=symbol,
                    instrument_token=0,  # synthetic; not a Kite token
                    ts=open_ts,
                    last_price=float(rows["open"].iloc[0]),
                )
            )
            fed += 1
        logger.info("prime_open_quotes: fed %d/%d open quotes for %s", fed, len(symbols), day)
        return fed

    # -- session close ----------------------------------------------------

    def on_session_close(self, day: date) -> Path:
        """Mark holdings to the day's closes, snapshot day-end equity, evaluate
        rebalance targets off that day's completed bars, queue the delta orders
        for the next trading day's open, and write the EOD divergence report.
        Returns the report path."""
        close_ts = session_bounds(day)[1]

        positions = self._current_positions()
        current_holdings = {p.symbol: p.qty for p in positions}

        data = self._load_market_data()
        # Mark every held symbol to its last completed close (<= 15:30 of
        # `day`) BEFORE the equity snapshot and target sizing: a replayed
        # broker that saw no ticks (report-only / --once runs) would otherwise
        # value positions at old fill prices and corrupt the divergence metric.
        closes = self._closing_prices(data, current_holdings, close_ts)
        self._broker.mark_to_market(closes)
        self._broker.snapshot(close_ts)

        targets = self._evaluate_targets(day, data, current_holdings)

        next_day = self._calendar.next_trading_day(day)
        orders = self._diff_orders(targets, current_holdings, next_day)
        self._cancel_stale_planned(next_day, {o.client_order_id for o in orders})
        if orders:
            for order in orders:
                self._broker.queue_for_open(order, next_day)
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

        return run_eod(
            self._settings,
            self._config,
            self._store,
            positions,
            reference_run_dir=self._reference_run_dir,
            day=day,
        )

    def _cancel_stale_planned(self, next_day: date, new_ids: set[str]) -> None:
        """Cancel this runner's still-PENDING planned orders for ``next_day``
        that the freshly computed target set no longer wants.

        A close-job re-run (e.g. after a data re-sync changed the targets)
        would otherwise leave the FIRST run's queue entries live: an order for
        a symbol that dropped out of the delta set -- or whose delta flipped
        side -- would still fire at the next open alongside the new orders.
        Orders re-issued with the same client_order_id are upserted by
        ``queue_for_open``, so only the no-longer-wanted remainder is
        cancelled. Scoped to ``tag == "rebalance"`` -- orders queued by anything
        other than this runner are never touched."""
        for stale in self._store.planned_orders(next_day):
            if stale.tag != "rebalance" or stale.client_order_id in new_ids:
                continue
            self._broker.cancel_order(stale.client_order_id)
            logger.info(
                "session close: cancelled stale planned order %s (%s %d %s no longer "
                "in the target delta for %s)",
                stale.client_order_id,
                stale.side.value,
                stale.qty,
                stale.symbol,
                next_day.isoformat(),
            )

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

    @staticmethod
    def _closing_prices(
        data: MarketData, holdings: dict[str, int], close_ts: datetime
    ) -> dict[str, float]:
        """Last completed close (bar index <= ``close_ts``) for each held
        symbol; symbols with no such bar are skipped (keep their last mark)."""
        closes: dict[str, float] = {}
        for symbol, qty in holdings.items():
            if qty == 0 or symbol not in data.symbols:
                continue
            visible = data.full_frame(symbol).loc[:close_ts]
            if visible.empty:
                logger.warning("no completed bar to mark %s at %s", symbol, close_ts)
                continue
            closes[symbol] = float(visible["close"].iloc[-1])
        return closes

    def _evaluate_targets(
        self, day: date, data: MarketData, current_holdings: dict[str, int]
    ) -> dict[str, int]:
        """Build a DataView bound to ``day`` 15:30 over pre-loaded ``data`` and
        delegate to ``evaluate_targets``."""
        latest_idx = data.union_index()
        if latest_idx.empty or latest_idx.max().date() < day:
            latest_desc = "no data at all" if latest_idx.empty else latest_idx.max().date().isoformat()
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
            tag="rebalance",
        )

    # -- scheduler ----------------------------------------------------------

    def build_scheduler(self) -> BackgroundScheduler:
        """A ``BackgroundScheduler`` with two Mon-Fri IST cron jobs: 09:15-09:25
        each minute (session open, retried because the first firing can beat
        the day's first ticks) and 15:35 (session close, after a data-sync job
        has a window to land the day's closing bars). Not started -- the caller
        starts/shuts it down (see ``cli/paper_cmds.py``)."""
        scheduler = BackgroundScheduler(timezone=IST)
        # minute="15-25": the 09:15 firing can race the websocket's first
        # ticks (planned MARKET orders rest / stay PENDING until a same-day
        # quote exists), so retry each minute until 09:25. place_planned is
        # idempotent -- it only touches still-PENDING orders.
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
        return scheduler

    def _run_open_job(self, now: datetime | None = None) -> None:
        """The scheduler's 09:15 callback. A non-trading day is a logged
        no-op; any exception is logged and swallowed -- a bad open must never
        kill the scheduler. ``now`` is overridable for tests; the scheduler
        itself always calls this with no arguments (i.e. real wall-clock
        time)."""
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
        contract as :meth:`_run_open_job` -- a failed close must not kill the
        scheduler."""
        day = (now or now_ist()).date()
        if not self._calendar.is_trading_day(day):
            logger.info("session close %s skipped: not an NSE trading day", day.isoformat())
            return
        try:
            self.on_session_close(day)
        except Exception:
            logger.exception("session close job failed for %s", day.isoformat())


__all__ = ["PaperSessionRunner"]

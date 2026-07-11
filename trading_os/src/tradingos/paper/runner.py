"""Paper trading session runner: session-open order placement, session-close
rebalance + EOD report, and the cron scheduler that drives both automatically.

Design: :class:`PaperSessionRunner` is deliberately a thin shell over three
individually-testable methods (:meth:`on_session_open`, :meth:`on_session_close`,
``build_scheduler``). The session-scheduling skeleton (cron jobs, target
evaluation, delta-order diffing, planned-queue bookkeeping) is shared with the
live runner via :class:`~tradingos.broker.session.BaseSessionRunner`; this
module keeps only what is paper-specific. It does NOT own a
:class:`~tradingos.paper.ticks.TickStreamer` -- wiring live ticks into
:meth:`~tradingos.paper.broker.PaperBroker.on_tick` is the CLI's job
(``cli/paper_cmds.py``), so this module has no live-network surface and can be
tested entirely offline.

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

from tradingos.broker.session import TAG_REBALANCE, BaseSessionRunner
from tradingos.config.schemas import StrategyConfig
from tradingos.config.settings import Settings
from tradingos.core.logging import get_logger
from tradingos.core.models import Order, Tick
from tradingos.core.timeutils import session_bounds
from tradingos.data.calendar import NSECalendar
from tradingos.engine.dataview import MarketData
from tradingos.paper.broker import PaperBroker
from tradingos.paper.eod import run_eod
from tradingos.paper.ledgerdb import PaperStore

logger = get_logger(__name__)


class PaperSessionRunner(BaseSessionRunner[PaperBroker]):
    """Drives one strategy's paper session: place the day's planned orders at
    the open, rebalance + write the EOD report at the close, and (via
    ``build_scheduler``) do both automatically on trading days."""

    _logger = logger  # session events keep logging as tradingos.paper.runner

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
        super().__init__(settings, config, broker, calendar=calendar, store=store)
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
        self._queue_rebalance_delta(day, targets, current_holdings)

        return run_eod(
            self._settings,
            self._config,
            self._store,
            positions,
            reference_run_dir=self._reference_run_dir,
            day=day,
        )

    # -- planned (next-open) queue, owned by the PaperBroker ---------------

    def _queue_planned(self, order: Order, on_day: date) -> None:
        """``PaperBroker`` owns the planned-order queue (unlike live, where
        the runner writes the journal itself)."""
        self._broker.queue_for_open(order, on_day)

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
            if stale.tag != TAG_REBALANCE or stale.client_order_id in new_ids:
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


__all__ = ["PaperSessionRunner"]

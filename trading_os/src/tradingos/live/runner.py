"""Live trading session runner: session-open placement of queued orders,
session-close rebalance evaluation + next-open queueing, and the cron
scheduler (open / close / reconciliation) that drives all three automatically.

Design mirrors :class:`~tradingos.paper.runner.PaperSessionRunner` closely --
the shared skeleton (session-open / session-close split, the
:func:`~tradingos.engine.event.strategy_runtime.evaluate_targets` pipeline
bound to a :class:`~tradingos.engine.dataview.DataView` pinned to the day's
15:30 close, the SELLs-then-BUYs delta ordering with deterministic
``client_order_id``\\ s, and stale-planned-order cancellation on a close
re-run) lives in :class:`~tradingos.broker.session.BaseSessionRunner`. Two
things differ because :class:`~tradingos.live.broker.ZerodhaLiveBroker` is a
thinner adapter than :class:`~tradingos.paper.broker.PaperBroker`:

* **The runner owns the planned-order queue.** ``PaperBroker`` has
  ``queue_for_open`` / ``place_planned`` built in; ``ZerodhaLiveBroker`` does
  not (Zerodha itself has no notion of "queued for tomorrow's open"). Both
  brokers journal to the *same* :class:`~tradingos.paper.ledgerdb.PaperStore`
  schema, so this runner reads/writes the planned-order queue
  (``PaperStore.save_order(planned_for=...)`` / ``PaperStore.planned_orders``)
  directly, and replicates ``PaperBroker.place_planned``'s per-order fault
  tolerance itself in :meth:`~LiveSessionRunner.on_session_open`.
* **No automatic EOD / divergence report.** Paper trading owns the
  backtest-vs-paper divergence narrative (``paper/eod.py``) and writes a
  report on every session close; live's job in this phase is correctness of
  the order flow (Phase 6 acceptance: a dry-run session shows the correct
  intended orders), so ``on_session_close`` still returns the queued orders,
  not a report path, and no report is generated automatically in the close
  job. It DOES, however, snapshot the day's close equity into the journal
  (see :meth:`~LiveSessionRunner._snapshot_close_equity`), exactly as
  ``PaperBroker`` does -- so the live journal accumulates the same daily
  equity curve paper's does. ``cli/live_cmds.py``'s ``live report`` command
  reuses ``paper/eod.py::run_eod`` on demand, off that live journal, to
  render the same report paper gets (charges inside it are ``sync_orders``'s
  cost-model *estimates*, not broker-confirmed contract-note charges -- see
  this module's charges note and docs/assumptions.md).

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

from tradingos.broker.session import TAG_REBALANCE, BaseSessionRunner
from tradingos.config.schemas import StrategyConfig
from tradingos.config.settings import Settings
from tradingos.core.alerts import TelegramAlerter
from tradingos.core.errors import AuthError, BrokerError, KillSwitchActive, RiskViolation
from tradingos.core.logging import get_logger
from tradingos.core.models import Order, OrderStatus
from tradingos.core.timeutils import IST, now_ist, session_bounds
from tradingos.data.calendar import NSECalendar
from tradingos.live.broker import ZerodhaLiveBroker
from tradingos.paper.ledgerdb import PaperStore

logger = get_logger(__name__)


def _reconcile_once(broker: ZerodhaLiveBroker, alerter: TelegramAlerter) -> list[object]:
    """Lazy indirection onto ``tradingos.live.reconcile.reconcile_once``.

    Imported here (not at module scope) so this module never hard-depends on
    ``tradingos.live.reconcile`` -- a module built in parallel with this one.
    A dedicated module-level function (rather than an inline import in the job
    wrapper) so tests can monkeypatch this single seam regardless of whether
    the real module exists yet."""
    from tradingos.live.reconcile import reconcile_once

    return reconcile_once(broker, alerter=alerter)


class LiveSessionRunner(BaseSessionRunner[ZerodhaLiveBroker]):
    """Drives one strategy's live session: place the day's queued orders at
    the open, evaluate the rebalance and queue tomorrow's delta orders at the
    close, and (via ``build_scheduler``) do both automatically -- plus a
    periodic reconciliation pass -- on trading days."""

    _logger = logger  # session events keep logging as tradingos.live.runner

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
        super().__init__(settings, config, broker, calendar=calendar, store=store)
        # Used only by the reconciliation cron job (reconcile_once's alerter
        # kwarg); the broker owns its own alerter for order-flow alerts.
        self._alerter = alerter or TelegramAlerter.from_settings(settings)
        # Injectable clock (tests pin it) for the queue-mechanics timestamps
        # this runner writes itself (see _queue_planned / _cancel_stale_planned).
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
        - ``BrokerError`` -> the order was not (confirmedly) placed this
          attempt; it stays in the journal as the broker left it -- PENDING
          for a scheduler retry, REJECTED (a confirmed broker rejection), or
          OPEN/unconfirmed awaiting reconciliation (an ambiguous failure the
          broker could not resolve against the Kite order book; see
          ``ZerodhaLiveBroker``'s write-ahead journal).

        ``include_dry_placed`` (real sessions only): planned rows a DRY-RUN
        rehearsal already consumed (journalled OPEN with a ``DRY-*`` id) are
        still due for real placement -- the broker supersedes the dry intent.

        Returns the orders actually run through ``place_order`` (including
        pre-trade-rejected ones, which don't raise out of here)."""
        planned = self._store.planned_orders(day, include_dry_placed=not self._broker.dry_run)
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
                    "planned order %s not placed this attempt (journal state decides the "
                    "retry: PENDING retries, OPEN/unconfirmed awaits reconciliation): %s",
                    order.client_order_id,
                    exc,
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
        """Sync the day's fills from Kite, snapshot the day's close equity
        into the journal, evaluate rebalance targets off that day's
        completed bars (identical point-in-time-safe pipeline to paper --
        see module docstring), queue the delta orders for the next trading
        day's open, and return them.

        No automatic EOD / divergence report is produced here -- ``live
        report`` (cli/live_cmds.py) builds one on demand off the journal this
        method just wrote the close snapshot into (see module docstring)."""
        self._broker.sync_orders()  # pick up the day's fills before pricing holdings

        positions = self._current_positions()
        current_holdings = {p.symbol: p.qty for p in positions}

        equity = self._snapshot_close_equity(day)

        data = self._load_market_data()
        targets = self._evaluate_targets(day, data, current_holdings, equity)

        return self._queue_rebalance_delta(day, targets, current_holdings)

    def _snapshot_close_equity(self, day: date) -> float | None:
        """Snapshot ``day``'s 15:30 close equity into the journal, mirroring
        ``PaperSessionRunner.on_session_close``'s close snapshot -- so the
        live journal accumulates the same daily equity curve paper's does
        (consumed by ``paper/eod.py::run_eod`` via ``live report``).

        Reads equity BEFORE margins so a margins-only failure still leaves a
        usable equity value in hand: the snapshot itself needs both equity
        and cash and is skipped if either read fails, but the already-fetched
        equity is returned regardless and reused by ``_evaluate_targets``
        for sizing instead of re-reading it (avoids a second, likely
        identically-failing, broker round trip).

        Returns the equity value read (or ``None`` if the equity read itself
        failed) -- ``AuthError``/``BrokerError`` are caught and logged as a
        warning here so a broker read hiccup never blocks the close
        evaluation that follows; it is not otherwise treated as fatal."""
        equity: float | None = None
        try:
            equity = self._broker.equity()
            cash = self._broker.get_margins().cash_available
        except (AuthError, BrokerError) as exc:
            logger.warning(
                "session close %s: equity/margins read failed, skipping close "
                "equity snapshot: %s",
                day.isoformat(),
                exc,
            )
            return equity
        self._store.snapshot_equity(session_bounds(day)[1], equity, cash)
        return equity

    # -- planned (next-open) queue, owned by the runner --------------------

    def _queue_planned(self, order: Order, on_day: date) -> None:
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
            if stale.tag != TAG_REBALANCE or stale.client_order_id in new_ids:
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

    # -- scheduler ----------------------------------------------------------

    def _add_scheduler_jobs(self, scheduler: BackgroundScheduler) -> None:
        """Add live's third cron job to the base's open/close pair: every 5
        minutes across the trading session (reconciliation -- the job body
        itself gates the exact 09:15-15:30 window, see
        :meth:`_run_reconcile_job`, so a single simple cron expression
        suffices)."""
        scheduler.add_job(
            self._run_reconcile_job,
            CronTrigger(day_of_week="mon-fri", hour="9-15", minute="*/5", timezone=IST),
            id=f"{self._config.name}-reconcile",
            name=f"{self._config.name} reconciliation",
        )

    def _run_reconcile_job(self, now: datetime | None = None) -> None:
        """The scheduler's every-5-minutes callback. A non-trading day, or a
        firing outside the 09:15-15:30 session window (the cron expression
        itself is coarser than that -- see :meth:`_add_scheduler_jobs`), is a
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

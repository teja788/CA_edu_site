"""Live trading broker backed by Zerodha Kite Connect.

:class:`ZerodhaLiveBroker` implements the abstract
:class:`~tradingos.broker.base.Broker` interface so a strategy graduates
backtest -> paper -> live with a config change only. It is the thinnest of the
three brokers: Zerodha itself owns the order book, margins and fills, so this
class is mostly a *safety-gated adapter* onto the Kite REST API plus a durable
local journal that makes order placement idempotent and restart-safe.

Safety-critical design decisions (this code is order flow — correctness and
absence of surprise beat cleverness):

* **dry_run defaults to True.** Going live is always an explicit opt-in
  (``dry_run=False``). In dry-run, order-*mutating* Kite calls (place / modify
  / cancel) are NOT issued -- instead an intent is journalled and the exact
  kwargs are appended to :attr:`intended_calls` for the CLI to print. Read
  calls (ltp / quote / positions / holdings / margins / orders) DO still run in
  dry-run, so the full pre-trade pipeline is exercised against real account
  state. Every dry-run suppression is logged with an unmistakable ``DRY-RUN:``
  prefix at WARNING level.

* **Idempotency / never double-place.** ``place_order`` for a
  ``client_order_id`` already present in the journal in any non-PENDING state
  returns the stored order unchanged and issues NO API call. The journal is the
  single source of "did we already send this?", so a process restart mid-flight
  (new broker instance, same ``live_db_path``) cannot double-place -- the
  reloaded journal row short-circuits the retry.

* **Write-ahead placement journal.** The placement intent (status OPEN, the
  deterministic reconciliation tag, NO ``broker_order_id`` yet) is persisted
  BEFORE ``kite.place_order`` is called, and the learned ``broker_order_id``
  is persisted after. A crash anywhere between the two writes therefore leaves
  an *unconfirmed* row (OPEN, ``broker_order_id is None``) rather than nothing
  -- and an unconfirmed row is never blindly re-placed. It is resolved against
  ``kite.orders()`` by tag (on broker startup, in ``sync_orders`` and at the
  idempotency gate): found -> the broker's row is adopted (order id, status,
  fill); confirmed absent -> the request never reached Kite, so the row is
  rolled back to PENDING and the normal planned-open retry loop places it for
  real; order book unreadable -> it stays unconfirmed (and keeps blocking a
  re-place) until a later resolution succeeds. The same resolution runs when
  ``kite.place_order`` itself raises ambiguously (e.g. a timeout after Kite
  accepted the order): REJECTED is only ever journalled once the tag is
  confirmed absent from the broker's book.

* **Reconciliation via the tag.** Kite order *tags* are <=20 alphanumeric
  characters, far shorter than our 16-hex ``client_order_id``. We derive the
  tag as ``sha1(client_order_id).hexdigest()[:18]`` (18 lowercase-hex chars =
  <=20 alphanumeric, deterministic). ``place_order`` records both the returned
  ``broker_order_id`` and this tag on the journal row; ``sync_orders`` matches
  ``kite.orders()`` rows back to journal orders by ``broker_order_id`` first and
  by tag as a defensive fallback.

* **Charges are ESTIMATES.** A fill journalled by ``sync_orders`` carries a
  cost estimate from :class:`~tradingos.costs.model.CostModel` (the single
  charge seam), NOT the broker's actual contract-note charges. Real charges are
  only known once contract notes are ingested (future work); until then live
  P&L that leans on ``Fill.charges`` is approximate. See docs/assumptions.md.

* **No local cash / oversell guard.** Unlike ``PaperBroker``, this broker does
  not simulate a ledger and therefore runs no local funds/holdings guard --
  Zerodha enforces margins and long-only holdings server-side and rejects the
  order. We surface such a rejection through the exception mapping (BrokerError)
  and, on reconciliation, through ``sync_orders``.

Kite status mapping (``kite.orders()[i]["status"]`` -> ``OrderStatus``):
``COMPLETE`` -> COMPLETE, ``REJECTED`` -> REJECTED, ``CANCELLED`` -> CANCELLED;
every other (OPEN-ish) status -- ``OPEN``, ``TRIGGER PENDING``,
``VALIDATION PENDING``, ``PUT ORDER REQ RECEIVED`` and any unrecognised
non-terminal status -- maps to OPEN, except that an OPEN-ish status with
``filled_quantity > 0`` maps to PARTIAL. Unknown statuses are deliberately
treated as still-working rather than terminal (fail safe: never drop an order).

Journal: reuses :class:`~tradingos.paper.ledgerdb.PaperStore` (broker-agnostic
orders / fills / equity-snapshot tables scoped by ``strategy_id``) keyed on
``settings.live_db_path``. Nothing about that schema is paper-specific.

Equity: ``margins.cash_available + sum(qty*last_price over holdings) +
sum(qty*last_price over positions)``. For our CNC delivery flow holdings and
positions never overlap, so no double counting; ``last_price`` falls back to
``avg_price`` only if the broker omitted it.

Thread safety: every public entry point takes one reentrant lock, mirroring
``PaperBroker`` -- a reconciliation thread (``sync_orders``) and an
order-placing thread must not interleave their check-then-persist sequences.
"""

from __future__ import annotations

import hashlib
import threading
from collections.abc import Callable
from datetime import date, datetime

from tradingos.broker.base import Broker, TickCallback
from tradingos.broker.killswitch import KillSwitch
from tradingos.broker.risk import PreTradeRiskChecker, RiskLimits
from tradingos.config.settings import Settings
from tradingos.core.alerts import TelegramAlerter
from tradingos.core.errors import (
    AuthError,
    BrokerError,
    KillSwitchActive,
    OrderStateError,
    RiskViolation,
)
from tradingos.core.logging import get_logger
from tradingos.core.models import (
    Fill,
    Margins,
    Order,
    OrderStatus,
    OrderType,
    Position,
    Quote,
    Side,
)
from tradingos.core.timeutils import MARKET_OPEN, now_ist, session_bounds, to_naive_ist
from tradingos.costs.model import CostModel
from tradingos.data.calendar import NSECalendar
from tradingos.paper.ledgerdb import DRY_ORDER_ID_PREFIX, PaperStore

logger = get_logger(__name__)

# Kite order statuses we treat as terminal, mapped to our OrderStatus.
_TERMINAL_KITE_STATUS: dict[str, OrderStatus] = {
    "COMPLETE": OrderStatus.COMPLETE,
    "REJECTED": OrderStatus.REJECTED,
    "CANCELLED": OrderStatus.CANCELLED,
    "CANCELED": OrderStatus.CANCELLED,  # tolerate the US spelling defensively
}


def _tag_for(client_order_id: str) -> str:
    """Deterministic Kite order tag for a client order id.

    Kite tags are capped at 20 alphanumeric characters. sha1 hex digest is 40
    lowercase-hex chars; the first 18 are well under the cap, collision-safe at
    our order volumes, and stable across restarts -- so the tag is a usable
    reconciliation join key when a ``broker_order_id`` was somehow never learned.
    """
    return hashlib.sha1(client_order_id.encode("utf-8")).hexdigest()[:18]


def _is_token_exception(exc: BaseException) -> bool:
    """True if ``exc`` is (or is named) a Kite ``TokenException`` -- a stale /
    invalidated access token. Imported lazily so the module never hard-depends
    on kiteconnect at import time; falls back to a class-name check if the
    import is unavailable."""
    try:
        from kiteconnect.exceptions import TokenException
    except Exception:  # pragma: no cover -- kiteconnect always present in this env
        return type(exc).__name__ == "TokenException"
    return isinstance(exc, TokenException)


class ZerodhaLiveBroker(Broker):
    """Live broker over Kite Connect. See the module docstring for the safety
    model (dry-run default, idempotency, tag-based reconciliation, estimated
    charges, journal reuse)."""

    def __init__(
        self,
        settings: Settings,
        *,
        strategy_id: str,
        dry_run: bool = True,
        kite: object | None = None,
        cost_schedule: str = "zerodha_2026",
        risk_limits: RiskLimits | None = None,
        kill_switch: KillSwitch | None = None,
        calendar: NSECalendar | None = None,
        alerter: TelegramAlerter | None = None,
        store: PaperStore | None = None,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        self._settings = settings
        self._strategy_id = strategy_id
        self._dry_run = dry_run
        # Injectable clock (tests pin it); everything time-stamped by this
        # broker reads the SAME clock.
        self._now = now_fn or now_ist

        self._store = store or PaperStore(settings.live_db_path, strategy_id)
        self._cost_model = CostModel(cost_schedule)
        self._calendar = calendar or NSECalendar(settings)
        self._kill_switch = kill_switch or KillSwitch.from_settings(settings)
        self._alerter = alerter or TelegramAlerter.from_settings(settings)
        # Live defaults to market-hours enforcement (RiskLimits.from_settings'
        # own default market_hours_only=True). An explicit RiskLimits wins.
        self._risk = PreTradeRiskChecker(
            risk_limits or RiskLimits.from_settings(settings), self._calendar
        )

        # The Kite client is injected in tests; in production it is built lazily
        # from the daily access token so importing this module never requires
        # kiteconnect and constructing the broker never triggers a login.
        self._kite = kite if kite is not None else self._build_kite()

        # Public: the CLI prints these in dry-run so an operator can eyeball the
        # exact order kwargs that WOULD be sent live.
        self.intended_calls: list[dict] = []
        # Monotonic per-instance counter for synthetic dry-run broker order ids.
        self._dry_seq = 0
        # One reentrant lock over every public entry point (see module docstring).
        self._lock = threading.RLock()
        # Days whose 09:15 day-start-equity snapshot is already written.
        self._day_start_done: set[date] = set()
        self._seed_day_start_done()

        # Crash recovery: resolve any unconfirmed write-ahead placements (see
        # module docstring) against the Kite order book BEFORE this broker can
        # place anything. Live only -- a dry-run broker never sent anything.
        if not self._dry_run:
            self._recover_unconfirmed_on_startup()

    @property
    def dry_run(self) -> bool:
        """True when this broker journals order intents instead of sending
        them to Kite (the default). Public so collaborators (reconcile, CLI)
        never need the private flag."""
        return self._dry_run

    # -- construction helpers ----------------------------------------------

    def _build_kite(self) -> object:
        """Build a real ``kiteconnect.KiteConnect`` with today's access token.
        Imported lazily so tests (which always inject ``kite``) never need
        kiteconnect, and so a stale token surfaces as ``AuthError`` here."""
        from kiteconnect import KiteConnect  # lazy: only the live path needs it

        from tradingos.data.auth import KiteAuth

        access_token = KiteAuth(self._settings).get_access_token()
        return KiteConnect(api_key=self._settings.kite_api_key, access_token=access_token)

    def _seed_day_start_done(self) -> None:
        """Recognise day-start snapshots already in the journal (stamped 09:15)
        so a mid-day restart never overwrites the day's baseline equity."""
        curve = self._store.equity_curve()
        for ts in curve.index:
            if ts.time() == MARKET_OPEN:
                self._day_start_done.add(ts.date())

    # -- Kite call plumbing ------------------------------------------------

    def _read(self, method: str, *args: object) -> object:
        """Invoke a read-only Kite method with full logging and the
        token-expiry guard. Every call logs the method + args at INFO before the
        call and the raw response at DEBUG after (responses are large/frequent).
        A token expiry -> alert + AuthError; any other failure -> BrokerError."""
        logger.info("calling kite.%s(%s)", method, ", ".join(repr(a) for a in args))
        fn = getattr(self._kite, method)
        try:
            resp = fn(*args)
        except Exception as exc:
            if _is_token_exception(exc):
                self._alerter.alert_token_expiry(f"kite.{method}: {exc}")
                raise AuthError(f"Kite access token expired during kite.{method}: {exc}") from exc
            raise BrokerError(f"kite.{method} failed: {exc}") from exc
        logger.debug("kite.%s response: %r", method, resp)
        return resp

    # -- read side ---------------------------------------------------------

    def get_positions(self) -> list[Position]:
        resp = self._read("positions")
        net = resp.get("net", []) if isinstance(resp, dict) else []
        return [
            Position(
                symbol=row["tradingsymbol"],
                qty=int(row.get("quantity", 0)),
                avg_price=float(row.get("average_price", 0.0)),
                last_price=_opt_float(row.get("last_price")),
            )
            for row in net
        ]

    def get_holdings(self) -> list[Position]:
        resp = self._read("holdings")
        rows = resp if isinstance(resp, list) else []
        # qty = settled quantity + T1 (bought yesterday, not yet settled): both
        # are ours and both back a sell, so they count toward the position.
        return [
            Position(
                symbol=row["tradingsymbol"],
                qty=int(row.get("quantity", 0)) + int(row.get("t1_quantity", 0)),
                avg_price=float(row.get("average_price", 0.0)),
                last_price=_opt_float(row.get("last_price")),
            )
            for row in rows
        ]

    def get_margins(self) -> Margins:
        resp = self._read("margins", "equity")
        resp = resp if isinstance(resp, dict) else {}
        available = resp.get("available", {}) or {}
        utilised = resp.get("utilised", {}) or {}
        # Prefer live_balance (real-time), fall back to cash (start-of-day).
        cash = available.get("live_balance")
        if cash is None:
            cash = available.get("cash", 0.0)
        used = utilised.get("debits", 0.0)
        return Margins(cash_available=float(cash), used=float(used))

    def get_quote(self, symbols: list[str]) -> dict[str, Quote]:
        keys = [f"NSE:{s}" for s in symbols]
        resp = self._read("quote", keys)
        resp = resp if isinstance(resp, dict) else {}
        out: dict[str, Quote] = {}
        for symbol in symbols:
            row = resp.get(f"NSE:{symbol}")
            if row is None:
                continue
            depth = row.get("depth", {}) or {}
            buy = depth.get("buy") or []
            sell = depth.get("sell") or []
            ts = _parse_kite_ts(row.get("last_trade_time")) or self._now()
            out[symbol] = Quote(
                symbol=symbol,
                last_price=float(row["last_price"]),
                bid=_opt_float(buy[0].get("price")) if buy else None,
                ask=_opt_float(sell[0].get("price")) if sell else None,
                volume=row.get("volume") or row.get("volume_traded"),
                ts=ts,
            )
        return out

    def _ltp(self, symbol: str) -> float:
        """Last traded price for one NSE symbol via ``kite.ltp``."""
        key = f"NSE:{symbol}"
        resp = self._read("ltp", [key])
        entry = (resp.get(key) if isinstance(resp, dict) else None) or {}
        price = entry.get("last_price")
        if price is None:
            raise BrokerError(f"kite.ltp returned no last_price for {key}")
        return float(price)

    def _account_state(self) -> tuple[float, float, dict[str, int]]:
        """(equity, cash, qty-by-symbol) from margins + holdings + positions,
        read once so a caller that needs all three issues one batch of reads."""
        margins = self.get_margins()
        cash = margins.cash_available
        equity = cash
        qty_by_symbol: dict[str, int] = {}
        for pos in (*self.get_holdings(), *self.get_positions()):
            equity += pos.market_value  # (last_price or avg_price) * qty
            qty_by_symbol[pos.symbol] = qty_by_symbol.get(pos.symbol, 0) + pos.qty
        return round(equity, 2), round(cash, 2), qty_by_symbol

    def equity(self) -> float:
        with self._lock:
            return self._account_state()[0]

    # -- day-start equity snapshot -----------------------------------------

    def _maybe_snapshot_day_start(self, day: date) -> None:
        """Lazily persist the day's opening equity (stamped 09:15) exactly once
        -- the max_daily_loss basis, read back below by the risk check."""
        if day in self._day_start_done:
            return
        equity, cash, _ = self._account_state()
        ts = session_bounds(day)[0]  # 09:15 of that day
        self._store.snapshot_equity(ts, equity, cash)
        self._day_start_done.add(day)

    # -- unconfirmed-placement (write-ahead journal) resolution -------------

    @staticmethod
    def _is_unconfirmed(order: Order) -> bool:
        """True for a write-ahead journal row whose Kite outcome was never
        learned: journalled OPEN (intent persisted) with no ``broker_order_id``
        -- the shape a crash between the write-ahead save and the
        post-placement save leaves behind. Dry-run rows never look like this
        (they always carry a synthetic ``DRY-n`` id)."""
        return order.status == OrderStatus.OPEN and order.broker_order_id is None

    @staticmethod
    def _is_dry_intent(order: Order) -> bool:
        """True for a journal row written by a DRY-RUN session (synthetic
        ``DRY-n`` broker order id) -- nothing exists at the real broker for
        such a row."""
        return str(order.broker_order_id or "").startswith(DRY_ORDER_ID_PREFIX)

    def _find_kite_row_by_tag(self, tag: str | None) -> dict | None:
        """The ``kite.orders()`` row carrying ``tag``, or None if absent.
        Raises AuthError/BrokerError if the order book cannot be read."""
        if not tag:
            return None
        rows = self._read("orders")
        rows = rows if isinstance(rows, list) else []
        for row in rows:
            if row.get("tag") == tag:
                return row
        return None

    def _resolve_unconfirmed(self, order: Order) -> Order | None:
        """Resolve an unconfirmed placement against the Kite order book by tag.

        Returns the updated order if it DID reach the broker (``broker_order_id``
        learned; status/fill synced through :meth:`_apply_sync`), or ``None``
        if the tag is confirmed absent (the request never created an order --
        safe to place). Raises AuthError/BrokerError if the order book cannot
        be read; the journal row is left untouched (still unconfirmed, still
        blocking any blind re-place) in that case."""
        row = self._find_kite_row_by_tag(order.tag)
        if row is None:
            logger.warning(
                "unconfirmed placement %s (tag=%s) is NOT in the Kite order book; "
                "it never reached the broker",
                order.client_order_id,
                order.tag,
            )
            return None
        order.broker_order_id = str(row.get("order_id"))
        filled = int(row.get("filled_quantity", 0) or 0)
        new_status = self._map_status(row.get("status"), filled)
        logger.warning(
            "resolved unconfirmed placement %s to Kite order %s (status=%s)",
            order.client_order_id,
            order.broker_order_id,
            new_status.value,
        )
        if new_status == order.status and filled == order.filled_qty:
            self._store.save_order(order)  # persist the learned broker_order_id
        else:
            self._apply_sync(order, row, new_status, filled)
        return order

    def _recover_unconfirmed_on_startup(self) -> None:
        """Resolve unconfirmed write-ahead rows left by a crash mid-placement,
        via one ``sync_orders`` pass, before this (live) broker instance can
        place anything new. A failed resolution is logged and swallowed: the
        rows stay unconfirmed, which is safe -- the idempotency gate keeps
        them from being blindly re-placed until a later sync succeeds."""
        unconfirmed = [
            o for o in self._store.orders(status=OrderStatus.OPEN) if o.broker_order_id is None
        ]
        if not unconfirmed:
            return
        logger.warning(
            "startup: %d unconfirmed placement(s) in the journal (crash mid-placement?); "
            "reconciling against the Kite order book before anything new is placed",
            len(unconfirmed),
        )
        try:
            self.sync_orders()
        except (AuthError, BrokerError):
            logger.exception(
                "startup reconciliation of unconfirmed placements failed; they stay "
                "journalled OPEN (blind re-placement stays blocked) until a later "
                "sync_orders succeeds"
            )

    # -- placement ---------------------------------------------------------

    def _reject(self, order: Order, message: str, now: datetime) -> None:
        """Persist ``order`` REJECTED with ``message`` and fire the alert (mirror
        of PaperBroker._reject). Stamps created_at at rejection time so the order
        counts, conservatively, toward the day's order tally. Caller decides
        whether to re-raise."""
        order.created_at = now
        order.updated_at = now
        order.transition(OrderStatus.REJECTED, message)
        self._store.save_order(order)
        self._alerter.alert_rejection(order, message)

    def _place_kwargs(self, order: Order) -> dict:
        """The exact ``kite.place_order`` kwargs for ``order``. Kept explicit and
        flat so it can be asserted field-for-field in review and tests."""
        kwargs: dict[str, object] = {
            "variety": "regular",
            "exchange": order.exchange,  # "NSE"
            "tradingsymbol": order.symbol,
            "transaction_type": order.side.value,  # "BUY" / "SELL"
            "quantity": order.qty,
            "product": order.product.value,  # "CNC" / "MIS"
            "order_type": order.order_type.value,  # "MARKET" / "LIMIT" / "SL" / "SL-M"
            "validity": "DAY",
            "tag": _tag_for(order.client_order_id),
        }
        # LIMIT (and SL, a stop-LIMIT) carry a limit price; SL / SL-M carry a
        # trigger. MARKET / SL-M carry no limit price.
        if order.order_type in (OrderType.LIMIT, OrderType.SL):
            kwargs["price"] = order.limit_price
        if order.order_type in (OrderType.SL, OrderType.SL_M):
            kwargs["trigger_price"] = order.trigger_price
        return kwargs

    def place_order(self, order: Order) -> Order:
        with self._lock:
            return self._place_order_locked(order)

    def _place_order_locked(self, order: Order) -> Order:
        # (a) idempotency -- a stored, non-PENDING order is a completed placement
        # (or a rejection). Return it verbatim; issue NO API call. This is what
        # makes a restart / retry safe from double-placing. Two live-mode
        # exceptions, both resolved here rather than blindly short-circuited:
        #
        # * an UNCONFIRMED write-ahead row (crash / network failure between the
        #   write-ahead save and the post-placement save): resolve it against
        #   the Kite order book by tag FIRST. Found -> adopt it (no second
        #   placement); confirmed absent -> place it for real below; order book
        #   unreadable -> the resolution raises, and the row keeps blocking a
        #   blind re-place.
        # * a DRY-RUN intent (synthetic ``DRY-n`` broker id): nothing exists at
        #   the real broker, so a live session must supersede it -- otherwise a
        #   morning dry-run rehearsal would consume the day's orders and the
        #   real session would silently place nothing.
        stored = self._store.get_order(order.client_order_id)
        if stored is not None and stored.status != OrderStatus.PENDING:
            if not self._dry_run and self._is_unconfirmed(stored):
                resolved = self._resolve_unconfirmed(stored)
                if resolved is not None:
                    return resolved
                order = stored  # confirmed absent at the broker: place it for real
            elif not self._dry_run and not stored.status.is_terminal and self._is_dry_intent(
                stored
            ):
                logger.warning(
                    "superseding dry-run intent %s (%s) with a live placement",
                    stored.client_order_id,
                    stored.broker_order_id,
                )
                order = stored
            else:
                logger.info(
                    "idempotent place_order: %s already in journal as %s; no API call",
                    order.client_order_id,
                    stored.status.value,
                )
                return stored

        now = self._now()
        today = now.date()

        # (b) kill switch FIRST -- cheapest, side-effect-free check, so a halted
        # broker never touches the Kite API at all.
        try:
            self._kill_switch.check()
        except KillSwitchActive as exc:
            self._reject(order, str(exc), now)
            raise

        # (c) pre-trade risk. Establish the day's baseline equity (the
        # max_daily_loss basis) before the check reads it back.
        self._maybe_snapshot_day_start(today)
        ref_price = order.limit_price if order.limit_price is not None else self._ltp(order.symbol)
        equity, _cash, positions = self._account_state()
        orders_today = self._store.orders_placed_count(today)
        day_start_equity = self._store.day_start_equity(today)
        if day_start_equity is None:
            day_start_equity = equity
        try:
            self._risk.check(
                order,
                price=ref_price,
                equity=equity,
                positions=positions,
                orders_today=orders_today,
                day_start_equity=day_start_equity,
                now=now,
            )
        except RiskViolation as exc:
            self._reject(order, str(exc), now)
            raise

        # (d) build the exact Kite kwargs.
        kwargs = self._place_kwargs(order)
        order.tag = kwargs["tag"]  # persist the reconciliation key on the journal row

        # (e) dry-run: journal the intent, never call the API.
        if self._dry_run:
            self._dry_seq += 1
            order.broker_order_id = f"{DRY_ORDER_ID_PREFIX}{self._dry_seq}"
            order.created_at = now
            order.updated_at = now
            order.transition(OrderStatus.OPEN)
            self._store.save_order(order)
            self.intended_calls.append(kwargs)
            logger.warning("DRY-RUN: would call kite.place_order(**%r)", kwargs)
            return order

        # (f) live: journal the placement intent BEFORE the API call (the
        # write-ahead journal -- see module docstring). A crash between this
        # save and the post-placement save below leaves an unconfirmed row
        # (OPEN, no broker_order_id) that a restart resolves against the Kite
        # order book by tag instead of re-placing -- the double-order window
        # this ordering exists to close.
        order.created_at = now
        order.updated_at = now
        order.broker_order_id = None
        order.filled_qty = 0
        if order.status == OrderStatus.PENDING:
            order.transition(OrderStatus.OPEN)
        else:
            # Re-placing a confirmed-absent unconfirmed row / superseding a
            # dry-run intent: the row is already OPEN in the journal. Keeping
            # it OPEN is a journal-level reset, not a lifecycle transition.
            order.status = OrderStatus.OPEN
        self._store.save_order(order)

        logger.info("calling kite.place_order(**%r)", kwargs)
        try:
            resp = self._kite.place_order(**kwargs)  # type: ignore[attr-defined]
        except Exception as exc:
            return self._handle_place_failure(order, exc, now)

        logger.info("kite.place_order response: %r", resp)
        order.broker_order_id = str(resp)  # place_order returns the order_id
        order.updated_at = now
        self._store.save_order(order)
        return order

    def _handle_place_failure(self, order: Order, exc: Exception, now: datetime) -> Order:
        """Decide what a ``kite.place_order`` exception means for the
        write-ahead journal row.

        * Token expiry: the request was refused at the auth gate, so nothing
          was placed. Roll the row back to PENDING (do NOT burn it as
          REJECTED) so a re-auth'd retry of the same ``client_order_id``
          places normally.
        * Anything else is AMBIGUOUS -- e.g. a timeout after Kite accepted the
          order -- so consult the order book by tag before deciding: found ->
          the order IS live at the broker; adopt and return it. Confirmed
          absent -> a genuine placement failure; journal REJECTED, alert,
          re-raise. Order book unreadable -> leave the row OPEN/unconfirmed
          (the idempotency gate blocks a blind retry) and raise.
        """
        if _is_token_exception(exc):
            # Journal rollback, not a lifecycle transition -- OPEN -> PENDING
            # is deliberately not a legal Order.transition.
            order.status = OrderStatus.PENDING
            order.broker_order_id = None
            order.updated_at = now
            self._store.save_order(order)
            self._alerter.alert_token_expiry(f"place_order: {exc}")
            raise AuthError(f"Kite access token expired placing order: {exc}") from exc

        try:
            resolved = self._resolve_unconfirmed(order)
        except (AuthError, BrokerError):
            msg = (
                f"kite.place_order failed ({exc}) and the order book could not be read "
                f"to confirm the outcome; {order.client_order_id} left journalled OPEN "
                f"(unconfirmed) for reconciliation -- it will NOT be blindly re-placed"
            )
            logger.error(msg)
            self._alerter.alert_risk(msg)
            raise BrokerError(msg) from exc
        if resolved is not None:
            logger.warning(
                "kite.place_order raised (%s) but the order DID reach the broker as %s; "
                "adopted from the order book",
                exc,
                resolved.broker_order_id,
            )
            return resolved
        # Confirmed absent at the broker (margin shortfall, bad symbol, ...):
        # persist REJECTED so the journal reflects reality, alert, re-raise.
        self._reject(order, str(exc), now)
        raise BrokerError(f"kite.place_order failed: {exc}") from exc

    # -- modify / cancel ---------------------------------------------------

    def modify_order(
        self,
        client_order_id: str,
        qty: int | None = None,
        limit_price: float | None = None,
        trigger_price: float | None = None,
    ) -> Order:
        with self._lock:
            order = self._store.get_order(client_order_id)
            if order is None:
                raise BrokerError(f"unknown order {client_order_id!r}")
            if order.status.is_terminal:
                raise OrderStateError(f"cannot modify a {order.status.value} order")
            # Kill switch: a modification can INCREASE exposure (qty up), so an
            # engaged switch blocks it exactly like a fresh placement. The order
            # keeps working at the broker exactly as previously accepted -- no
            # journal write, no REJECTED (mirrors the risk-violation contract
            # below). Cancels stay allowed: they only reduce risk.
            self._kill_switch.check()
            if not self._dry_run and (
                order.broker_order_id is None or self._is_dry_intent(order)
            ):
                # PENDING planned rows, unconfirmed write-ahead rows and dry-run
                # intents were never (confirmedly) placed at Kite; a modify call
                # would send a None / "DRY-n" order id to the API.
                raise OrderStateError(
                    f"cannot modify {client_order_id!r}: not (confirmed) placed at the "
                    f"broker (status {order.status.value}, broker_order_id "
                    f"{order.broker_order_id!r})"
                )
            new_qty = qty if qty is not None else order.qty
            new_limit = limit_price if limit_price is not None else order.limit_price
            new_trigger = trigger_price if trigger_price is not None else order.trigger_price
            now = self._now()

            # A modification must pass the same pre-trade risk gates as a fresh
            # placement (mirrors PaperBroker._validate_modification): Zerodha
            # re-validates margins server-side, but OUR self-imposed limits
            # (max_order_value, max_position_pct, restricted list, daily loss)
            # would otherwise be bypassable by inflating qty after acceptance.
            # On violation: raise and leave the order working exactly as
            # previously accepted -- no journal write, no API call, no REJECTED
            # (the order is still live at the broker). orders_today=0: a
            # modification is not a new placement and must not trip the tally.
            self._maybe_snapshot_day_start(now.date())
            candidate = order.model_copy()
            candidate.qty = new_qty
            candidate.limit_price = new_limit
            candidate.trigger_price = new_trigger
            ref_price = new_limit if new_limit is not None else self._ltp(order.symbol)
            equity, _cash, positions = self._account_state()
            day_start_equity = self._store.day_start_equity(now.date())
            if day_start_equity is None:
                day_start_equity = equity
            self._risk.check(
                candidate,
                price=ref_price,
                equity=equity,
                positions=positions,
                orders_today=0,
                day_start_equity=day_start_equity,
                now=now,
            )

            if self._dry_run:
                order.qty = new_qty
                order.limit_price = new_limit
                order.trigger_price = new_trigger
                order.updated_at = now
                self._store.save_order(order)
                logger.warning(
                    "DRY-RUN: would call kite.modify_order(variety='regular', order_id=%r, "
                    "quantity=%r, price=%r, trigger_price=%r)",
                    order.broker_order_id,
                    new_qty,
                    new_limit,
                    new_trigger,
                )
                return order

            kwargs: dict[str, object] = {
                "variety": "regular",
                "order_id": order.broker_order_id,
                "quantity": new_qty,
                "order_type": order.order_type.value,
                "validity": "DAY",
            }
            if new_limit is not None:
                kwargs["price"] = new_limit
            if new_trigger is not None:
                kwargs["trigger_price"] = new_trigger
            logger.info("calling kite.modify_order(**%r)", kwargs)
            try:
                resp = self._kite.modify_order(**kwargs)  # type: ignore[attr-defined]
            except Exception as exc:
                if _is_token_exception(exc):
                    self._alerter.alert_token_expiry(f"modify_order: {exc}")
                    raise AuthError(f"Kite access token expired modifying order: {exc}") from exc
                raise BrokerError(f"kite.modify_order failed: {exc}") from exc
            logger.info("kite.modify_order response: %r", resp)
            order.qty = new_qty
            order.limit_price = new_limit
            order.trigger_price = new_trigger
            order.updated_at = now
            self._store.save_order(order)
            return order

    def cancel_order(self, client_order_id: str) -> Order:
        with self._lock:
            return self._cancel_order_locked(client_order_id)

    def _cancel_order_locked(self, client_order_id: str) -> Order:
        order = self._store.get_order(client_order_id)
        if order is None:
            raise BrokerError(f"unknown order {client_order_id!r}")
        if order.status.is_terminal:
            raise OrderStateError(f"cannot cancel a {order.status.value} order")
        now = self._now()

        if self._dry_run:
            order.transition(OrderStatus.CANCELLED)
            order.updated_at = now
            self._store.save_order(order)
            logger.warning(
                "DRY-RUN: would call kite.cancel_order(variety='regular', order_id=%r)",
                order.broker_order_id,
            )
            return order

        # Orders that never reached Kite are cancelled in the journal only --
        # there is nothing at the broker to cancel, and kite.cancel_order with
        # a None / "DRY-n" order id would hit the API with garbage.
        if order.status == OrderStatus.PENDING or self._is_dry_intent(order):
            prior_status = order.status.value
            order.transition(OrderStatus.CANCELLED)
            order.updated_at = now
            self._store.save_order(order)
            logger.info(
                "cancelled %s journal-only (never sent to the broker: was %s, "
                "broker_order_id=%r)",
                client_order_id,
                prior_status,
                order.broker_order_id,
            )
            return order

        if self._is_unconfirmed(order):
            # Placement outcome unknown: resolve against the order book FIRST
            # (raises if the book is unreadable -- never guess about a
            # possibly-live order). Confirmed absent -> journal-only cancel.
            resolved = self._resolve_unconfirmed(order)
            if resolved is None:
                order.transition(OrderStatus.CANCELLED)
                order.updated_at = now
                self._store.save_order(order)
                return order
            order = resolved
            if order.status.is_terminal:
                raise OrderStateError(
                    f"cannot cancel {client_order_id!r}: resolved at the broker as "
                    f"{order.status.value}"
                )

        kwargs = {"variety": "regular", "order_id": order.broker_order_id}
        logger.info("calling kite.cancel_order(**%r)", kwargs)
        try:
            resp = self._kite.cancel_order(**kwargs)  # type: ignore[attr-defined]
        except Exception as exc:
            if _is_token_exception(exc):
                self._alerter.alert_token_expiry(f"cancel_order: {exc}")
                raise AuthError(f"Kite access token expired cancelling order: {exc}") from exc
            raise BrokerError(f"kite.cancel_order failed: {exc}") from exc
        logger.info("kite.cancel_order response: %r", resp)
        # We mark CANCELLED once Kite ACCEPTS the cancel request. In the rare
        # cancel/fill race the order can still fill at the broker; sync_orders
        # reconciles from kite.orders() and is the source of truth -- but note
        # that because CANCELLED is terminal, sync_orders skips an order already
        # marked here, so an operator wanting certainty should sync_orders before
        # assuming a cancel is final.
        order.transition(OrderStatus.CANCELLED)
        order.updated_at = now
        self._store.save_order(order)
        return order

    def cancel_all_open(self) -> list[Order]:
        """Cancel every working (OPEN / PARTIAL) journal order -- the kill-switch
        CLI's panic button. Per-order fault tolerant: one failed cancel is
        logged and the rest proceed. Returns the orders actually cancelled."""
        cancelled: list[Order] = []
        with self._lock:
            working = [
                o
                for o in self._store.orders()
                if o.status in (OrderStatus.OPEN, OrderStatus.PARTIAL)
            ]
            for order in working:
                try:
                    cancelled.append(self._cancel_order_locked(order.client_order_id))
                except (BrokerError, AuthError) as exc:
                    logger.warning(
                        "cancel_all_open: failed to cancel %s (%s): %s",
                        order.client_order_id,
                        order.broker_order_id,
                        exc,
                    )
        return cancelled

    # -- reconciliation ----------------------------------------------------

    def sync_orders(self) -> list[Order]:
        """Reconcile the journal against ``kite.orders()``. Returns the journal
        orders whose state changed. In dry-run this is a no-op (nothing was
        placed at the broker)."""
        with self._lock:
            if self._dry_run:
                logger.info("DRY-RUN: sync_orders is a no-op (no orders at the broker)")
                return []

            rows = self._read("orders")
            rows = rows if isinstance(rows, list) else []
            journal = self._store.orders()
            by_broker_id = {o.broker_order_id: o for o in journal if o.broker_order_id}
            by_tag = {o.tag: o for o in journal if o.tag}

            changed: list[Order] = []
            found_at_broker: set[str] = set()
            for row in rows:
                order = by_broker_id.get(str(row.get("order_id")))
                if order is None:
                    order = by_tag.get(row.get("tag"))  # defensive fallback
                if order is None:
                    continue  # not one of ours
                found_at_broker.add(order.client_order_id)
                filled = int(row.get("filled_quantity", 0) or 0)
                new_status = self._map_status(row.get("status"), filled)
                adopted = order.broker_order_id is None and row.get("order_id") is not None
                if adopted:
                    # Tag-only match (unconfirmed write-ahead row): learn the
                    # broker order id so later cancel/modify calls carry a real
                    # id, not None.
                    order.broker_order_id = str(row.get("order_id"))
                if order.status.is_terminal:
                    # Terminal journal rows are normally skipped -- that is what
                    # makes sync idempotent (a second sync never re-records a
                    # fill). The ONE exception is a journal-CANCELLED order: we
                    # mark CANCELLED as soon as Kite ACCEPTS the cancel request,
                    # but the broker may still have filled it in the cancel/fill
                    # race -- correct it when Kite reports COMPLETE, or more
                    # filled quantity than the journal has covered.
                    if order.status != OrderStatus.CANCELLED:
                        continue
                    if new_status != OrderStatus.COMPLETE and filled <= order.filled_qty:
                        continue
                elif new_status == order.status and filled == order.filled_qty:
                    if adopted:
                        # Nothing else changed, but the learned broker id must
                        # be persisted (it confirms the placement).
                        self._store.save_order(order)
                        changed.append(order)
                    continue
                self._apply_sync(order, row, new_status, filled)
                changed.append(order)

            # Unconfirmed write-ahead rows (OPEN, no broker_order_id -- a crash
            # between the write-ahead save and the post-placement save) that
            # are NOT in the order book never reached Kite: roll them back to
            # PENDING so the planned-open retry loop (or a direct re-place of
            # the same client_order_id) can place them for real. Rows that DID
            # reach Kite were adopted above via the tag match.
            for order in journal:
                if order.client_order_id in found_at_broker or not self._is_unconfirmed(
                    order
                ):
                    continue
                msg = (
                    f"unconfirmed placement {order.client_order_id} (tag={order.tag}) is "
                    f"not in the Kite order book; rolled back to PENDING for re-placement"
                )
                logger.warning("sync_orders: %s", msg)
                # Journal rollback, not a lifecycle transition (see place path).
                order.status = OrderStatus.PENDING
                order.updated_at = self._now()
                self._store.save_order(order)
                self._alerter.alert_risk(msg)
                changed.append(order)
            return changed

    def kite_orders(self) -> list[dict]:
        """Raw ``kite.orders()`` rows (read-only) -- the FULL order book, unlike
        ``sync_orders``'s return value which is only the orders whose journal
        state changed this call. Like the other read calls (ltp / quote /
        positions / holdings / margins -- see module docstring), this runs in
        dry-run too: it queries Kite for the real account's order book
        regardless of whether *this* broker instance would place orders for
        real. Used by ``tradingos.live.reconcile`` to detect drift
        ``sync_orders`` itself cannot fix (e.g. a journal order with no
        matching row at the broker at all)."""
        rows = self._read("orders")
        return rows if isinstance(rows, list) else []

    def _map_status(self, kite_status: object, filled_qty: int) -> OrderStatus:
        status = str(kite_status or "").upper()
        terminal = _TERMINAL_KITE_STATUS.get(status)
        if terminal is not None:
            return terminal
        # Any other status is OPEN-ish (OPEN / TRIGGER PENDING / VALIDATION
        # PENDING / PUT ORDER REQ RECEIVED / unrecognised). A partial fill on a
        # still-working order shows as PARTIAL.
        return OrderStatus.PARTIAL if filled_qty > 0 else OrderStatus.OPEN

    def _apply_sync(self, order: Order, row: dict, new_status: OrderStatus, filled: int) -> None:
        ts = _parse_kite_ts(row.get("order_timestamp")) or self._now()
        # Fills are journalled only when an order reaches a terminal state (one
        # estimated Fill covering everything filled by then), so the quantity
        # already covered by recorded fills is order.filled_qty if the journal
        # row is already terminal (the cancel/fill-race correction path), else 0.
        already_covered = order.filled_qty if order.status.is_terminal else 0

        if new_status == OrderStatus.COMPLETE:
            total = filled or order.qty
            if order.status == OrderStatus.CANCELLED:
                # Cancel/fill race correction: the broker filled the order after
                # our cancel request was accepted. A journal correction, not a
                # lifecycle transition (CANCELLED is terminal in the state
                # machine), hence the direct assignment.
                order.status = OrderStatus.COMPLETE
            else:
                order.transition(OrderStatus.COMPLETE)
            order.filled_qty = total
            order.updated_at = ts
            fill = self._estimated_fill(order, row, ts, total - already_covered)
            if fill is not None:
                # One transaction: a persisted fill beside a still-non-terminal
                # order row would double-count on a subsequent sync/restart.
                self._store.record_fill_and_order(fill, order)
                self._alerter.alert_fill(fill)
            else:
                self._store.save_order(order)
            return

        if new_status in (OrderStatus.CANCELLED, OrderStatus.REJECTED):
            message = row.get("status_message")
            status_changed = new_status != order.status
            if status_changed:
                order.transition(new_status, message)
            order.filled_qty = max(filled, order.filled_qty)
            order.updated_at = ts
            # A partial fill learned at (or after) the terminal state must
            # still be journalled -- those shares/rupees are real. Without
            # this, "partially filled then cancelled/rejected" would leave a
            # position the ledger never heard about.
            fill = None
            if filled - already_covered > 0:
                fill = self._estimated_fill(order, row, ts, filled - already_covered)
            if fill is not None:
                self._store.record_fill_and_order(fill, order)
                self._alerter.alert_fill(fill)
            else:
                self._store.save_order(order)
            if status_changed:
                self._alerter.alert_rejection(order, message or new_status.value)
            return

        # Still working: OPEN -> PARTIAL (a new partial fill) or a filled_qty
        # bump within OPEN/PARTIAL. Only transition when the status actually
        # changes (OPEN->OPEN / PARTIAL->PARTIAL with a bigger fill just updates
        # filled_qty). PARTIAL fills are NOT journalled as Fills while the order
        # is working -- the (single) estimated Fill is emitted once the order
        # reaches a terminal state (COMPLETE, or CANCELLED/REJECTED with a
        # partial fill).
        if new_status != order.status:
            order.transition(new_status)
        order.filled_qty = filled
        order.updated_at = ts
        self._store.save_order(order)

    def _estimated_fill(self, order: Order, row: dict, ts: datetime, qty: int) -> Fill | None:
        """Build the estimated Fill for ``qty`` shares of a synced order, or
        None if the quantity/price is non-positive (anomalous -- journalled
        without a Fill and logged).

        Charges are ESTIMATES from the cost model, NOT the broker's
        contract-note charges (see module docstring / docs/assumptions.md),
        priced at the schedule in force on the fill date. The DP charge
        applies once per scrip per day on the sell side; it is deduplicated
        against the fills already journalled for that day (restart-safe: the
        journal, not process memory, is the record)."""
        price = _opt_float(row.get("average_price")) or 0.0
        if qty <= 0 or price <= 0:
            logger.warning(
                "sync_orders: %s %s with qty=%s price=%s; no Fill recorded",
                order.client_order_id,
                order.status.value,
                qty,
                price,
            )
            return None
        value = qty * price
        first_sell = True
        if order.side == Side.SELL:
            sold_today = {
                f.symbol for f in self._store.fills(day=ts.date()) if f.side == Side.SELL
            }
            first_sell = order.symbol not in sold_today
        charges = self._cost_model.order_charges(
            order.side,
            order.product,
            value,
            first_sell_of_scrip_today=first_sell,
            trade_date=ts.date(),
        ).total
        return Fill(
            client_order_id=order.client_order_id,
            symbol=order.symbol,
            side=order.side,
            qty=qty,
            price=price,
            ts=ts,
            charges=charges,
            product=order.product,
        )

    # -- journal read side -------------------------------------------------

    def get_order(self, client_order_id: str) -> Order:
        order = self._store.get_order(client_order_id)
        if order is None:
            raise BrokerError(f"unknown order {client_order_id!r}")
        return order

    def get_orders(self) -> list[Order]:
        return self._store.orders()

    def stream_ticks(self, symbols: list[str], callback: TickCallback) -> None:
        raise NotImplementedError(
            "ZerodhaLiveBroker does not stream ticks; use tradingos.paper.ticks.TickStreamer"
        )


def _opt_float(value: object) -> float | None:
    """Coerce an optional numeric Kite field to float, treating 0 / None /
    empty as absent (Kite reports missing depth levels as a 0 price)."""
    if value is None or value == 0:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _parse_kite_ts(value: object) -> datetime | None:
    """Parse a Kite timestamp (a ``datetime`` from the SDK, or an ISO / Kite
    ``"YYYY-MM-DD HH:MM:SS"`` string) into a tz-naive IST datetime, or None."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return to_naive_ist(value)
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        try:
            return to_naive_ist(datetime.fromisoformat(value))
        except ValueError:
            return None
    return None


__all__ = ["ZerodhaLiveBroker"]

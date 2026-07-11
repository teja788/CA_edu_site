"""SQLite persistence for the paper virtual ledger.

Mirrors the engine-cache + ``SQLModel.metadata.create_all`` pattern of
``experiments/db.py`` / ``data/meta.py``, keyed on ``settings.paper_db_path``.

Positions and cash are NEVER stored here — they are derived by replaying fills
through ``engine/event/portfolio.py::Ledger``, the single source of money
math. This module only persists the raw event log (orders, fills, equity
snapshots) plus one run row per strategy so a restart can rebuild state.

Enum fields are stored as their plain ``str`` values; ``PaperStore`` converts
:class:`~tradingos.core.models.Order` / :class:`~tradingos.core.models.Fill`
to/from rows losslessly, including ``None`` fields and enum round-trips.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
from sqlalchemy import UniqueConstraint, func
from sqlalchemy.engine import Engine
from sqlmodel import Field, Session, SQLModel, create_engine, select

from tradingos.core.logging import get_logger
from tradingos.core.models import Fill, Order, OrderStatus, OrderType, Product, Side
from tradingos.core.timeutils import now_ist

logger = get_logger(__name__)

# Prefix of the synthetic broker_order_ids a DRY-RUN live session journals
# ("DRY-1", "DRY-2", ...). Defined here (not in live/broker.py) because the
# store must recognise them too and live already imports from this module --
# the reverse import would be circular.
DRY_ORDER_ID_PREFIX = "DRY-"

_engines: dict[Path, Engine] = {}


def _day_bounds(day: date) -> tuple[datetime, datetime]:
    """Half-open [00:00 of ``day``, 00:00 of ``day``+1) window for SQL-side
    date filtering of the naive-IST datetime columns. Equivalent to
    ``value.date() == day`` (and excludes NULLs, as the Python-side filters
    did)."""
    start = datetime(day.year, day.month, day.day)
    return start, start + timedelta(days=1)


def paper_engine(db_path: Path) -> Engine:
    """Return (creating on first use) the SQLAlchemy engine for this paper
    ledger DB. Cached per resolved path. Creates parent dirs and the paper
    tables on first use only — a cached engine skips the DDL, so the
    per-order hot path never re-runs ``create_all``."""
    path = Path(db_path).resolve()
    eng = _engines.get(path)
    if eng is None:
        path.parent.mkdir(parents=True, exist_ok=True)
        eng = create_engine(f"sqlite:///{path}")
        SQLModel.metadata.create_all(eng)
        _engines[path] = eng
    return eng


@contextmanager
def paper_db_session(db_path: Path) -> Iterator[Session]:
    """Transactional session on the paper ledger DB: commits on success, rolls
    back on error, always closes."""
    session = Session(paper_engine(db_path))
    try:
        yield session
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


# --------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------


class PaperRunRow(SQLModel, table=True):
    """One row per strategy_id: the capital/config the paper session started
    with."""

    __tablename__ = "paper_runs"

    id: int | None = Field(default=None, primary_key=True)
    strategy_id: str = Field(index=True, unique=True)
    config_hash: str = ""
    capital: float
    created_at: datetime


class PaperOrderRow(SQLModel, table=True):
    """Every ``Order`` ever seen by the paper broker for this strategy,
    upserted by ``client_order_id`` as its status changes."""

    __tablename__ = "paper_orders"

    id: int | None = Field(default=None, primary_key=True)
    client_order_id: str = Field(index=True, unique=True)
    strategy_id: str = Field(index=True)
    broker_order_id: str | None = None
    symbol: str
    exchange: str = "NSE"
    side: str
    qty: int
    filled_qty: int = 0
    order_type: str
    product: str
    limit_price: float | None = None
    trigger_price: float | None = None
    status: str
    status_message: str | None = None
    tag: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    planned_for: date | None = Field(default=None, index=True)  # next-open queue date


class PaperFillRow(SQLModel, table=True):
    """Append-only fill log; the replay source for restart-safe ledger
    reconstruction."""

    __tablename__ = "paper_fills"

    id: int | None = Field(default=None, primary_key=True)
    strategy_id: str = Field(index=True)
    client_order_id: str = Field(index=True)
    symbol: str
    side: str
    qty: int
    price: float
    ts: datetime = Field(index=True)
    charges: float = 0.0
    product: str


class PaperEquitySnapshotRow(SQLModel, table=True):
    """Periodic equity/cash snapshots (typically one per day) used for the
    equity curve and day-start-equity risk basis."""

    __tablename__ = "paper_equity"
    __table_args__ = (UniqueConstraint("strategy_id", "ts", name="uq_paper_equity_strategy_ts"),)

    id: int | None = Field(default=None, primary_key=True)
    strategy_id: str = Field(index=True)
    ts: datetime = Field(index=True)
    equity: float
    cash: float


# --------------------------------------------------------------------------
# Row <-> domain-model conversion (lossless)
# --------------------------------------------------------------------------


def _row_to_order(row: PaperOrderRow) -> Order:
    return Order(
        client_order_id=row.client_order_id,
        broker_order_id=row.broker_order_id,
        symbol=row.symbol,
        exchange=row.exchange,
        side=Side(row.side),
        qty=row.qty,
        filled_qty=row.filled_qty,
        order_type=OrderType(row.order_type),
        product=Product(row.product),
        limit_price=row.limit_price,
        trigger_price=row.trigger_price,
        status=OrderStatus(row.status),
        status_message=row.status_message,
        strategy_id=row.strategy_id,
        tag=row.tag,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _row_to_fill(row: PaperFillRow) -> Fill:
    return Fill(
        client_order_id=row.client_order_id,
        symbol=row.symbol,
        side=Side(row.side),
        qty=row.qty,
        price=row.price,
        ts=row.ts,
        charges=row.charges,
        product=Product(row.product),
    )


class PaperStore:
    """Facade bound to one ``strategy_id``. All reads/writes are filtered to
    it, so two stores on the same DB file never see each other's rows."""

    def __init__(self, db_path: Path, strategy_id: str) -> None:
        self.db_path = Path(db_path)
        self.strategy_id = strategy_id

    # -- run row ----------------------------------------------------------

    def ensure_run(self, capital: float, config_hash: str = "") -> PaperRunRow:
        """Get-or-create the run row for this strategy. If a run already
        exists with a different capital, log a WARNING and keep the stored
        value (the first `ensure_run` call for a strategy is authoritative)."""
        with paper_db_session(self.db_path) as session:
            row = session.exec(
                select(PaperRunRow).where(PaperRunRow.strategy_id == self.strategy_id)
            ).first()
            if row is None:
                row = PaperRunRow(
                    strategy_id=self.strategy_id,
                    config_hash=config_hash,
                    capital=capital,
                    created_at=now_ist(),
                )
                session.add(row)
                session.flush()  # assign the pk without ending the transaction
            elif row.capital != capital:
                logger.warning(
                    "paper run %r already exists with capital=%.2f; ignoring requested "
                    "capital=%.2f",
                    self.strategy_id,
                    row.capital,
                    capital,
                )
            session.expunge(row)  # detach a fully-loaded copy usable after close()
            return row

    def capital(self) -> float | None:
        """Stored capital for this strategy's run row, or None if no run yet."""
        with paper_db_session(self.db_path) as session:
            row = session.exec(
                select(PaperRunRow).where(PaperRunRow.strategy_id == self.strategy_id)
            ).first()
            return row.capital if row is not None else None

    # -- orders -------------------------------------------------------------

    def _upsert_order_row(
        self, session: Session, order: Order, planned_for: date | None
    ) -> None:
        row = session.exec(
            select(PaperOrderRow).where(
                PaperOrderRow.client_order_id == order.client_order_id,
                PaperOrderRow.strategy_id == self.strategy_id,
            )
        ).first()
        if row is None:
            row = PaperOrderRow(
                client_order_id=order.client_order_id,
                strategy_id=self.strategy_id,
                planned_for=planned_for,
            )
        elif planned_for is not None:
            row.planned_for = planned_for
        # else: keep row.planned_for as-is (preserve on re-save with no arg)

        row.broker_order_id = order.broker_order_id
        row.symbol = order.symbol
        row.exchange = order.exchange
        row.side = order.side.value
        row.qty = order.qty
        row.filled_qty = order.filled_qty
        row.order_type = order.order_type.value
        row.product = order.product.value
        row.limit_price = order.limit_price
        row.trigger_price = order.trigger_price
        row.status = order.status.value
        row.status_message = order.status_message
        row.tag = order.tag
        row.created_at = order.created_at
        row.updated_at = order.updated_at
        session.add(row)

    def save_order(self, order: Order, planned_for: date | None = None) -> None:
        """Upsert by ``client_order_id``. When ``planned_for`` is None the
        existing row's ``planned_for`` is preserved (an order placed from the
        planned queue keeps its queue date); every other field is overwritten
        from ``order``."""
        with paper_db_session(self.db_path) as session:
            self._upsert_order_row(session, order, planned_for)

    def get_order(self, client_order_id: str) -> Order | None:
        with paper_db_session(self.db_path) as session:
            row = session.exec(
                select(PaperOrderRow).where(
                    PaperOrderRow.client_order_id == client_order_id,
                    PaperOrderRow.strategy_id == self.strategy_id,
                )
            ).first()
            return _row_to_order(row) if row is not None else None

    def orders(self, day: date | None = None, status: OrderStatus | None = None) -> list[Order]:
        """Orders for this strategy, optionally filtered to a ``created_at``
        day and/or status, ordered by created_at then id."""
        with paper_db_session(self.db_path) as session:
            stmt = select(PaperOrderRow).where(PaperOrderRow.strategy_id == self.strategy_id)
            if status is not None:
                stmt = stmt.where(PaperOrderRow.status == status.value)
            if day is not None:
                start, end = _day_bounds(day)
                stmt = stmt.where(
                    PaperOrderRow.created_at >= start, PaperOrderRow.created_at < end
                )
            stmt = stmt.order_by(PaperOrderRow.created_at, PaperOrderRow.id)
            rows = session.exec(stmt).all()
            return [_row_to_order(r) for r in rows]

    def planned_orders(self, day: date, *, include_dry_placed: bool = False) -> list[Order]:
        """PENDING orders queued for the next-open on ``day``, ordered by id.

        ``include_dry_placed``: also return non-terminal queue rows that a
        DRY-RUN live session already "placed" (journalled OPEN/PARTIAL with a
        synthetic ``DRY-*`` broker_order_id). Nothing exists at the real
        broker for those, so a real (non-dry-run) live session must still see
        them as due for placement -- otherwise a morning dry-run rehearsal
        would consume the planned queue and the real session would silently
        place nothing."""
        working_dry = {OrderStatus.OPEN.value, OrderStatus.PARTIAL.value}
        with paper_db_session(self.db_path) as session:
            stmt = (
                select(PaperOrderRow)
                .where(
                    PaperOrderRow.strategy_id == self.strategy_id,
                    PaperOrderRow.planned_for == day,
                )
                .order_by(PaperOrderRow.id)
            )
            rows = session.exec(stmt).all()
            out: list[Order] = []
            for r in rows:
                if r.status == OrderStatus.PENDING.value:
                    out.append(_row_to_order(r))
                elif (
                    include_dry_placed
                    and r.status in working_dry
                    and (r.broker_order_id or "").startswith(DRY_ORDER_ID_PREFIX)
                ):
                    out.append(_row_to_order(r))
            return out

    def orders_placed_count(self, day: date) -> int:
        """Count of orders whose created_at falls on ``day`` AND whose status
        is not PENDING (planned-but-not-yet-placed orders are excluded).
        Counted SQL-side — this runs inside every pre-trade risk check."""
        start, end = _day_bounds(day)
        with paper_db_session(self.db_path) as session:
            stmt = (
                select(func.count())
                .select_from(PaperOrderRow)
                .where(
                    PaperOrderRow.strategy_id == self.strategy_id,
                    PaperOrderRow.created_at >= start,  # NULL created_at never matches
                    PaperOrderRow.created_at < end,
                    PaperOrderRow.status != OrderStatus.PENDING.value,
                )
            )
            return int(session.exec(stmt).one())

    # -- fills ----------------------------------------------------------

    def _fill_row(self, fill: Fill) -> PaperFillRow:
        return PaperFillRow(
            strategy_id=self.strategy_id,
            client_order_id=fill.client_order_id,
            symbol=fill.symbol,
            side=fill.side.value,
            qty=fill.qty,
            price=fill.price,
            ts=fill.ts,
            charges=fill.charges,
            product=fill.product.value,
        )

    def record_fill(self, fill: Fill) -> None:
        with paper_db_session(self.db_path) as session:
            session.add(self._fill_row(fill))

    def record_fill_and_order(self, fill: Fill, order: Order) -> None:
        """Persist a fill and its order's post-fill state in ONE transaction.

        The fill log is the restart-replay source, so a fill must never be
        committed while its order is still stored OPEN: a crash in that window
        would replay the fill into the ledger AND reload the order as working,
        which double-fills on the next tick. Committing both rows atomically
        closes that window.
        """
        with paper_db_session(self.db_path) as session:
            session.add(self._fill_row(fill))
            self._upsert_order_row(session, order, None)

    def fills(self, day: date | None = None) -> list[Fill]:
        with paper_db_session(self.db_path) as session:
            stmt = (
                select(PaperFillRow)
                .where(PaperFillRow.strategy_id == self.strategy_id)
                .order_by(PaperFillRow.ts, PaperFillRow.id)
            )
            if day is not None:
                start, end = _day_bounds(day)
                stmt = stmt.where(PaperFillRow.ts >= start, PaperFillRow.ts < end)
            rows = session.exec(stmt).all()
            return [_row_to_fill(r) for r in rows]

    def all_fills(self) -> list[Fill]:
        """All fills for this strategy, ordered by ts, id — the replay
        source for restart-safe Ledger reconstruction."""
        return self.fills(day=None)

    # -- equity curve -----------------------------------------------------

    def snapshot_equity(self, ts: datetime, equity: float, cash: float) -> None:
        """Upsert an equity/cash snapshot keyed on (strategy_id, ts)."""
        with paper_db_session(self.db_path) as session:
            row = session.exec(
                select(PaperEquitySnapshotRow).where(
                    PaperEquitySnapshotRow.strategy_id == self.strategy_id,
                    PaperEquitySnapshotRow.ts == ts,
                )
            ).first()
            if row is None:
                row = PaperEquitySnapshotRow(
                    strategy_id=self.strategy_id, ts=ts, equity=equity, cash=cash
                )
            else:
                row.equity = equity
                row.cash = cash
            session.add(row)

    def _curve(self, field: str) -> pd.Series:
        with paper_db_session(self.db_path) as session:
            stmt = (
                select(PaperEquitySnapshotRow)
                .where(PaperEquitySnapshotRow.strategy_id == self.strategy_id)
                .order_by(PaperEquitySnapshotRow.ts)
            )
            rows = session.exec(stmt).all()
            ts_list = [r.ts for r in rows]
            data = [getattr(r, field) for r in rows]
        index = pd.DatetimeIndex(ts_list, name="ts")
        return pd.Series(data, index=index, name=field, dtype=float)

    def equity_curve(self) -> pd.Series:
        """Float Series named 'equity', sorted DatetimeIndex named 'ts'.
        Empty Series (dtype float) if no snapshots."""
        return self._curve("equity")

    def cash_curve(self) -> pd.Series:
        """Same shape as `equity_curve`, name 'cash'."""
        return self._curve("cash")

    def day_start_equity(self, day: date) -> float | None:
        """Fallback chain: earliest snapshot ON `day` -> latest snapshot
        BEFORE `day` -> stored run capital -> None. Both lookups are
        SQL-side (ORDER BY + LIMIT 1) — this runs inside every pre-trade
        risk check."""
        start, end = _day_bounds(day)
        with paper_db_session(self.db_path) as session:
            on_day = session.exec(
                select(PaperEquitySnapshotRow)
                .where(
                    PaperEquitySnapshotRow.strategy_id == self.strategy_id,
                    PaperEquitySnapshotRow.ts >= start,
                    PaperEquitySnapshotRow.ts < end,
                )
                .order_by(PaperEquitySnapshotRow.ts)  # earliest ON day
                .limit(1)
            ).first()
            if on_day is not None:
                return on_day.equity
            before = session.exec(
                select(PaperEquitySnapshotRow)
                .where(
                    PaperEquitySnapshotRow.strategy_id == self.strategy_id,
                    PaperEquitySnapshotRow.ts < start,
                )
                .order_by(PaperEquitySnapshotRow.ts.desc())  # latest BEFORE day  # type: ignore[attr-defined]
                .limit(1)
            ).first()
            if before is not None:
                return before.equity
        return self.capital()

    # -- lifecycle ----------------------------------------------------------

    def reset(self) -> None:
        """Delete all rows for this strategy_id across all four tables."""
        with paper_db_session(self.db_path) as session:
            for model in (PaperOrderRow, PaperFillRow, PaperEquitySnapshotRow, PaperRunRow):
                rows = session.exec(select(model).where(model.strategy_id == self.strategy_id)).all()
                for r in rows:
                    session.delete(r)


__all__ = [
    "DRY_ORDER_ID_PREFIX",
    "paper_engine",
    "paper_db_session",
    "PaperRunRow",
    "PaperOrderRow",
    "PaperFillRow",
    "PaperEquitySnapshotRow",
    "PaperStore",
]

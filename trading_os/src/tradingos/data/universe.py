"""Point-in-time index universe — the survivorship-bias defense (spec 1c).

Backtests must pick constituents *as of each historical date*, never today's
index list. This module owns the membership table and the
``PITUniverseResolver`` that the engine uses through the ``UniverseResolver``
protocol. When point-in-time data is missing the resolver falls back to all
available symbols but emits a LOUD warning (logged and surfaced via
``warnings``): a run without PIT data overstates performance and must say so.

Seed the membership table from NSE / niftyindices historical constituent-change
announcements (they publish inclusion/exclusion dates); ``import_membership_csv``
loads those as ``index_name,symbol,start_date,end_date`` rows.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import pandas as pd
from sqlalchemy import or_
from sqlmodel import Field, SQLModel, col, select

from tradingos.config.schemas import UniverseSpec
from tradingos.config.settings import Settings
from tradingos.core.errors import DataError
from tradingos.core.logging import get_logger
from tradingos.core.timeutils import now_ist
from tradingos.data.actions import STOP_ACTIONS, CorporateAction
from tradingos.data.meta import meta_session
from tradingos.engine.dataview import MarketData

logger = get_logger(__name__)


class UniverseMembership(SQLModel, table=True):
    """One membership spell of ``symbol`` in ``index_name``.

    ``start_date`` and ``end_date`` are inclusive; ``end_date is None`` means the
    symbol is still a member.
    """

    id: int | None = Field(default=None, primary_key=True)
    index_name: str = Field(index=True)
    symbol: str = Field(index=True)
    start_date: date
    end_date: date | None = None


# --------------------------------------------------------------------------- #
# CSV import
# --------------------------------------------------------------------------- #
def _parse_date(value: str, *, row: int, field: str) -> date:
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise DataError(f"row {row}: bad {field} {value!r} (expected YYYY-MM-DD)") from exc


def import_membership_csv(path: Path | str, settings: Settings) -> int:
    """Import point-in-time membership rows, returning the count newly inserted.

    Columns: ``index_name,symbol,start_date,end_date`` (empty ``end_date`` means
    the spell is still open). Validates dates, requires ``start_date <=
    end_date`` when both are present, and skips exact duplicates (idempotent).
    """
    p = Path(path)
    if not p.exists():
        raise DataError(f"CSV not found: {p}")
    with p.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        header = set(reader.fieldnames or [])
        required = {"index_name", "symbol", "start_date", "end_date"}
        missing = required - header
        if missing:
            raise DataError(f"{p.name}: missing required columns {sorted(missing)}")
        rows = list(reader)

    inserted = 0
    with meta_session(settings.meta_db_path) as session:
        seen = {
            (m.index_name, m.symbol, m.start_date, m.end_date)
            for m in session.exec(select(UniverseMembership)).all()
        }
        for i, row in enumerate(rows, start=2):  # line 1 is the header
            index_name = (row.get("index_name") or "").strip()
            symbol = (row.get("symbol") or "").strip()
            if not index_name or not symbol:
                raise DataError(f"row {i}: empty index_name or symbol")
            start_date = _parse_date(row.get("start_date", ""), row=i, field="start_date")
            end_raw = (row.get("end_date") or "").strip()
            end_date = _parse_date(end_raw, row=i, field="end_date") if end_raw else None
            if end_date is not None and end_date < start_date:
                raise DataError(f"row {i}: end_date {end_date} before start_date {start_date}")
            key = (index_name, symbol, start_date, end_date)
            if key in seen:
                continue
            session.add(
                UniverseMembership(
                    index_name=index_name,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                )
            )
            seen.add(key)
            inserted += 1
        session.commit()
    logger.info("imported %d membership row(s) from %s", inserted, p)
    return inserted


# --------------------------------------------------------------------------- #
# Queries
# --------------------------------------------------------------------------- #
def members_as_of(index_name: str, on: date, settings: Settings) -> list[str]:
    """Symbols in ``index_name`` on date ``on`` (start/end dates inclusive)."""
    with meta_session(settings.meta_db_path) as session:
        stmt = select(UniverseMembership.symbol).where(  # type: ignore[call-overload]
            UniverseMembership.index_name == index_name,
            UniverseMembership.start_date <= on,
            or_(col(UniverseMembership.end_date).is_(None), UniverseMembership.end_date >= on),
        )
        return sorted(set(session.exec(stmt).all()))


def membership_coverage(index_name: str, settings: Settings) -> tuple[date, date] | None:
    """``(earliest start, latest known date)`` for ``index_name``, or None.

    The upper bound is the latest explicit date in the table, extended to today
    when any spell is still open (those members are current, so coverage reaches
    the present). Used to warn when a run date falls outside PIT coverage.
    """
    with meta_session(settings.meta_db_path) as session:
        rows = session.exec(
            select(UniverseMembership).where(UniverseMembership.index_name == index_name)
        ).all()
    if not rows:
        return None
    lower = min(r.start_date for r in rows)
    known: list[date] = [r.start_date for r in rows]
    known += [r.end_date for r in rows if r.end_date is not None]
    upper = max(known)
    if any(r.end_date is None for r in rows):
        upper = max(upper, now_ist().date())
    return (lower, upper)


def delisting_date(symbol: str, settings: Settings) -> date | None:
    """Earliest delisting/suspension ex-date for ``symbol``, or None if active."""
    with meta_session(settings.meta_db_path) as session:
        stmt = select(CorporateAction.ex_date).where(  # type: ignore[call-overload]
            CorporateAction.symbol == symbol,
            col(CorporateAction.action_type).in_(sorted(STOP_ACTIONS)),
        )
        dates = list(session.exec(stmt).all())
    return min(dates) if dates else None


# --------------------------------------------------------------------------- #
# Resolver
# --------------------------------------------------------------------------- #
class PITUniverseResolver:
    """Point-in-time ``UniverseResolver`` backed by the membership table.

    ``resolve`` order: explicit ``spec.symbols`` override PIT membership;
    otherwise resolve point-in-time members (loudly warning and falling back to
    all data symbols when membership data is absent or the date is outside
    coverage); drop symbols already delisted/suspended as of ``on``; intersect
    with symbols that actually have price data (warning on ANY drop); then
    apply the liquidity filter using ONLY bars dated on/before ``on``.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._warnings: list[str] = []
        # Per-resolver caches: resolve() runs once per rebalance date, and
        # coverage/delisting facts never change within one backtest.
        self._coverage_cache: dict[str, tuple[date, date] | None] = {}
        self._delisting_cache: dict[str, date | None] = {}

    @property
    def warnings(self) -> list[str]:
        return self._warnings

    def _warn(self, msg: str) -> None:
        if msg not in self._warnings:
            self._warnings.append(msg)
            logger.warning(msg)

    def resolve(self, spec: UniverseSpec, on: date, data: MarketData) -> list[str]:
        # (1) explicit symbol list overrides point-in-time membership.
        if spec.symbols is not None:
            candidates: list[str] = list(spec.symbols)
        elif spec.point_in_time:
            candidates = self._resolve_pit(spec, on, data)
        else:
            candidates = list(data.symbols)

        # (2) a symbol delisted/suspended on or before `on` cannot be entered
        # — its membership spell may lag reality, so honor the corporate-action
        # record directly. This drop is CORRECT behavior (not a bias), so it is
        # logged, not appended to `warnings`.
        candidates, dropped_delisted = self._drop_delisted(candidates, on)
        if dropped_delisted:
            logger.info(
                "universe %r as of %s: dropped %d delisted/suspended symbol(s): %s",
                spec.index,
                on,
                len(dropped_delisted),
                ", ".join(dropped_delisted),
            )

        # (3) can't trade what we have no data for. ANY drop here means the
        # tradable universe differs from the true point-in-time universe, so
        # warn loudly with counts however small the gap (hard rule 4).
        data_symbols = set(data.symbols)
        n_before = len(candidates)
        missing = sorted(s for s in candidates if s not in data_symbols)
        candidates = [s for s in candidates if s in data_symbols]
        if missing:
            shown = ", ".join(missing[:8]) + ("..." if len(missing) > 8 else "")
            self._warn(
                f"DATA COVERAGE: {len(missing)}/{n_before} universe candidate(s) for index "
                f"{spec.index!r} have no price data (kept {len(candidates)}; missing: {shown}); "
                "results may be unrepresentative of the true point-in-time universe"
            )

        # (4) liquidity filter — look-ahead-safe.
        if spec.min_median_traded_value is not None:
            candidates = self._liquidity_filter(candidates, spec, on, data)

        return sorted(set(candidates))

    def _drop_delisted(self, candidates: list[str], on: date) -> tuple[list[str], list[str]]:
        """Split ``candidates`` into (still listed as of ``on``, delisted).

        Point-in-time safe: a delisting/suspension dated AFTER ``on`` must not
        affect earlier dates, so the comparison is against ``on`` per call while
        the (immutable) delisting date itself is cached per symbol.
        """
        kept: list[str] = []
        dropped: list[str] = []
        for sym in candidates:
            if sym not in self._delisting_cache:
                self._delisting_cache[sym] = delisting_date(sym, self._settings)
            d = self._delisting_cache[sym]
            if d is not None and d <= on:
                dropped.append(sym)
            else:
                kept.append(sym)
        return kept, dropped

    def _resolve_pit(self, spec: UniverseSpec, on: date, data: MarketData) -> list[str]:
        if spec.index not in self._coverage_cache:
            self._coverage_cache[spec.index] = membership_coverage(spec.index, self._settings)
        coverage = self._coverage_cache[spec.index]
        if coverage is None:
            self._warn(
                f"SURVIVORSHIP BIAS: no point-in-time membership data for index "
                f"{spec.index}; falling back to all available symbols — results "
                "overstate performance"
            )
            return list(data.symbols)
        lower, upper = coverage
        if on < lower or on > upper:
            self._warn(
                f"SURVIVORSHIP BIAS: point-in-time membership for index {spec.index} "
                f"covers {lower}..{upper} but run date {on} is outside coverage — "
                "partial data; results may carry survivorship bias"
            )
        return members_as_of(spec.index, on, self._settings)

    def _liquidity_filter(
        self, candidates: list[str], spec: UniverseSpec, on: date, data: MarketData
    ) -> list[str]:
        """Keep symbols whose median close*volume over the last
        ``liquidity_lookback_days`` bars dated on/before ``on`` meets the
        threshold. STRICTLY no bar after ``on`` may influence the result: we
        slice by date first, then take the trailing window."""
        on_ts = pd.Timestamp(on)
        lookback = spec.liquidity_lookback_days
        threshold = spec.min_median_traded_value
        assert threshold is not None
        kept: list[str] = []
        for sym in candidates:
            try:
                df = data.full_frame(sym)
            except DataError:
                continue
            past = df[df.index.normalize() <= on_ts]  # date-first slice (no look-ahead)
            if past.empty:
                continue  # no bars as of `on` -> not tradeable, drop
            window = past.tail(lookback)
            traded_value = (window["close"] * window["volume"]).median()
            if pd.notna(traded_value) and traded_value >= threshold:
                kept.append(sym)
        return kept

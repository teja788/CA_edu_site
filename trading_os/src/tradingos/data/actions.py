"""Corporate actions, dividends, and back-adjustment of raw OHLCV.

Raw market data is immutable (CLAUDE.md hard rule 8); *adjusted* data is stored
separately and derived from raw via the functions here. Kite serves candles
adjusted **as of fetch time**, which does NOT make stored raw data adjusted:
in an append-only store, rows fetched before an action keep the old price
scale forever, so after any split/bonus the raw series is mixed-scale until
``build_adjusted`` rebuilds the adjusted set from recorded actions (see
docs/assumptions.md). ``validate_adjustments`` is the review queue that flags
unexplained overnight jumps (spec 1b); the ``data adjust`` CLI runs it over
every freshly rebuilt adjusted series, so a jump that survives adjustment
(= a missing/incorrect corporate action) is surfaced immediately.

Ratio / factor conventions (READ THIS before touching the math)
---------------------------------------------------------------
Every price-affecting action carries a ``price_factor``: the divisor applied to
prices of bars *strictly before* its ex-date (back-adjustment), and the
multiplier applied to their volumes.

* **split** — ``ratio_num:ratio_den = old_face:new_face``. A 10 -> 2 face-value
  split is ``ratio_num=10, ratio_den=2``: one old share becomes ``10/2 = 5``
  shares, so pre-ex prices are divided by ``price_factor = ratio_num/ratio_den =
  5``.
* **bonus** — ``A:B`` means *A new shares for every B held*, stored
  ``ratio_num=A, ratio_den=B``. One share becomes ``(A+B)/B`` shares, so
  pre-ex prices are divided by ``price_factor = (ratio_num+ratio_den)/ratio_den``
  (a 1:1 bonus -> divisor 2).
* **symbol_change / delisting / suspension** — not price events;
  ``price_factor == 1.0``.

Back-adjustment is anchored to the *latest* regime: bars on/after the most
recent ex-date have cumulative factor 1.0, so the adjusted series equals raw
for the most recent price regime and only history is rescaled. Factors from
multiple actions compound (a split then a bonus multiply).

Total-return close (``total_return_close``) adds dividends back by chain-linking
gross returns ``(close_t + div_t)/close_{t-1}`` from the series start; momentum
ranking should use this where dividend data exists (spec 1b).
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import date, datetime, time
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

import pandas as pd
import polars as pl
from sqlmodel import Field, SQLModel, select

from tradingos.config.settings import Settings
from tradingos.core.errors import DataError
from tradingos.core.logging import get_logger
from tradingos.core.models import Timeframe
from tradingos.core.timeutils import now_ist
from tradingos.data.meta import meta_session

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids importing store eagerly
    from tradingos.data.store import BarStore

logger = get_logger(__name__)

# Action types that change the number of shares outstanding (and thus prices).
PRICE_ACTIONS: frozenset[str] = frozenset({"split", "bonus"})
# All recognised corporate-action types.
ACTION_TYPES: frozenset[str] = frozenset(
    {"split", "bonus", "symbol_change", "delisting", "suspension"}
)
# Actions that mark a symbol as no longer tradeable.
STOP_ACTIONS: frozenset[str] = frozenset({"delisting", "suspension"})


# --------------------------------------------------------------------------- #
# Tables
# --------------------------------------------------------------------------- #
class CorporateAction(SQLModel, table=True):
    """A split / bonus / symbol change / delisting / suspension for one symbol.

    ``ratio_num`` / ``ratio_den`` carry the split or bonus ratio (see module
    docstring); ``new_symbol`` is the post-change tradingsymbol for a
    symbol_change. ``ex_date`` is the first date the action is in effect.
    """

    id: int | None = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    ex_date: date
    action_type: str
    ratio_num: float | None = None
    ratio_den: float | None = None
    new_symbol: str | None = None
    note: str = ""

    @property
    def price_factor(self) -> float:
        """Divisor applied to pre-ex-date prices (and multiplier for volumes)."""
        if self.action_type == "split":
            if not self.ratio_num or not self.ratio_den:
                raise DataError(f"split action for {self.symbol} missing ratio_num/ratio_den")
            return self.ratio_num / self.ratio_den
        if self.action_type == "bonus":
            if not self.ratio_num or not self.ratio_den:
                raise DataError(f"bonus action for {self.symbol} missing ratio_num/ratio_den")
            return (self.ratio_num + self.ratio_den) / self.ratio_den
        return 1.0


class Dividend(SQLModel, table=True):
    """A cash dividend, per share, in rupees, on its ex-date."""

    id: int | None = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    ex_date: date
    amount: float  # per share, rupees


class SharesOutstanding(SQLModel, table=True):
    """A CURRENT shares-outstanding snapshot for one symbol.

    NOT a point-in-time share count: ``as_of`` records when the snapshot was
    taken (from a filing / data vendor), and one-or-more rows may exist per
    symbol (distinct ``as_of`` dates form a coarse history; the latest ``as_of``
    is the one consumers use). Historical market cap is reconstructed as
    ``latest_snapshot_shares × adjusted close(t)`` — correct through
    splits/bonuses because the store's Kite prices are back-adjusted (a split
    multiplies shares and divides adjusted price by the same factor, so they
    cancel), with residual error only from genuine issuance drift (QIPs,
    buybacks, ESOPs, rights) between snapshot dates. Intended for decile /
    quantile screens, not exact-value logic. See docs/assumptions.md.
    """

    id: int | None = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    as_of: date
    shares: int  # total shares outstanding (count), must be > 0
    source: str = ""


# --------------------------------------------------------------------------- #
# CSV import (validation + clear errors + idempotency)
# --------------------------------------------------------------------------- #
def _parse_date(value: str, *, row: int, field: str) -> date:
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise DataError(f"row {row}: bad {field} {value!r} (expected YYYY-MM-DD)") from exc


def _parse_float(value: str, *, row: int, field: str) -> float:
    try:
        return float(value.strip())
    except ValueError as exc:
        raise DataError(f"row {row}: bad {field} {value!r} (expected a number)") from exc


def _read_rows(path: Path | str, required: set[str]) -> list[dict[str, str]]:
    p = Path(path)
    if not p.exists():
        raise DataError(f"CSV not found: {p}")
    with p.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        header = set(reader.fieldnames or [])
        missing = required - header
        if missing:
            raise DataError(f"{p.name}: missing required columns {sorted(missing)}")
        return list(reader)


def _action_signature(a: CorporateAction) -> tuple:
    return (a.symbol, a.ex_date, a.action_type, a.ratio_num, a.ratio_den, a.new_symbol, a.note)


def _build_action(row: dict[str, str], *, line: int) -> CorporateAction:
    symbol = (row.get("symbol") or "").strip()
    if not symbol:
        raise DataError(f"row {line}: empty symbol")
    action_type = (row.get("action_type") or "").strip()
    if action_type not in ACTION_TYPES:
        raise DataError(f"row {line}: unknown action_type {action_type!r} (expected {sorted(ACTION_TYPES)})")
    ex_date = _parse_date(row.get("ex_date", ""), row=line, field="ex_date")

    num_raw = (row.get("ratio_num") or "").strip()
    den_raw = (row.get("ratio_den") or "").strip()
    ratio_num = _parse_float(num_raw, row=line, field="ratio_num") if num_raw else None
    ratio_den = _parse_float(den_raw, row=line, field="ratio_den") if den_raw else None
    new_symbol = (row.get("new_symbol") or "").strip() or None
    note = (row.get("note") or "").strip()

    if action_type in PRICE_ACTIONS:
        if ratio_num is None or ratio_den is None:
            raise DataError(f"row {line}: {action_type} for {symbol} requires ratio_num and ratio_den")
        if ratio_num <= 0 or ratio_den <= 0:
            raise DataError(f"row {line}: {action_type} ratios must be > 0")
    if action_type == "symbol_change" and not new_symbol:
        raise DataError(f"row {line}: symbol_change for {symbol} requires new_symbol")

    return CorporateAction(
        symbol=symbol,
        ex_date=ex_date,
        action_type=action_type,
        ratio_num=ratio_num,
        ratio_den=ratio_den,
        new_symbol=new_symbol,
        note=note,
    )


def import_actions_csv(path: Path | str, settings: Settings) -> int:
    """Import corporate actions from a CSV, returning the count newly inserted.

    Columns: ``symbol,ex_date,action_type,ratio_num,ratio_den,new_symbol,note``
    (extra columns are ignored). Validates each row and skips exact duplicates,
    so re-importing the same file is a no-op (returns 0).
    """
    rows = _read_rows(path, required={"symbol", "ex_date", "action_type"})
    inserted = 0
    with meta_session(settings.meta_db_path) as session:
        seen = {_action_signature(a) for a in session.exec(select(CorporateAction)).all()}
        for i, row in enumerate(rows, start=2):  # line 1 is the header
            action = _build_action(row, line=i)
            sig = _action_signature(action)
            if sig in seen:
                continue
            session.add(action)
            seen.add(sig)
            inserted += 1
        session.commit()
    logger.info("imported %d corporate action(s) from %s", inserted, path)
    return inserted


def import_dividends_csv(path: Path | str, settings: Settings) -> int:
    """Import cash dividends from a CSV, returning the count newly inserted.

    Columns: ``symbol,ex_date,amount`` (per share, rupees). Validates rows and
    skips exact duplicates (idempotent).
    """
    rows = _read_rows(path, required={"symbol", "ex_date", "amount"})
    inserted = 0
    with meta_session(settings.meta_db_path) as session:
        seen = {
            (d.symbol, d.ex_date, d.amount)
            for d in session.exec(select(Dividend)).all()
        }
        for i, row in enumerate(rows, start=2):
            symbol = (row.get("symbol") or "").strip()
            if not symbol:
                raise DataError(f"row {i}: empty symbol")
            ex_date = _parse_date(row.get("ex_date", ""), row=i, field="ex_date")
            amount = _parse_float(row.get("amount", ""), row=i, field="amount")
            if amount <= 0:
                raise DataError(f"row {i}: dividend amount must be > 0")
            key = (symbol, ex_date, amount)
            if key in seen:
                continue
            session.add(Dividend(symbol=symbol, ex_date=ex_date, amount=amount))
            seen.add(key)
            inserted += 1
        session.commit()
    logger.info("imported %d dividend(s) from %s", inserted, path)
    return inserted


def import_shares_csv(path: Path | str, settings: Settings) -> dict[str, int]:
    """Import shares-outstanding snapshots from a CSV.

    Columns: ``symbol,shares,as_of,source``. Upsert semantics on the
    (symbol, as_of) key: an existing row for that pair is REPLACED (shares +
    source overwritten), while distinct ``as_of`` dates for a symbol are kept
    as separate rows (a coarse history). Rows that fail validation — empty
    symbol, unparseable ``as_of`` or ``shares``, or ``shares <= 0`` — are
    skipped (never abort the batch). Returns counts
    ``{"imported": n, "replaced": n, "skipped": n}``.

    Missing required columns is still a hard ``DataError`` (structural), matching
    the other importers.
    """
    rows = _read_rows(path, required={"symbol", "shares", "as_of"})
    imported = replaced = skipped = 0
    with meta_session(settings.meta_db_path) as session:
        existing: dict[tuple[str, date], SharesOutstanding] = {
            (r.symbol, r.as_of): r for r in session.exec(select(SharesOutstanding)).all()
        }
        for row in rows:
            symbol = (row.get("symbol") or "").strip()
            if not symbol:
                skipped += 1
                continue
            try:
                as_of = date.fromisoformat((row.get("as_of") or "").strip())
            except ValueError:
                skipped += 1
                continue
            try:
                shares = int((row.get("shares") or "").strip())
            except ValueError:
                skipped += 1
                continue
            if shares <= 0:
                skipped += 1
                continue
            source = (row.get("source") or "").strip()
            key = (symbol, as_of)
            found = existing.get(key)
            if found is not None:
                found.shares = shares
                found.source = source
                session.add(found)
                replaced += 1
            else:
                created = SharesOutstanding(
                    symbol=symbol, as_of=as_of, shares=shares, source=source
                )
                session.add(created)
                existing[key] = created
                imported += 1
        session.commit()
    counts = {"imported": imported, "replaced": replaced, "skipped": skipped}
    logger.info("imported shares from %s: %s", path, counts)
    return counts


# --------------------------------------------------------------------------- #
# Queries
# --------------------------------------------------------------------------- #
def get_actions(symbol: str, settings: Settings) -> list[CorporateAction]:
    """All corporate actions for ``symbol``, ordered by ex-date ascending."""
    with meta_session(settings.meta_db_path) as session:
        stmt = (
            select(CorporateAction)
            .where(CorporateAction.symbol == symbol)
            .order_by(CorporateAction.ex_date)  # type: ignore[arg-type]
        )
        return list(session.exec(stmt).all())


def get_dividends(symbol: str, settings: Settings) -> list[Dividend]:
    """All dividends for ``symbol``, ordered by ex-date ascending."""
    with meta_session(settings.meta_db_path) as session:
        stmt = (
            select(Dividend)
            .where(Dividend.symbol == symbol)
            .order_by(Dividend.ex_date)  # type: ignore[arg-type]
        )
        return list(session.exec(stmt).all())


def actions_signature(actions: list[CorporateAction]) -> str:
    """Order-independent 16-hex fingerprint of the PRICE-affecting actions.

    Only splits/bonuses enter the hash (symbol changes, delistings and
    suspensions never rescale bars). ``build_adjusted`` records this signature
    beside every adjusted series; the store compares it against the current
    corporate-actions table at read time to detect a STALE adjusted series
    (an action recorded after the last adjustment pass).
    """
    parts = sorted(
        json.dumps([a.ex_date.isoformat(), a.action_type, a.ratio_num, a.ratio_den])
        for a in actions
        if a.action_type in PRICE_ACTIONS
    )
    payload = "|".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def migrate_symbol_actions(old_symbol: str, new_symbol: str, settings: Settings) -> dict[str, int]:
    """Re-key corporate actions and dividends from ``old_symbol`` to
    ``new_symbol`` after a symbol rename (used by `platform data
    migrate-symbol`). Returns counts: ``{"actions": n, "dividends": n}``.
    """
    with meta_session(settings.meta_db_path) as session:
        actions = list(
            session.exec(select(CorporateAction).where(CorporateAction.symbol == old_symbol)).all()
        )
        for action in actions:
            action.symbol = new_symbol
            session.add(action)
        dividends = list(
            session.exec(select(Dividend).where(Dividend.symbol == old_symbol)).all()
        )
        for dividend in dividends:
            dividend.symbol = new_symbol
            session.add(dividend)
        session.commit()
    counts = {"actions": len(actions), "dividends": len(dividends)}
    logger.info("migrated meta rows %s -> %s: %s", old_symbol, new_symbol, counts)
    return counts


# --------------------------------------------------------------------------- #
# Back-adjustment
# --------------------------------------------------------------------------- #
def adjustment_factors(
    actions: list[CorporateAction], index: pd.DatetimeIndex
) -> pd.Series:
    """Cumulative back-adjustment divisor aligned to ``index``.

    A bar whose timestamp is *strictly before* an action's ex-date is divided by
    that action's ``price_factor``; factors from multiple actions compound. Bars
    on/after the latest ex-date keep factor 1.0 (adjusted == raw for the most
    recent regime). Returns a float Series indexed like ``index``.
    """
    factors = pd.Series(1.0, index=index, dtype="float64")
    for action in actions:
        pf = action.price_factor
        if pf == 1.0:
            continue
        # Strictly before the ex-date's midnight -> covers daily and intraday bars.
        mask = index < pd.Timestamp(action.ex_date)
        factors.loc[mask] *= pf
    return factors


def apply_adjustments(raw: pl.DataFrame, actions: list[CorporateAction]) -> pl.DataFrame:
    """Back-adjust a raw OHLCV polars frame. Pure function (no I/O).

    Divides open/high/low/close by the per-bar cumulative factor and *multiplies*
    volume by it (rounded to Int64); ``ts`` is untouched and column order is
    preserved. Bars on/after the latest ex-date are returned identical to raw.
    """
    if raw.is_empty():
        return raw

    factor_expr = pl.lit(1.0)
    for action in actions:
        pf = action.price_factor
        if pf == 1.0:
            continue
        cutoff = datetime.combine(action.ex_date, time())  # midnight of ex-date
        factor_expr = factor_expr * (
            pl.when(pl.col("ts") < pl.lit(cutoff)).then(pl.lit(pf)).otherwise(pl.lit(1.0))
        )

    out = raw.with_columns(factor_expr.alias("_factor"))
    out = out.with_columns(
        (pl.col("open") / pl.col("_factor")).alias("open"),
        (pl.col("high") / pl.col("_factor")).alias("high"),
        (pl.col("low") / pl.col("_factor")).alias("low"),
        (pl.col("close") / pl.col("_factor")).alias("close"),
        (pl.col("volume") * pl.col("_factor")).round(0).cast(pl.Int64).alias("volume"),
    )
    return out.drop("_factor")


def build_adjusted(
    symbol: str,
    timeframe: Timeframe,
    settings: Settings,
    store: BarStore | None = None,
) -> int:
    """Read raw bars, apply corporate-action adjustments, write the adjusted set.

    Returns the number of adjusted rows written. Alongside the bars, the
    signature of the price-affecting action set that was applied is recorded
    via ``store.write_adjustment_meta`` so reads can detect a stale adjusted
    series (a corporate action recorded after this pass). ``store`` is
    injected in tests; in production the ``BarStore`` is imported lazily to
    avoid a hard import dependency on a module built in parallel.
    """
    if store is None:  # pragma: no cover - exercised via injected fake in tests
        from tradingos.data.store import BarStore as _BarStore

        store = _BarStore(settings)
    raw = store.read_raw(symbol, timeframe)
    actions = get_actions(symbol, settings)
    adjusted = apply_adjustments(raw, actions)
    written = store.write_adjusted(symbol, timeframe, adjusted)
    store.write_adjustment_meta(
        symbol,
        timeframe,
        {
            "actions_sig": actions_signature(actions),
            "built_at": now_ist().isoformat(sep=" ", timespec="seconds"),
        },
    )
    return written


# --------------------------------------------------------------------------- #
# Total return
# --------------------------------------------------------------------------- #
def total_return_close(close: pd.Series, dividends: list[Dividend]) -> pd.Series:
    """Total-return close series (dividends reinvested), same index as ``close``.

    Standard chain-link: the series starts at ``close.iloc[0]`` and grows by the
    gross return ``(close_t + div_t)/close_{t-1}`` each bar, where ``div_t`` is
    the sum of dividends with ex-date on that bar's date (0 otherwise). Bars with
    no dividend reproduce the plain price return.
    """
    if close.empty:
        return close.copy()

    div_aligned = pd.Series(0.0, index=close.index, dtype="float64")
    bar_dates = close.index.normalize()
    for dv in dividends:
        div_aligned.loc[bar_dates == pd.Timestamp(dv.ex_date)] += dv.amount

    prev = close.shift(1)
    gross = (close + div_aligned) / prev
    gross.iloc[0] = 1.0  # no return on the first bar
    return close.iloc[0] * gross.cumprod()


# --------------------------------------------------------------------------- #
# Adjustment validation ("possibly unadjusted data" review queue)
# --------------------------------------------------------------------------- #
class AdjustmentFlag(NamedTuple):
    """One suspicious overnight gap for human review."""

    symbol: str
    date: date
    gap: float  # signed close-to-close return


def validate_adjustments(
    frames: dict[str, pd.DataFrame],
    actions_by_symbol: dict[str, list[CorporateAction]],
    *,
    market: pd.Series | None = None,
    gap_threshold: float = 0.40,
    market_move_threshold: float = 0.05,
) -> list[AdjustmentFlag]:
    """Flag overnight |close-to-close| moves that look like unadjusted data.

    A move on date *t* is flagged only when its magnitude exceeds
    ``gap_threshold`` AND it is (a) not explained by a recorded corporate action
    with that ex-date, and (b) not market-wide (skipped when a ``market`` series
    is given and ``|market return| > market_move_threshold`` on *t*). This is the
    review queue required by spec 1b — flags are advisory, not automatic edits.
    """
    market_by_date: dict[date, float] = {}
    if market is not None:
        mret = market.pct_change()
        for ts, value in mret.items():
            if pd.notna(value):
                market_by_date[pd.Timestamp(ts).date()] = float(value)

    flags: list[AdjustmentFlag] = []
    for symbol in sorted(frames):
        close = frames[symbol]["close"]
        rets = close.pct_change()
        action_dates = {a.ex_date for a in actions_by_symbol.get(symbol, [])}
        for ts, r in rets.items():
            if pd.isna(r) or abs(r) <= gap_threshold:
                continue
            d = pd.Timestamp(ts).date()
            if d in action_dates:
                continue  # explained by a recorded corporate action
            mret_d = market_by_date.get(d)
            if mret_d is not None and abs(mret_d) > market_move_threshold:
                continue  # market-wide move, not symbol-specific
            flags.append(AdjustmentFlag(symbol=symbol, date=d, gap=float(r)))
    return flags

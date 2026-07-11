"""Instrument master + symbol-mapping tables.

`Instrument` mirrors Kite's instruments dump (NSE cash-equity subset only).
`SymbolChange` is the symbol-mapping table: whenever a previously-seen
instrument_token reappears under a different tradingsymbol, we record the
rename here instead of silently losing the old symbol's history.
"""

from __future__ import annotations

from datetime import date

from sqlmodel import Field, SQLModel, select

from tradingos.config.settings import Settings
from tradingos.core.errors import DataError
from tradingos.core.logging import get_logger
from tradingos.core.timeutils import now_ist
from tradingos.data.meta import meta_session

logger = get_logger(__name__)


class Instrument(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    instrument_token: int = Field(index=True, unique=True)
    tradingsymbol: str = Field(index=True)
    name: str | None = None
    exchange: str
    segment: str
    instrument_type: str
    lot_size: int
    tick_size: float
    first_seen: date
    last_seen: date


class SymbolChange(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    instrument_token: int
    old_symbol: str
    new_symbol: str
    detected_on: date


def sync_instruments(kite: object, settings: Settings) -> dict[str, int]:
    """Fetch the NSE instruments dump, keep cash equities (segment NSE,
    instrument_type EQ), and upsert into the Instrument table by
    instrument_token. When a stored token's tradingsymbol has changed since
    the last sync, record a SymbolChange row and update the instrument.

    Returns a summary dict: fetched / added / updated / symbol_changes counts.
    """
    raw = kite.instruments("NSE")
    equities = [
        row for row in raw if row.get("segment") == "NSE" and row.get("instrument_type") == "EQ"
    ]
    today = now_ist().date()
    added = 0
    updated = 0
    symbol_changes = 0

    with meta_session(settings.meta_db_path) as session:
        for row in equities:
            token = int(row["instrument_token"])
            symbol = row["tradingsymbol"]
            existing = session.exec(
                select(Instrument).where(Instrument.instrument_token == token)
            ).first()

            if existing is None:
                session.add(
                    Instrument(
                        instrument_token=token,
                        tradingsymbol=symbol,
                        name=row.get("name") or None,
                        exchange=row.get("exchange", "NSE"),
                        segment=row.get("segment", "NSE"),
                        instrument_type=row.get("instrument_type", "EQ"),
                        lot_size=int(row.get("lot_size") or 1),
                        tick_size=float(row.get("tick_size") or 0.05),
                        first_seen=today,
                        last_seen=today,
                    )
                )
                added += 1
                continue

            if existing.tradingsymbol != symbol:
                session.add(
                    SymbolChange(
                        instrument_token=token,
                        old_symbol=existing.tradingsymbol,
                        new_symbol=symbol,
                        detected_on=today,
                    )
                )
                existing.tradingsymbol = symbol
                symbol_changes += 1

            existing.name = row.get("name") or existing.name
            existing.exchange = row.get("exchange") or existing.exchange
            existing.segment = row.get("segment") or existing.segment
            existing.instrument_type = row.get("instrument_type") or existing.instrument_type
            existing.lot_size = int(row.get("lot_size") or existing.lot_size)
            existing.tick_size = float(row.get("tick_size") or existing.tick_size)
            existing.last_seen = today
            session.add(existing)
            updated += 1

        session.commit()

    summary = {
        "fetched": len(equities),
        "added": added,
        "updated": updated,
        "symbol_changes": symbol_changes,
    }
    logger.info("instrument sync: %s", summary)
    return summary


def token_for(symbol: str, settings: Settings) -> int:
    """Instrument token for the current tradingsymbol. Raises DataError if unknown.

    NSE reuses tradingsymbols: a delisted company's symbol can be reassigned
    to a new listing, leaving multiple Instrument rows with the same
    tradingsymbol. Resolution is deterministic and prefers the ACTIVE /
    most-recent listing: greatest last_seen wins (a delisted instrument stops
    appearing in the dump, so its last_seen stops advancing), then greatest
    first_seen, then greatest id as the final tiebreak.
    """
    with meta_session(settings.meta_db_path) as session:
        inst = session.exec(
            select(Instrument)
            .where(Instrument.tradingsymbol == symbol)
            .order_by(
                Instrument.last_seen.desc(),  # type: ignore[attr-defined]
                Instrument.first_seen.desc(),  # type: ignore[attr-defined]
                Instrument.id.desc(),  # type: ignore[union-attr]
            )
        ).first()
        if inst is None:
            raise DataError(f"unknown instrument symbol: {symbol}")
        return inst.instrument_token


def current_symbol_for(token: int, settings: Settings) -> str:
    """Current tradingsymbol for an instrument token. Raises DataError if unknown."""
    with meta_session(settings.meta_db_path) as session:
        inst = session.exec(select(Instrument).where(Instrument.instrument_token == token)).first()
        if inst is None:
            raise DataError(f"unknown instrument token: {token}")
        return inst.tradingsymbol


def record_symbol_change(old_symbol: str, new_symbol: str, settings: Settings) -> bool:
    """Record a symbol rename in the SymbolChange mapping table if not already
    known (idempotent). Returns True when a new row was inserted.

    Used by `platform data migrate-symbol` for the repair path where a rename
    was never captured by `data instruments` (e.g. the instrument dump was
    synced only after the rename). instrument_token resolves from the new
    symbol's active listing when the instrument master knows it, else 0.
    """
    with meta_session(settings.meta_db_path) as session:
        existing = session.exec(
            select(SymbolChange).where(
                SymbolChange.old_symbol == old_symbol,
                SymbolChange.new_symbol == new_symbol,
            )
        ).first()
        if existing is not None:
            return False
        inst = session.exec(
            select(Instrument)
            .where(Instrument.tradingsymbol == new_symbol)
            .order_by(
                Instrument.last_seen.desc(),  # type: ignore[attr-defined]
                Instrument.first_seen.desc(),  # type: ignore[attr-defined]
                Instrument.id.desc(),  # type: ignore[union-attr]
            )
        ).first()
        session.add(
            SymbolChange(
                instrument_token=inst.instrument_token if inst is not None else 0,
                old_symbol=old_symbol,
                new_symbol=new_symbol,
                detected_on=now_ist().date(),
            )
        )
        session.commit()
        logger.info("recorded symbol change %s -> %s", old_symbol, new_symbol)
        return True


def symbol_history(symbol: str, settings: Settings) -> list[SymbolChange]:
    """All recorded SymbolChange rows touching `symbol`, as either its old or
    new name, ordered by detection date."""
    with meta_session(settings.meta_db_path) as session:
        rows = session.exec(
            select(SymbolChange)
            .where((SymbolChange.old_symbol == symbol) | (SymbolChange.new_symbol == symbol))
            .order_by(SymbolChange.detected_on)
        ).all()
        return list(rows)

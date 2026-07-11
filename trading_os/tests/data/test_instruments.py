"""Instrument sync + symbol-mapping tests. `kite` is a fake -- never network."""

from __future__ import annotations

import pytest

from tradingos.config.settings import Settings
from tradingos.core.errors import DataError
from tradingos.core.timeutils import now_ist
from tradingos.data.instruments import (
    Instrument,
    SymbolChange,
    current_symbol_for,
    symbol_history,
    sync_instruments,
    token_for,
)
from tradingos.data.meta import meta_session


class FakeKite:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows
        self.calls: list[str] = []

    def instruments(self, exchange: str) -> list[dict]:
        self.calls.append(exchange)
        return self.rows


def eq_row(token: int, symbol: str, name: str = "Some Co", lot_size: int = 1, tick_size: float = 0.05) -> dict:
    return {
        "instrument_token": token,
        "tradingsymbol": symbol,
        "name": name,
        "exchange": "NSE",
        "segment": "NSE",
        "instrument_type": "EQ",
        "lot_size": lot_size,
        "tick_size": tick_size,
    }


def index_row(token: int, symbol: str) -> dict:
    # e.g. NIFTY 50 -- must be filtered out (not a tradable equity).
    return {
        "instrument_token": token,
        "tradingsymbol": symbol,
        "name": symbol,
        "exchange": "NSE",
        "segment": "INDICES",
        "instrument_type": "EQ",
        "lot_size": 0,
        "tick_size": 0.05,
    }


def test_sync_filters_to_nse_equities_and_calls_correct_exchange(settings: Settings) -> None:
    kite = FakeKite([eq_row(1, "RELIANCE"), eq_row(2, "TCS"), index_row(3, "NIFTY 50")])
    summary = sync_instruments(kite, settings)

    assert kite.calls == ["NSE"]
    assert summary == {"fetched": 2, "added": 2, "updated": 0, "symbol_changes": 0}
    assert token_for("RELIANCE", settings) == 1
    assert token_for("TCS", settings) == 2
    with pytest.raises(DataError):
        token_for("NIFTY 50", settings)


def test_sync_upserts_and_bumps_last_seen(settings: Settings) -> None:
    kite = FakeKite([eq_row(1, "RELIANCE")])
    sync_instruments(kite, settings)
    summary2 = sync_instruments(kite, settings)

    assert summary2 == {"fetched": 1, "added": 0, "updated": 1, "symbol_changes": 0}
    assert token_for("RELIANCE", settings) == 1

    with meta_session(settings.meta_db_path) as session:
        from sqlmodel import select

        row = session.exec(select(Instrument).where(Instrument.instrument_token == 1)).first()
        assert row is not None
        assert row.first_seen == now_ist().date()
        assert row.last_seen == now_ist().date()


def test_symbol_change_detected_and_recorded(settings: Settings) -> None:
    kite = FakeKite([eq_row(42, "OLDNAME")])
    sync_instruments(kite, settings)
    assert current_symbol_for(42, settings) == "OLDNAME"

    # symbol renamed, same instrument_token
    kite.rows = [eq_row(42, "NEWNAME")]
    summary = sync_instruments(kite, settings)

    assert summary == {"fetched": 1, "added": 0, "updated": 1, "symbol_changes": 1}
    assert current_symbol_for(42, settings) == "NEWNAME"
    assert token_for("NEWNAME", settings) == 42

    # old name no longer resolves via token_for (it's not the current symbol)...
    with pytest.raises(DataError):
        token_for("OLDNAME", settings)

    # ...but the rename is preserved in the symbol-mapping table.
    history_old = symbol_history("OLDNAME", settings)
    history_new = symbol_history("NEWNAME", settings)
    assert len(history_old) == 1
    assert history_old == history_new
    change = history_old[0]
    assert isinstance(change, SymbolChange)
    assert change.instrument_token == 42
    assert change.old_symbol == "OLDNAME"
    assert change.new_symbol == "NEWNAME"
    assert change.detected_on == now_ist().date()


def test_no_symbol_change_when_symbol_unchanged(settings: Settings) -> None:
    kite = FakeKite([eq_row(7, "STABLE")])
    sync_instruments(kite, settings)
    summary = sync_instruments(kite, settings)
    assert summary["symbol_changes"] == 0
    assert symbol_history("STABLE", settings) == []


def test_token_for_unknown_symbol_raises(settings: Settings) -> None:
    with pytest.raises(DataError):
        token_for("NOPE", settings)


def test_current_symbol_for_unknown_token_raises(settings: Settings) -> None:
    with pytest.raises(DataError):
        current_symbol_for(999999, settings)


def test_symbol_history_empty_for_unknown_symbol(settings: Settings) -> None:
    assert symbol_history("NEVER_SEEN", settings) == []

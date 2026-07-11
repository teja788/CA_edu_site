"""Known-answer tests for the point-in-time universe (survivorship defense).

The membership timeline, boundary inclusivity, and the liquidity look-ahead
cases are hand-constructed; see comments for the reasoning behind each expected
result.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pandas as pd

from tradingos.config.schemas import UniverseSpec
from tradingos.config.settings import Settings
from tradingos.core.models import Timeframe
from tradingos.data.actions import CorporateAction
from tradingos.data.meta import meta_session
from tradingos.data.universe import (
    PITUniverseResolver,
    UniverseMembership,
    delisting_date,
    import_membership_csv,
    members_as_of,
    membership_coverage,
)
from tradingos.engine.dataview import MarketData


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _seed_timeline(settings: Settings) -> None:
    """A member 2015-01-01..2018-06-30; B 2016-01-01..open; C 2019-01-01..open."""
    with meta_session(settings.meta_db_path) as s:
        s.add(UniverseMembership(index_name="IDX", symbol="A",
                                 start_date=date(2015, 1, 1), end_date=date(2018, 6, 30)))
        s.add(UniverseMembership(index_name="IDX", symbol="B",
                                 start_date=date(2016, 1, 1), end_date=None))
        s.add(UniverseMembership(index_name="IDX", symbol="C",
                                 start_date=date(2019, 1, 1), end_date=None))
        s.commit()


def _flat_frame(symbols: list[str], *, close: float = 100.0, volume: int = 1_000_000,
                n: int = 5, start: date = date(2020, 1, 1)) -> MarketData:
    idx = pd.DatetimeIndex([datetime(start.year, start.month, start.day) + pd.Timedelta(days=i)
                            for i in range(n)])
    frames = {
        s: pd.DataFrame(
            {"open": close, "high": close, "low": close, "close": close, "volume": volume},
            index=idx,
        )
        for s in symbols
    }
    return MarketData(frames, timeframe=Timeframe.DAY)


# --------------------------------------------------------------------------- #
# members_as_of / coverage
# --------------------------------------------------------------------------- #
class TestMembership:
    def test_members_as_of_timeline(self, settings: Settings) -> None:
        _seed_timeline(settings)
        # 2015-06-01: only A active
        assert members_as_of("IDX", date(2015, 6, 1), settings) == ["A"]
        # 2016-06-01: A and B
        assert members_as_of("IDX", date(2016, 6, 1), settings) == ["A", "B"]
        # 2018-06-30: A's end_date is inclusive -> still A, plus B
        assert members_as_of("IDX", date(2018, 6, 30), settings) == ["A", "B"]
        # 2019-01-01: A gone (ended 2018-06-30), B open, C's start_date inclusive
        assert members_as_of("IDX", date(2019, 1, 1), settings) == ["B", "C"]

    def test_start_date_inclusive(self, settings: Settings) -> None:
        _seed_timeline(settings)
        # exactly on A's start date
        assert "A" in members_as_of("IDX", date(2015, 1, 1), settings)

    def test_coverage(self, settings: Settings) -> None:
        _seed_timeline(settings)
        lower, upper = membership_coverage("IDX", settings)
        assert lower == date(2015, 1, 1)
        # open spells (B, C) extend coverage to at least today
        assert upper >= date.today()

    def test_coverage_none_when_empty(self, settings: Settings) -> None:
        assert membership_coverage("IDX", settings) is None

    def test_import_membership_roundtrip_idempotent(self, settings: Settings,
                                                    tmp_path: Path) -> None:
        csv_path = tmp_path / "members.csv"
        csv_path.write_text(
            "index_name,symbol,start_date,end_date\n"
            "IDX,A,2015-01-01,2018-06-30\n"
            "IDX,B,2016-01-01,\n"
        )
        assert import_membership_csv(csv_path, settings) == 2
        assert import_membership_csv(csv_path, settings) == 0  # idempotent
        assert members_as_of("IDX", date(2017, 1, 1), settings) == ["A", "B"]


# --------------------------------------------------------------------------- #
# delisting_date (imported from actions)
# --------------------------------------------------------------------------- #
class TestDelisting:
    def test_delisting_date_roundtrip(self, settings: Settings) -> None:
        with meta_session(settings.meta_db_path) as s:
            s.add(CorporateAction(symbol="DEAD", ex_date=date(2021, 4, 5),
                                  action_type="delisting"))
            s.commit()
        assert delisting_date("DEAD", settings) == date(2021, 4, 5)

    def test_earliest_of_suspension_and_delisting(self, settings: Settings) -> None:
        with meta_session(settings.meta_db_path) as s:
            s.add(CorporateAction(symbol="DEAD", ex_date=date(2021, 4, 5),
                                  action_type="delisting"))
            s.add(CorporateAction(symbol="DEAD", ex_date=date(2020, 1, 1),
                                  action_type="suspension"))
            s.commit()
        assert delisting_date("DEAD", settings) == date(2020, 1, 1)

    def test_active_symbol_none(self, settings: Settings) -> None:
        assert delisting_date("ALIVE", settings) is None


# --------------------------------------------------------------------------- #
# PITUniverseResolver
# --------------------------------------------------------------------------- #
class TestResolver:
    def test_pit_path_intersects_data(self, settings: Settings) -> None:
        _seed_timeline(settings)
        # on 2017-01-01 members are A, B; data has A, B, Z (Z not a member,
        # C is a member later but no data now)
        data = _flat_frame(["A", "B", "Z"])
        resolver = PITUniverseResolver(settings)
        spec = UniverseSpec(index="IDX", point_in_time=True)
        out = resolver.resolve(spec, date(2017, 1, 1), data)
        assert out == ["A", "B"]  # members ∩ data.symbols, Z excluded
        assert resolver.warnings == []

    def test_empty_table_emits_survivorship_warning_once(self, settings: Settings) -> None:
        data = _flat_frame(["A", "B"])
        resolver = PITUniverseResolver(settings)
        spec = UniverseSpec(index="NOSUCH", point_in_time=True)
        out1 = resolver.resolve(spec, date(2017, 1, 1), data)
        out2 = resolver.resolve(spec, date(2018, 1, 1), data)
        assert out1 == ["A", "B"]  # fell back to all data symbols
        assert out2 == ["A", "B"]
        survivorship = [w for w in resolver.warnings if "SURVIVORSHIP BIAS" in w]
        assert len(survivorship) == 1  # deduped: exactly once
        assert "overstate performance" in survivorship[0]

    def test_explicit_symbols_bypass_pit(self, settings: Settings) -> None:
        # no membership seeded, but explicit list must NOT trigger survivorship warning
        data = _flat_frame(["A", "B", "C"])
        resolver = PITUniverseResolver(settings)
        spec = UniverseSpec(index="IDX", point_in_time=True, symbols=["A", "B"])
        out = resolver.resolve(spec, date(2017, 1, 1), data)
        assert out == ["A", "B"]
        assert resolver.warnings == []

    def _liq_frame(self, closes: list[float], volumes: list[int]) -> pd.DataFrame:
        idx = pd.DatetimeIndex([datetime(2020, 1, 1) + pd.Timedelta(days=i)
                                for i in range(len(closes))])
        return pd.DataFrame(
            {"open": closes, "high": closes, "low": closes, "close": closes, "volume": volumes},
            index=idx,
        )

    def test_liquidity_lookahead_both_directions(self, settings: Settings) -> None:
        # lookback 3, threshold 1000, `on` = day 2 -> only days 0,1,2 may count.
        # BELOW: visible value 10*50=500 (<1000) but future bars spike to 10*10000
        #        -> must be EXCLUDED (a leaky tail-then-slice would wrongly keep it).
        # ABOVE: visible value 10*500=5000 (>=1000) but future bars collapse to 10*10
        #        -> must be KEPT (future lows must not drag it below).
        below = self._liq_frame([10.0] * 6, [50, 50, 50, 10_000, 10_000, 10_000])
        above = self._liq_frame([10.0] * 6, [500, 500, 500, 10, 10, 10])
        data = MarketData({"BELOW": below, "ABOVE": above}, timeframe=Timeframe.DAY)
        resolver = PITUniverseResolver(settings)
        spec = UniverseSpec(
            index="IDX", point_in_time=True, symbols=["BELOW", "ABOVE"],
            min_median_traded_value=1_000.0, liquidity_lookback_days=3,
        )
        assert resolver.resolve(spec, date(2020, 1, 3), data) == ["ABOVE"]

    def test_liquidity_temporal_inclusion(self, settings: Settings) -> None:
        # Same symbol: illiquid early, liquid later. Inclusion depends on `on`.
        low = self._liq_frame([10.0] * 6, [50, 50, 50, 10_000, 10_000, 10_000])
        data = MarketData({"LOW": low}, timeframe=Timeframe.DAY)
        resolver = PITUniverseResolver(settings)
        spec = UniverseSpec(
            index="IDX", point_in_time=True, symbols=["LOW"],
            min_median_traded_value=1_000.0, liquidity_lookback_days=3,
        )
        # as of day 2: visible median 500 < 1000 -> excluded
        assert resolver.resolve(spec, date(2020, 1, 3), data) == []
        # as of day 5: high-volume bars now legitimately visible -> included
        assert resolver.resolve(spec, date(2020, 1, 6), data) == ["LOW"]

    def test_no_bars_as_of_date_dropped(self, settings: Settings) -> None:
        # symbol has data, but all of it is AFTER `on` -> no visible bars -> dropped
        future = self._liq_frame([100.0] * 3, [1_000_000] * 3)  # days 0,1,2 = 2020-01-01..03
        data = MarketData({"FUT": future}, timeframe=Timeframe.DAY)
        resolver = PITUniverseResolver(settings)
        spec = UniverseSpec(
            index="IDX", point_in_time=True, symbols=["FUT"],
            min_median_traded_value=1.0, liquidity_lookback_days=3,
        )
        assert resolver.resolve(spec, date(2019, 12, 31), data) == []

    def test_satisfies_universe_resolver_protocol(self, settings: Settings) -> None:
        from tradingos.engine.base import UniverseResolver

        resolver = PITUniverseResolver(settings)
        assert isinstance(resolver, UniverseResolver)

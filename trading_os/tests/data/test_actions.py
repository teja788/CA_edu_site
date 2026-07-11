"""Known-answer tests for corporate actions and back-adjustment.

Every expected number below is hand-computed from the ratio/factor conventions
documented in ``tradingos.data.actions`` — see the worked arithmetic in each
test's comments. If one fails, either the math or the conventions changed;
investigate before editing expected values.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pandas as pd
import polars as pl
import pytest

from tradingos.config.settings import Settings
from tradingos.core.errors import DataError
from tradingos.core.models import Timeframe
from tradingos.data.actions import (
    AdjustmentFlag,
    CorporateAction,
    Dividend,
    adjustment_factors,
    apply_adjustments,
    build_adjusted,
    get_actions,
    get_dividends,
    import_actions_csv,
    import_dividends_csv,
    total_return_close,
    validate_adjustments,
)
from tradingos.data.meta import meta_session


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _add_action(settings: Settings, **kwargs) -> None:
    with meta_session(settings.meta_db_path) as s:
        s.add(CorporateAction(**kwargs))
        s.commit()


def _raw(rows: list[tuple]) -> pl.DataFrame:
    """rows: (ts, open, high, low, close, volume)."""
    ts, o, h, low, c, v = zip(*rows, strict=True)
    return pl.DataFrame(
        {
            "ts": list(ts),
            "open": list(o),
            "high": list(h),
            "low": list(low),
            "close": list(c),
            "volume": list(v),
        }
    )


# --------------------------------------------------------------------------- #
# price_factor conventions
# --------------------------------------------------------------------------- #
class TestPriceFactor:
    def test_split_10_to_2(self) -> None:
        # old_face:new_face = 10:2 -> 1 share becomes 5, divisor 10/2 = 5
        a = CorporateAction(symbol="X", ex_date=date(2020, 1, 3), action_type="split",
                            ratio_num=10, ratio_den=2)
        assert a.price_factor == 5.0

    def test_bonus_1_1(self) -> None:
        # 1:1 bonus -> 1 share becomes (1+1)/1 = 2, divisor 2
        a = CorporateAction(symbol="X", ex_date=date(2020, 1, 3), action_type="bonus",
                            ratio_num=1, ratio_den=1)
        assert a.price_factor == 2.0

    def test_bonus_3_2(self) -> None:
        # 3:2 bonus -> divisor (3+2)/2 = 2.5
        a = CorporateAction(symbol="X", ex_date=date(2020, 1, 3), action_type="bonus",
                            ratio_num=3, ratio_den=2)
        assert a.price_factor == 2.5

    def test_non_price_actions_are_one(self) -> None:
        for at in ("symbol_change", "delisting", "suspension"):
            a = CorporateAction(symbol="X", ex_date=date(2020, 1, 3), action_type=at,
                                new_symbol="Y" if at == "symbol_change" else None)
            assert a.price_factor == 1.0


# --------------------------------------------------------------------------- #
# adjustment_factors
# --------------------------------------------------------------------------- #
class TestAdjustmentFactors:
    def test_single_split_strictly_before(self) -> None:
        # 10:2 split (factor 5) ex-date 2020-01-03.
        # bars strictly before 01-03 -> 5; on/after -> 1.0
        idx = pd.DatetimeIndex([datetime(2020, 1, d) for d in (1, 2, 3, 6)])
        a = CorporateAction(symbol="X", ex_date=date(2020, 1, 3), action_type="split",
                            ratio_num=10, ratio_den=2)
        f = adjustment_factors([a], idx)
        assert f.tolist() == [5.0, 5.0, 1.0, 1.0]

    def test_stacked_actions_compound(self) -> None:
        # split 10:2 (factor 5) ex 01-03, bonus 1:1 (factor 2) ex 01-05.
        # 01-02: before both -> 5*2 = 10
        # 01-03: on split ex, before bonus -> 1*2 = 2
        # 01-04: after split, before bonus -> 2
        # 01-06: after both -> 1
        idx = pd.DatetimeIndex([datetime(2020, 1, d) for d in (2, 3, 4, 6)])
        split = CorporateAction(symbol="X", ex_date=date(2020, 1, 3), action_type="split",
                                ratio_num=10, ratio_den=2)
        bonus = CorporateAction(symbol="X", ex_date=date(2020, 1, 5), action_type="bonus",
                                ratio_num=1, ratio_den=1)
        f = adjustment_factors([split, bonus], idx)
        assert f.tolist() == [10.0, 2.0, 2.0, 1.0]

    def test_no_price_action_all_ones(self) -> None:
        idx = pd.DatetimeIndex([datetime(2020, 1, d) for d in (1, 2, 3)])
        a = CorporateAction(symbol="X", ex_date=date(2020, 1, 2), action_type="symbol_change",
                            new_symbol="Y")
        assert adjustment_factors([a], idx).tolist() == [1.0, 1.0, 1.0]


# --------------------------------------------------------------------------- #
# apply_adjustments
# --------------------------------------------------------------------------- #
class TestApplyAdjustments:
    def test_split_backadjusts_price_and_volume(self) -> None:
        # pre-ex bar close 500, vol 1000; ex-date bar already at new regime.
        # 10:2 split, factor 5 -> pre-ex close 100, vol 5000; ex bar unchanged.
        split = CorporateAction(symbol="X", ex_date=date(2020, 1, 3), action_type="split",
                                ratio_num=10, ratio_den=2)
        raw = _raw([
            (datetime(2020, 1, 2), 490.0, 510.0, 480.0, 500.0, 1000),
            (datetime(2020, 1, 3), 98.0, 102.0, 97.0, 100.0, 5000),
        ])
        out = apply_adjustments(raw, [split])
        assert out["close"].to_list() == [100.0, 100.0]
        assert out["open"].to_list() == [98.0, 98.0]
        assert out["high"].to_list() == [102.0, 102.0]
        assert out["low"].to_list() == [96.0, 97.0]
        assert out["volume"].to_list() == [5000, 5000]
        assert out["volume"].dtype == pl.Int64
        # ts untouched
        assert out["ts"].to_list() == raw["ts"].to_list()

    def test_bonus_divisor_two(self) -> None:
        bonus = CorporateAction(symbol="X", ex_date=date(2020, 1, 3), action_type="bonus",
                                ratio_num=1, ratio_den=1)
        raw = _raw([
            (datetime(2020, 1, 2), 100.0, 100.0, 100.0, 100.0, 1000),
            (datetime(2020, 1, 3), 50.0, 50.0, 50.0, 50.0, 2000),
        ])
        out = apply_adjustments(raw, [bonus])
        assert out["close"].to_list() == [50.0, 50.0]  # pre-ex 100/2, ex unchanged
        assert out["volume"].to_list() == [2000, 2000]

    def test_stacked_compound_10x(self) -> None:
        split = CorporateAction(symbol="X", ex_date=date(2020, 1, 3), action_type="split",
                                ratio_num=10, ratio_den=2)
        bonus = CorporateAction(symbol="X", ex_date=date(2020, 1, 5), action_type="bonus",
                                ratio_num=1, ratio_den=1)
        # bar before both actions: prices /10, volume *10
        raw = _raw([(datetime(2020, 1, 2), 1000.0, 1000.0, 1000.0, 1000.0, 100)])
        out = apply_adjustments(raw, [split, bonus])
        assert out["close"].to_list() == [100.0]
        assert out["volume"].to_list() == [1000]

    def test_post_ex_rows_identical_to_raw(self) -> None:
        split = CorporateAction(symbol="X", ex_date=date(2020, 1, 3), action_type="split",
                                ratio_num=10, ratio_den=2)
        raw = _raw([
            (datetime(2020, 1, 3), 98.0, 102.0, 97.0, 100.0, 5000),
            (datetime(2020, 1, 6), 99.0, 103.0, 98.0, 101.0, 4000),
        ])
        out = apply_adjustments(raw, [split])
        assert out.equals(raw)  # factor 1.0 leaves these bars byte-identical

    def test_empty_frame_returns_empty(self) -> None:
        raw = pl.DataFrame(
            schema={"ts": pl.Datetime, "open": pl.Float64, "high": pl.Float64,
                    "low": pl.Float64, "close": pl.Float64, "volume": pl.Int64}
        )
        out = apply_adjustments(raw, [])
        assert out.is_empty()


# --------------------------------------------------------------------------- #
# total_return_close
# --------------------------------------------------------------------------- #
class TestTotalReturnClose:
    def test_three_bar_one_dividend(self) -> None:
        # closes 100, 110, 121; ₹2 dividend on the middle bar's ex-date.
        #   gross[0] = 1                  -> tr[0] = 100
        #   gross[1] = (110+2)/100 = 1.12 -> tr[1] = 100 * 1.12 = 112
        #   gross[2] = (121+0)/110 = 1.1  -> tr[2] = 112 * 1.1  = 123.2
        idx = pd.DatetimeIndex([datetime(2020, 1, d) for d in (1, 2, 3)])
        close = pd.Series([100.0, 110.0, 121.0], index=idx)
        divs = [Dividend(symbol="X", ex_date=date(2020, 1, 2), amount=2.0)]
        tr = total_return_close(close, divs)
        assert tr.tolist() == pytest.approx([100.0, 112.0, 123.2])

    def test_no_dividends_equals_price(self) -> None:
        idx = pd.DatetimeIndex([datetime(2020, 1, d) for d in (1, 2, 3)])
        close = pd.Series([100.0, 110.0, 121.0], index=idx)
        tr = total_return_close(close, [])
        assert tr.tolist() == pytest.approx([100.0, 110.0, 121.0])


# --------------------------------------------------------------------------- #
# validate_adjustments
# --------------------------------------------------------------------------- #
class TestValidateAdjustments:
    def _frame(self, closes: list[float]) -> pd.DataFrame:
        idx = pd.DatetimeIndex([datetime(2020, 1, 1) + pd.Timedelta(days=i)
                                for i in range(len(closes))])
        return pd.DataFrame(
            {"open": closes, "high": closes, "low": closes, "close": closes,
             "volume": [1000] * len(closes)},
            index=idx,
        )

    def test_unexplained_gap_flagged(self) -> None:
        # 100 -> 50 overnight = -50% > 40% threshold, no recorded action -> flag
        frames = {"SYM": self._frame([100.0, 50.0])}
        flags = validate_adjustments(frames, {})
        assert flags == [AdjustmentFlag(symbol="SYM", date=date(2020, 1, 2), gap=pytest.approx(-0.5))]

    def test_recorded_action_not_flagged(self) -> None:
        frames = {"SYM": self._frame([100.0, 50.0])}
        actions = {"SYM": [CorporateAction(symbol="SYM", ex_date=date(2020, 1, 2),
                                           action_type="bonus", ratio_num=1, ratio_den=1)]}
        assert validate_adjustments(frames, actions) == []

    def test_market_wide_move_not_flagged(self) -> None:
        # symbol drops 50% but market fell 6% (> 5% threshold) -> treated as market-wide
        idx = pd.DatetimeIndex([datetime(2020, 1, 1), datetime(2020, 1, 2)])
        frames = {"SYM": self._frame([100.0, 50.0])}
        market = pd.Series([100.0, 94.0], index=idx)  # -6%
        assert validate_adjustments(frames, {}, market=market) == []

    def test_market_small_move_still_flagged(self) -> None:
        idx = pd.DatetimeIndex([datetime(2020, 1, 1), datetime(2020, 1, 2)])
        frames = {"SYM": self._frame([100.0, 50.0])}
        market = pd.Series([100.0, 98.0], index=idx)  # -2%, below threshold
        flags = validate_adjustments(frames, {}, market=market)
        assert len(flags) == 1 and flags[0].symbol == "SYM"

    def test_small_gap_ignored(self) -> None:
        frames = {"SYM": self._frame([100.0, 90.0])}  # -10%, below 40%
        assert validate_adjustments(frames, {}) == []


# --------------------------------------------------------------------------- #
# CSV importers
# --------------------------------------------------------------------------- #
class TestImporters:
    def test_actions_roundtrip_and_idempotent(self, settings: Settings, tmp_path: Path) -> None:
        csv_path = tmp_path / "actions.csv"
        csv_path.write_text(
            "symbol,ex_date,action_type,ratio_num,ratio_den,new_symbol,note,extra\n"
            "AAA,2020-01-03,split,10,2,,ten-to-two,IGNORED\n"
            "AAA,2021-06-01,bonus,1,1,,,IGNORED\n"
            "BBB,2019-05-05,symbol_change,,,BBBNEW,renamed,IGNORED\n"
        )
        n = import_actions_csv(csv_path, settings)
        assert n == 3
        # idempotent: re-importing the same file inserts nothing
        assert import_actions_csv(csv_path, settings) == 0

        aaa = get_actions("AAA", settings)
        assert [a.action_type for a in aaa] == ["split", "bonus"]  # ordered by ex_date
        assert aaa[0].price_factor == 5.0
        bbb = get_actions("BBB", settings)
        assert bbb[0].new_symbol == "BBBNEW"

    def test_actions_bad_type_raises(self, settings: Settings, tmp_path: Path) -> None:
        csv_path = tmp_path / "bad.csv"
        csv_path.write_text("symbol,ex_date,action_type,ratio_num,ratio_den,new_symbol,note\n"
                            "AAA,2020-01-03,merger,,,,\n")
        with pytest.raises(DataError, match="unknown action_type"):
            import_actions_csv(csv_path, settings)

    def test_split_missing_ratio_raises(self, settings: Settings, tmp_path: Path) -> None:
        csv_path = tmp_path / "bad2.csv"
        csv_path.write_text("symbol,ex_date,action_type,ratio_num,ratio_den,new_symbol,note\n"
                            "AAA,2020-01-03,split,,,,\n")
        with pytest.raises(DataError, match="requires ratio"):
            import_actions_csv(csv_path, settings)

    def test_dividends_roundtrip_and_idempotent(self, settings: Settings, tmp_path: Path) -> None:
        csv_path = tmp_path / "divs.csv"
        csv_path.write_text("symbol,ex_date,amount\nAAA,2020-03-01,5.5\nAAA,2021-03-01,6.0\n")
        assert import_dividends_csv(csv_path, settings) == 2
        assert import_dividends_csv(csv_path, settings) == 0
        divs = get_dividends("AAA", settings)
        assert [d.amount for d in divs] == [5.5, 6.0]

    def test_dividend_non_positive_raises(self, settings: Settings, tmp_path: Path) -> None:
        csv_path = tmp_path / "baddiv.csv"
        csv_path.write_text("symbol,ex_date,amount\nAAA,2020-03-01,0\n")
        with pytest.raises(DataError, match="must be > 0"):
            import_dividends_csv(csv_path, settings)


# --------------------------------------------------------------------------- #
# build_adjusted (fake store injection)
# --------------------------------------------------------------------------- #
class _FakeStore:
    def __init__(self, raw: pl.DataFrame) -> None:
        self._raw = raw
        self.written: pl.DataFrame | None = None

    def read_raw(self, symbol: str, timeframe: Timeframe) -> pl.DataFrame:
        return self._raw

    def write_adjusted(self, symbol: str, timeframe: Timeframe, df: pl.DataFrame) -> int:
        self.written = df
        return df.height

    def write_adjustment_meta(self, symbol: str, timeframe: Timeframe, meta: dict) -> None:
        self.meta = meta

    def symbols(self, timeframe: Timeframe) -> list[str]:
        return ["TEST"]


class TestBuildAdjusted:
    def test_reads_applies_writes(self, settings: Settings) -> None:
        _add_action(settings, symbol="TEST", ex_date=date(2020, 1, 3),
                    action_type="split", ratio_num=10, ratio_den=2)
        raw = _raw([
            (datetime(2020, 1, 2), 490.0, 510.0, 480.0, 500.0, 1000),
            (datetime(2020, 1, 3), 98.0, 102.0, 97.0, 100.0, 5000),
        ])
        store = _FakeStore(raw)
        n = build_adjusted("TEST", Timeframe.DAY, settings, store=store)
        assert n == 2
        assert store.written is not None
        assert store.written["close"].to_list() == [100.0, 100.0]  # pre-ex 500/5
        assert store.written["volume"].to_list() == [5000, 5000]

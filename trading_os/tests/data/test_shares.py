"""Known-answer tests for the shares-outstanding data layer.

Covers the CSV importer (counts, (symbol, as_of) upsert, invalid-row skip),
``latest_shares`` (max as_of wins), and the market-cap / scaled-turnover panels
including the split-invariance identity, causality, and missing-snapshot
omission. Every expected number is hand-computed in the test's comments.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from tradingos.config.settings import Settings
from tradingos.data.actions import import_shares_csv
from tradingos.data.shares import (
    latest_shares,
    mcap_panel,
    mcap_series,
    scaled_turnover_panel,
)
from tradingos.engine.dataview import MarketData


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _frame(closes: list[float], volumes: list[float]) -> pd.DataFrame:
    idx = pd.DatetimeIndex(pd.date_range("2020-01-01", periods=len(closes), freq="D"))
    return pd.DataFrame(
        {
            "open": closes,
            "high": closes,
            "low": closes,
            "close": [float(c) for c in closes],
            "volume": [float(v) for v in volumes],
        },
        index=idx,
    )


def _market(frames: dict[str, pd.DataFrame]) -> MarketData:
    return MarketData(frames=frames)


# --------------------------------------------------------------------------- #
# import_shares_csv
# --------------------------------------------------------------------------- #
class TestImportSharesCsv:
    def test_import_counts(self, settings: Settings, tmp_path: Path) -> None:
        csv = tmp_path / "shares.csv"
        csv.write_text(
            "symbol,shares,as_of,source\n"
            "AAA,1000,2020-01-01,filing\n"
            "BBB,2000,2020-01-01,vendor\n"
        )
        counts = import_shares_csv(csv, settings)
        assert counts == {"imported": 2, "replaced": 0, "skipped": 0}

    def test_upsert_replaces_same_symbol_asof(self, settings: Settings, tmp_path: Path) -> None:
        first = tmp_path / "a.csv"
        first.write_text("symbol,shares,as_of,source\nAAA,1000,2020-01-01,filing\n")
        assert import_shares_csv(first, settings)["imported"] == 1

        # same (symbol, as_of), new share count -> replaced, latest_shares reflects it
        second = tmp_path / "b.csv"
        second.write_text("symbol,shares,as_of,source\nAAA,1500,2020-01-01,corrected\n")
        counts = import_shares_csv(second, settings)
        assert counts == {"imported": 0, "replaced": 1, "skipped": 0}
        assert latest_shares(settings) == {"AAA": 1500}

    def test_distinct_asof_kept_as_history(self, settings: Settings, tmp_path: Path) -> None:
        csv = tmp_path / "hist.csv"
        csv.write_text(
            "symbol,shares,as_of,source\n"
            "AAA,1000,2020-01-01,old\n"
            "AAA,1200,2021-01-01,new\n"
        )
        counts = import_shares_csv(csv, settings)
        # distinct as_of dates -> two separate rows, both inserts
        assert counts == {"imported": 2, "replaced": 0, "skipped": 0}
        # latest as_of wins
        assert latest_shares(settings) == {"AAA": 1200}

    def test_invalid_rows_skipped_with_count(self, settings: Settings, tmp_path: Path) -> None:
        csv = tmp_path / "bad.csv"
        csv.write_text(
            "symbol,shares,as_of,source\n"
            "AAA,1000,2020-01-01,ok\n"  # valid
            ",500,2020-01-01,empty-symbol\n"  # skip: empty symbol
            "BBB,0,2020-01-01,zero\n"  # skip: shares <= 0
            "CCC,-5,2020-01-01,negative\n"  # skip: shares <= 0
            "DDD,notanumber,2020-01-01,bad-shares\n"  # skip: unparseable shares
            "EEE,700,not-a-date,bad-date\n"  # skip: unparseable as_of
        )
        counts = import_shares_csv(csv, settings)
        assert counts == {"imported": 1, "replaced": 0, "skipped": 5}
        assert latest_shares(settings) == {"AAA": 1000}


# --------------------------------------------------------------------------- #
# latest_shares
# --------------------------------------------------------------------------- #
class TestLatestShares:
    def test_empty_store(self, settings: Settings) -> None:
        assert latest_shares(settings) == {}

    def test_picks_max_as_of_regardless_of_insert_order(
        self, settings: Settings, tmp_path: Path
    ) -> None:
        csv = tmp_path / "s.csv"
        # newest row is listed FIRST to prove ordering is by as_of, not row order
        csv.write_text(
            "symbol,shares,as_of,source\n"
            "AAA,3000,2022-01-01,newest\n"
            "AAA,1000,2020-01-01,oldest\n"
            "AAA,2000,2021-01-01,middle\n"
            "BBB,50,2019-06-30,only\n"
        )
        import_shares_csv(csv, settings)
        assert latest_shares(settings) == {"AAA": 3000, "BBB": 50}


# --------------------------------------------------------------------------- #
# mcap_series
# --------------------------------------------------------------------------- #
class TestMcapSeries:
    def test_known_answer(self) -> None:
        frame = _frame([10, 20, 30], [1, 1, 1])
        s = mcap_series(frame, shares=1000)
        # 1000 shares * close
        assert list(s) == [10_000.0, 20_000.0, 30_000.0]
        assert s.name == "mcap"

    def test_split_invariance_identity(self) -> None:
        # halve the (adjusted) close, double the shares -> identical mcap series
        base = _frame([10, 20, 30], [1, 1, 1])
        split = _frame([5, 10, 15], [1, 1, 1])
        a = mcap_series(base, shares=1000)
        b = mcap_series(split, shares=2000)
        pd.testing.assert_series_equal(a, b)

    def test_causal_future_bar_perturbation(self) -> None:
        frame = _frame([10, 20, 30], [1, 1, 1])
        s0 = mcap_series(frame, shares=1000)
        perturbed = frame.copy()
        perturbed.iloc[-1, perturbed.columns.get_loc("close")] = 999.0
        s1 = mcap_series(perturbed, shares=1000)
        # earlier bars are unchanged by a future-bar perturbation
        pd.testing.assert_series_equal(s0.iloc[:-1], s1.iloc[:-1])


# --------------------------------------------------------------------------- #
# mcap_panel
# --------------------------------------------------------------------------- #
class TestMcapPanel:
    def test_alignment_and_values(self) -> None:
        data = _market({"AAA": _frame([10, 20], [1, 1]), "BBB": _frame([100, 200], [1, 1])})
        panel = mcap_panel(data, {"AAA": 1000, "BBB": 10})
        assert sorted(panel.columns) == ["AAA", "BBB"]
        assert list(panel["AAA"]) == [10_000.0, 20_000.0]
        assert list(panel["BBB"]) == [1_000.0, 2_000.0]

    def test_missing_snapshot_symbols_absent(self) -> None:
        data = _market({"AAA": _frame([10, 20], [1, 1]), "BBB": _frame([100, 200], [1, 1])})
        # only AAA has a snapshot -> BBB is entirely absent (no NaN column)
        panel = mcap_panel(data, {"AAA": 1000})
        assert list(panel.columns) == ["AAA"]
        assert "BBB" not in panel.columns

    def test_empty_when_no_snapshots(self) -> None:
        data = _market({"AAA": _frame([10, 20], [1, 1])})
        assert mcap_panel(data, {}).empty


# --------------------------------------------------------------------------- #
# scaled_turnover_panel
# --------------------------------------------------------------------------- #
class TestScaledTurnoverPanel:
    def test_known_answer(self) -> None:
        # close=10 flat, volume=1..5 -> traded_value=[10,20,30,40,50]; shares=2 -> mcap=20
        frame = _frame([10, 10, 10, 10, 10], [1, 2, 3, 4, 5])
        data = _market({"AAA": frame})
        panel = scaled_turnover_panel(data, {"AAA": 2}, window=3)
        got = panel["AAA"]
        # rolling median(window=3, min_periods=3) of traded_value / mcap(=20):
        #   bar0,1 -> NaN; bar2 median(10,20,30)=20 /20=1.0;
        #   bar3 median(20,30,40)=30 /20=1.5; bar4 median(30,40,50)=40 /20=2.0
        assert pd.isna(got.iloc[0]) and pd.isna(got.iloc[1])
        assert list(got.iloc[2:]) == [1.0, 1.5, 2.0]

    def test_causal_future_bar_perturbation(self) -> None:
        frame = _frame([10, 10, 10, 10, 10], [1, 2, 3, 4, 5])
        base = scaled_turnover_panel(_market({"AAA": frame}), {"AAA": 2}, window=3)["AAA"]
        perturbed = frame.copy()
        perturbed.iloc[-1, perturbed.columns.get_loc("volume")] = 9999.0
        after = scaled_turnover_panel(
            _market({"AAA": perturbed}), {"AAA": 2}, window=3
        )["AAA"]
        # a future (last-bar) perturbation cannot change earlier rolling values
        pd.testing.assert_series_equal(base.iloc[:-1], after.iloc[:-1])

    def test_missing_snapshot_symbols_absent(self) -> None:
        data = _market(
            {
                "AAA": _frame([10, 10, 10], [1, 2, 3]),
                "BBB": _frame([10, 10, 10], [1, 2, 3]),
            }
        )
        panel = scaled_turnover_panel(data, {"AAA": 2}, window=2)
        assert list(panel.columns) == ["AAA"]

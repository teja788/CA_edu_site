"""Tests for paper/eod.py: BacktestResult reconstruction from a paper
session, the paper-vs-reference divergence join, and the EOD report writer.

Every non-trivial expectation is a hand-computed literal (in the style of
tests/analytics/test_metrics.py) so the gross-equity identity and the
divergence-frame arithmetic are pinned exactly, not just "does it run".
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fixtures.synthetic import synthetic_daily

from tradingos.analytics.metrics import _METRIC_KEYS
from tradingos.config.schemas import EngineMode, StrategyConfig
from tradingos.config.settings import Settings
from tradingos.core.models import Fill, Position, Product, Side
from tradingos.engine.result import BacktestResult
from tradingos.paper.eod import (
    build_paper_result,
    divergence_frame,
    load_reference,
    run_eod,
    write_eod_report,
)
from tradingos.paper.ledgerdb import PaperStore

# --------------------------------------------------------------------------
# build_paper_result
# --------------------------------------------------------------------------


def test_build_paper_result_matches_hand_built_fills(settings: Settings) -> None:
    """Two fills (a full round trip) + three equity snapshots. Every derived
    field (gross equity, trades, costs, capital, window) is checked against
    hand-computed literals.

    fill1: BUY 10 TCS @ 100.00, charges 5.00, ts 2024-01-15 09:20
    fill2: SELL 10 TCS @ 110.00, charges 6.00, ts 2024-01-16 10:00 (closes the
    position, so this is the only fill that produces a Trade).

    Equity snapshots are picked independently of the fills (a real session
    marks equity from live quotes, not from replaying its own fills) so this
    also proves build_paper_result never recomputes equity, only reads
    store.equity_curve() and layers cumulative charges on top of it:
        gross[t] = equity[t] + sum(charges of fills with ts <= t)
      2024-01-15 15:30: equity 250100.00 + charges{fill1}=5.00   -> 250105.00
      2024-01-16 15:30: equity 250300.00 + charges{fill1,fill2}=11.00 -> 250311.00
      2024-01-17 15:30: equity 250300.00 (flat, no new fill) + 11.00  -> 250311.00
    """
    config = StrategyConfig(name="eod-hand-built", capital=1_000_000.0)
    store = PaperStore(settings.paper_db_path, config.name)
    stored_capital = 250_000.0
    store.ensure_run(stored_capital)

    fill1 = Fill(
        client_order_id="c1",
        symbol="TCS",
        side=Side.BUY,
        qty=10,
        price=100.0,
        ts=datetime(2024, 1, 15, 9, 20),
        charges=5.0,
        product=Product.CNC,
    )
    fill2 = Fill(
        client_order_id="c2",
        symbol="TCS",
        side=Side.SELL,
        qty=10,
        price=110.0,
        ts=datetime(2024, 1, 16, 10, 0),
        charges=6.0,
        product=Product.CNC,
    )
    store.record_fill(fill1)
    store.record_fill(fill2)

    store.snapshot_equity(datetime(2024, 1, 15, 15, 30), 250_100.0, cash=250_100.0)
    store.snapshot_equity(datetime(2024, 1, 16, 15, 30), 250_300.0, cash=250_300.0)
    store.snapshot_equity(datetime(2024, 1, 17, 15, 30), 250_300.0, cash=250_300.0)

    result = build_paper_result(store, config)

    assert result.engine == EngineMode.EVENT
    assert result.start == date(2024, 1, 15)
    assert result.end == date(2024, 1, 17)
    # store.capital() (250_000) wins over config.capital (1_000_000).
    assert result.capital == pytest.approx(250_000.0)
    assert result.meta == {"source": "paper"}

    assert result.equity.tolist() == pytest.approx([250_100.0, 250_300.0, 250_300.0])
    assert result.gross_equity.tolist() == pytest.approx([250_105.0, 250_311.0, 250_311.0])
    assert result.total_costs == pytest.approx(11.0)

    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.symbol == "TCS"
    assert trade.qty == 10
    assert trade.entry_ts == fill1.ts
    assert trade.exit_ts == fill2.ts
    assert trade.entry_price == pytest.approx(100.0)
    assert trade.exit_price == pytest.approx(110.0)
    assert trade.entry_costs == pytest.approx(5.0)
    assert trade.exit_costs == pytest.approx(6.0)
    # gross P&L (110-100)*10 = 100, minus total costs 11 -> net 89.
    assert trade.net_pnl == pytest.approx(89.0)


def test_build_paper_result_no_fills_gross_equals_net(settings: Settings) -> None:
    """With no fills at all, gross_equity must equal equity exactly (zero
    cumulative charges everywhere) and there are no trades."""
    config = StrategyConfig(name="eod-no-fills", capital=100_000.0)
    store = PaperStore(settings.paper_db_path, config.name)
    store.ensure_run(100_000.0)
    store.snapshot_equity(datetime(2024, 2, 1, 15, 30), 100_000.0, cash=100_000.0)
    store.snapshot_equity(datetime(2024, 2, 2, 15, 30), 100_500.0, cash=100_500.0)

    result = build_paper_result(store, config)

    assert result.trades == []
    assert result.total_costs == pytest.approx(0.0)
    assert result.gross_equity.tolist() == pytest.approx(result.equity.tolist())


def test_build_paper_result_empty_curve_raises(settings: Settings) -> None:
    config = StrategyConfig(name="eod-empty", capital=100_000.0)
    store = PaperStore(settings.paper_db_path, config.name)
    # no ensure_run / no snapshots at all -> empty equity_curve()
    with pytest.raises(ValueError):
        build_paper_result(store, config)


# --------------------------------------------------------------------------
# divergence_frame
# --------------------------------------------------------------------------


def _bt(name: str, index: pd.DatetimeIndex, values: list[float]) -> BacktestResult:
    equity = pd.Series(values, index=index, dtype=float)
    return BacktestResult(
        config=StrategyConfig(name=name),
        engine=EngineMode.EVENT,
        start=index[0].date(),
        end=index[-1].date(),
        capital=values[0],
        equity=equity,
        gross_equity=equity.copy(),
        trades=[],
        total_costs=0.0,
    )


def test_divergence_frame_known_answer_with_misaligned_dates() -> None:
    """paper snapshots at 15:30 IST; reference at midnight — different
    times, and only 2024-01-15/16 overlap (paper has an extra 01-17, the
    reference has an extra 01-18 instead).

    paper_equity: [100000, 100100, 100300]  (indices 01-15, 01-16, 01-17)
    ref_equity:   [100000, 100050, 100400]  (indices 01-15, 01-16, 01-18)
    -> inner join keeps only 01-15, 01-16.

    paper_ret = [0.0, 100100/100000 - 1] = [0.0, 0.001]
    ref_ret   = [0.0, 100050/100000 - 1] = [0.0, 0.0005]
    cum_diff_pct:
      01-15: 100000/100000 - 100000/100000 = 0.0
      01-16: 100100/100000 - 100050/100000 = 1.001 - 1.0005 = 0.0005
    """
    paper = _bt(
        "paper-div",
        pd.DatetimeIndex(
            [datetime(2024, 1, 15, 15, 30), datetime(2024, 1, 16, 15, 30), datetime(2024, 1, 17, 15, 30)]
        ),
        [100_000.0, 100_100.0, 100_300.0],
    )
    reference = _bt(
        "ref-div",
        pd.DatetimeIndex([datetime(2024, 1, 15, 0, 0), datetime(2024, 1, 16, 0, 0), datetime(2024, 1, 18, 0, 0)]),
        [100_000.0, 100_050.0, 100_400.0],
    )

    frame = divergence_frame(paper, reference)

    assert list(frame.index) == [date(2024, 1, 15), date(2024, 1, 16)]
    assert list(frame.columns) == ["paper_equity", "ref_equity", "paper_ret", "ref_ret", "cum_diff_pct"]
    assert frame["paper_equity"].tolist() == pytest.approx([100_000.0, 100_100.0])
    assert frame["ref_equity"].tolist() == pytest.approx([100_000.0, 100_050.0])
    np.testing.assert_allclose(frame["paper_ret"].to_numpy(), [0.0, 0.001])
    np.testing.assert_allclose(frame["ref_ret"].to_numpy(), [0.0, 0.0005])
    np.testing.assert_allclose(frame["cum_diff_pct"].to_numpy(), [0.0, 0.0005])


def test_divergence_frame_empty_overlap_returns_empty_frame_with_columns() -> None:
    paper = _bt(
        "paper-no-overlap",
        pd.DatetimeIndex([datetime(2024, 1, 15, 15, 30), datetime(2024, 1, 16, 15, 30)]),
        [100_000.0, 100_100.0],
    )
    reference = _bt(
        "ref-no-overlap",
        pd.DatetimeIndex([datetime(2024, 3, 1, 0, 0), datetime(2024, 3, 2, 0, 0)]),
        [100_000.0, 99_800.0],
    )

    frame = divergence_frame(paper, reference)

    assert frame.empty
    assert list(frame.columns) == ["paper_equity", "ref_equity", "paper_ret", "ref_ret", "cum_diff_pct"]


# --------------------------------------------------------------------------
# load_reference
# --------------------------------------------------------------------------


def test_load_reference_explicit_run_dir(settings: Settings, tmp_path: Path) -> None:
    config = StrategyConfig(name="ref-explicit", capital=100_000.0)
    idx = pd.date_range("2024-01-01", periods=5, freq="B")
    equity = pd.Series([100_000.0 * (1.001**i) for i in range(5)], index=idx)
    saved = BacktestResult(
        config=config,
        engine=EngineMode.EVENT,
        start=idx[0].date(),
        end=idx[-1].date(),
        capital=100_000.0,
        equity=equity,
        gross_equity=equity.copy(),
        trades=[],
        total_costs=0.0,
    )
    out_dir = tmp_path / "somewhere_else"
    saved.save(out_dir)

    loaded = load_reference(config, settings, run_dir=out_dir)

    assert loaded is not None
    assert loaded.capital == pytest.approx(100_000.0)
    assert loaded.equity.tolist() == pytest.approx(equity.tolist())


def test_load_reference_conventional_dir_hit(settings: Settings) -> None:
    config = StrategyConfig(name="ref-conventional", capital=200_000.0)
    idx = pd.date_range("2024-02-01", periods=5, freq="B")
    equity = pd.Series([200_000.0 + 100.0 * i for i in range(5)], index=idx)
    saved = BacktestResult(
        config=config,
        engine=EngineMode.EVENT,
        start=idx[0].date(),
        end=idx[-1].date(),
        capital=200_000.0,
        equity=equity,
        gross_equity=equity.copy(),
        trades=[],
        total_costs=0.0,
    )
    conventional = settings.artifacts_dir / "runs" / f"{config.name}-{config.config_hash()}"
    saved.save(conventional)

    loaded = load_reference(config, settings)

    assert loaded is not None
    assert loaded.capital == pytest.approx(200_000.0)
    assert loaded.equity.tolist() == pytest.approx(equity.tolist())


def test_load_reference_conventional_dir_miss_returns_none(settings: Settings) -> None:
    config = StrategyConfig(name="ref-nowhere", capital=100_000.0)
    assert load_reference(config, settings) is None


# --------------------------------------------------------------------------
# write_eod_report / run_eod
# --------------------------------------------------------------------------


def _build_paper_session(
    settings: Settings, config: StrategyConfig, n_days: int = 10
) -> tuple[PaperStore, pd.DatetimeIndex, float]:
    """A small paper session: two fills plus one equity snapshot per trading
    day over ``n_days`` business days starting 2024-03-04 (a Monday)."""
    store = PaperStore(settings.paper_db_path, config.name)
    store.ensure_run(config.capital)

    days = pd.bdate_range("2024-03-04", periods=n_days)

    fill1 = Fill(
        client_order_id="p1",
        symbol="TCS",
        side=Side.BUY,
        qty=10,
        price=3_500.0,
        ts=datetime(days[0].year, days[0].month, days[0].day, 9, 20),
        charges=15.0,
        product=Product.CNC,
    )
    fill2 = Fill(
        client_order_id="p2",
        symbol="INFY",
        side=Side.BUY,
        qty=5,
        price=1_500.0,
        ts=datetime(days[1].year, days[1].month, days[1].day, 9, 25),
        charges=8.0,
        product=Product.CNC,
    )
    store.record_fill(fill1)
    store.record_fill(fill2)

    equity_val = config.capital
    for i, d in enumerate(days):
        equity_val = config.capital + 250.0 * i  # deterministic linear drift
        ts = datetime(d.year, d.month, d.day, 15, 30)
        store.snapshot_equity(ts, equity_val, cash=equity_val * 0.6)

    return store, days, equity_val


def _build_reference_result(config: StrategyConfig, days: pd.DatetimeIndex) -> BacktestResult:
    """A reference backtest over the same calendar dates (midnight
    timestamps, unlike the paper session's 15:30 marks, to exercise the
    date-normalizing join in the report path too)."""
    bars = synthetic_daily("REFIDX", start=days[0].date(), end=days[-1].date(), seed=7)
    bars = bars.iloc[: len(days)]
    ref_equity = config.capital * (bars["close"] / bars["close"].iloc[0])
    ref_equity.index = pd.DatetimeIndex([pd.Timestamp(d.date()) for d in bars.index])
    return BacktestResult(
        config=config,
        engine=EngineMode.EVENT,
        start=ref_equity.index[0].date(),
        end=ref_equity.index[-1].date(),
        capital=config.capital,
        equity=ref_equity,
        gross_equity=ref_equity.copy(),
        trades=[],
        total_costs=0.0,
    )


def test_run_eod_report_with_reference(settings: Settings) -> None:
    config = StrategyConfig(name="eod-report-strat", capital=500_000.0)
    store, days, final_equity = _build_paper_session(settings, config, n_days=10)
    reference = _build_reference_result(config, days)
    conventional = settings.artifacts_dir / "runs" / f"{config.name}-{config.config_hash()}"
    reference.save(conventional)

    positions = [
        Position(symbol="TCS", qty=10, avg_price=3_500.0, last_price=3_550.0),
        Position(symbol="INFY", qty=5, avg_price=1_500.0, last_price=1_490.0),
    ]

    report_path = run_eod(settings, config, store, positions)

    last_day = days[-1].date()
    assert report_path.exists()
    assert report_path.name == f"eod-{last_day.isoformat()}.html"
    assert report_path.stat().st_size > 10_000  # non-trivial: inline plotly.js + tables

    json_path = report_path.with_suffix(".json")
    assert json_path.exists()
    data = json.loads(json_path.read_text())

    assert data["date"] == last_day.isoformat()
    assert data["paper_equity_final"] == pytest.approx(final_equity)
    assert data["n_open_positions"] == 2

    assert data["ref_equity_final"] is not None
    assert data["cum_diff_pct_final"] is not None

    # Cross-check against a fresh, independently built paper result + the
    # same divergence math the report uses internally.
    paper_result = build_paper_result(store, config)
    frame = divergence_frame(paper_result, reference)
    assert data["ref_equity_final"] == pytest.approx(float(reference.equity.iloc[-1]))
    assert data["cum_diff_pct_final"] == pytest.approx(float(frame["cum_diff_pct"].iloc[-1]))

    assert set(_METRIC_KEYS).issubset(data["paper_metrics"].keys())
    assert data["ref_metrics"] is not None
    assert set(_METRIC_KEYS).issubset(data["ref_metrics"].keys())


def test_run_eod_report_reference_none_degrades_gracefully(settings: Settings) -> None:
    """No conventional reference run saved anywhere -> reference=None path:
    the report must still be produced, with the reference/divergence fields
    nulled out rather than raising."""
    config = StrategyConfig(name="eod-report-no-ref", capital=300_000.0)
    store, days, final_equity = _build_paper_session(settings, config, n_days=5)
    positions: list[Position] = []

    report_path = run_eod(settings, config, store, positions)

    assert report_path.exists()
    html = report_path.read_text(encoding="utf-8")
    assert "no reference" in html.lower() or "no reference run" in html.lower()

    json_path = report_path.with_suffix(".json")
    data = json.loads(json_path.read_text())
    assert data["date"] == days[-1].date().isoformat()
    assert data["paper_equity_final"] == pytest.approx(final_equity)
    assert data["ref_equity_final"] is None
    assert data["cum_diff_pct_final"] is None
    assert data["n_open_positions"] == 0
    assert data["ref_metrics"] is None
    assert set(_METRIC_KEYS).issubset(data["paper_metrics"].keys())


def test_write_eod_report_explicit_day_and_positions_table(settings: Settings, tmp_path: Path) -> None:
    """write_eod_report directly: HTML mentions the given day + lists the
    given positions' symbols."""
    config = StrategyConfig(name="eod-write-direct", capital=100_000.0)
    idx = pd.date_range("2024-04-01", periods=6, freq="B")
    equity = pd.Series([100_000.0 + 50.0 * i for i in range(6)], index=idx)
    paper = BacktestResult(
        config=config,
        engine=EngineMode.EVENT,
        start=idx[0].date(),
        end=idx[-1].date(),
        capital=100_000.0,
        equity=equity,
        gross_equity=equity.copy(),
        trades=[],
        total_costs=0.0,
    )
    positions = [Position(symbol="WIPRO", qty=20, avg_price=450.0, last_price=460.0)]
    out_dir = tmp_path / "eod_out"
    day = idx[-1].date()

    html_path = write_eod_report(paper, None, positions, out_dir, day)

    assert html_path == out_dir / f"eod-{day.isoformat()}.html"
    html = html_path.read_text(encoding="utf-8")
    assert day.isoformat() in html
    assert "WIPRO" in html

    json_path = out_dir / f"eod-{day.isoformat()}.json"
    data = json.loads(json_path.read_text())
    assert data["n_open_positions"] == 1
    assert data["ref_equity_final"] is None


def test_build_paper_result_collapses_intraday_snapshots_to_daily(settings: Settings) -> None:
    """A real session writes TWO snapshots per trading day (the 09:15
    day-start risk baseline and the 15:30 close), but BacktestResult /
    compute_metrics treat every equity point as one trading day (252/yr).
    build_paper_result must therefore keep only each day's LAST snapshot
    (original timestamp preserved) — otherwise every annualized metric is
    computed over twice the period count. Review fix, 2026-07-10."""
    from tradingos.analytics.metrics import compute_metrics

    config = StrategyConfig(name="eod-daily-collapse", capital=100_000.0)
    store = PaperStore(settings.paper_db_path, config.name)
    store.ensure_run(config.capital)

    store.snapshot_equity(datetime(2024, 1, 15, 9, 15), 100_000.0, 100_000.0)
    store.snapshot_equity(datetime(2024, 1, 15, 15, 30), 101_000.0, 50_000.0)
    store.snapshot_equity(datetime(2024, 1, 16, 9, 15), 101_000.0, 50_000.0)
    store.snapshot_equity(datetime(2024, 1, 16, 15, 30), 102_010.0, 50_000.0)

    result = build_paper_result(store, config)

    # One point per day: each day's last snapshot, original 15:30 timestamps.
    assert list(result.equity.index) == [
        datetime(2024, 1, 15, 15, 30),
        datetime(2024, 1, 16, 15, 30),
    ]
    assert list(result.equity) == [101_000.0, 102_010.0]
    assert result.start == date(2024, 1, 15)
    assert result.end == date(2024, 1, 16)

    # Metrics see exactly one daily return of 1.0% — not the 09:15/15:30
    # pairs (which would report total_return 2.01% off the 09:15 baseline).
    metrics = compute_metrics(result)
    assert metrics["total_return"] == pytest.approx(102_010.0 / 101_000.0 - 1.0)

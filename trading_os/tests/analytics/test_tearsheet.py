"""Tests for tearsheet.py: plotly_report content/determinism/empty-trades
handling, and quantstats_tearsheet's graceful-degrade contract."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from fixtures.synthetic import synthetic_universe

from tradingos.analytics.tearsheet import plotly_report, quantstats_tearsheet
from tradingos.config.schemas import (
    EngineMode,
    RebalanceSpec,
    ScoreSpec,
    SelectionSpec,
    SignalSpec,
    SizingSpec,
    StrategyConfig,
    UniverseSpec,
)
from tradingos.core.models import Timeframe
from tradingos.engine.base import StaticUniverseResolver
from tradingos.engine.dataview import MarketData
from tradingos.engine.event.engine import EventEngine
from tradingos.engine.result import BacktestResult
from tradingos.strategies.registry import register_signal


@register_signal("test_tearsheet_mom", tier="custom", window=63)
def _mom(df: pd.DataFrame, **params: object) -> pd.Series:
    """Trailing return over ``window`` bars (causal) — test-local signal."""
    window = int(params["window"])
    return df["close"].pct_change(window)


def _run_result() -> BacktestResult:
    """2 synthetic symbols, ~1.5y daily, monthly top-1 momentum — produces a
    handful of trades and (via point_in_time universe resolution with no
    explicit symbol list) the survivorship-bias warning."""
    frames = synthetic_universe(["AAA", "BBB"], start=date(2020, 1, 1), end=date(2021, 6, 30))
    data = MarketData(frames, timeframe=Timeframe.DAY, snapshot_id="tearsheet")
    cfg = StrategyConfig(
        name="tearsheet_test",
        start=date(2020, 1, 1),
        end=date(2021, 6, 30),
        capital=1_000_000,
        universe=UniverseSpec(index="NIFTY500", point_in_time=True),
        signals=[SignalSpec(id="mom", name="test_tearsheet_mom", params={"window": 63})],
        score=ScoreSpec(type="single"),
        selection=SelectionSpec(method="top_n", n=1, exit_rank=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.9),
        rebalance=RebalanceSpec(frequency="monthly", trading_day=1),
    )
    return EventEngine().run(cfg, data, StaticUniverseResolver())


@pytest.fixture(scope="module")
def result() -> BacktestResult:
    res = _run_result()
    # sanity-check the fixture itself is interesting enough for the assertions below
    assert res.trades, "fixture must produce trades"
    assert res.warnings, "fixture must produce a warning"
    return res


def _empty_trades_result() -> BacktestResult:
    idx = pd.date_range(date(2022, 1, 1), periods=60, freq="B")
    equity = pd.Series([1_000_000.0 * (1.0004**i) for i in range(len(idx))], index=idx)
    cfg = StrategyConfig(
        name="fast_engine_run",
        start=date(2022, 1, 1),
        end=idx[-1].date(),
        capital=1_000_000,
        selection=SelectionSpec(method="top_n", n=1, exit_rank=1),
    )
    return BacktestResult(
        config=cfg,
        engine=EngineMode.VECTORIZED,
        start=date(2022, 1, 1),
        end=idx[-1].date(),
        capital=1_000_000,
        equity=equity,
        gross_equity=equity * 1.001,
        trades=[],
        total_costs=1_000.0,
        warnings=["FAST ENGINE: bar-close fills, no order book, no partial fills."],
    )


# ---------------------------------------------------------------------------
# plotly_report
# ---------------------------------------------------------------------------


def test_plotly_report_writes_file(tmp_path: Path, result: BacktestResult) -> None:
    out = plotly_report(result, tmp_path / "report.html")
    assert out == tmp_path / "report.html"
    assert out.exists()
    assert out.stat().st_size > 1000


def test_plotly_report_contains_key_content(tmp_path: Path, result: BacktestResult) -> None:
    out = plotly_report(result, tmp_path / "report.html")
    text = out.read_text(encoding="utf-8")
    assert result.config.name in text
    assert result.warnings[0] in text  # exact warning text, unmissable
    assert "STCG" in text
    assert f"Trades: {len(result.trades)}" in text


def test_plotly_report_is_deterministic(tmp_path: Path, result: BacktestResult) -> None:
    out1 = plotly_report(result, tmp_path / "r1.html")
    out2 = plotly_report(result, tmp_path / "r2.html")
    assert out1.read_bytes() == out2.read_bytes()


def test_plotly_report_empty_trades_renders_explanatory_note(tmp_path: Path) -> None:
    empty_result = _empty_trades_result()
    out = plotly_report(empty_result, tmp_path / "empty.html")
    text = out.read_text(encoding="utf-8")
    assert "No per-trade log" in text
    assert empty_result.warnings[0] in text


# ---------------------------------------------------------------------------
# quantstats_tearsheet: never raises, either writes a file or logs+returns None
# ---------------------------------------------------------------------------


def test_quantstats_tearsheet_never_raises(
    tmp_path: Path, result: BacktestResult, caplog: pytest.LogCaptureFixture
) -> None:
    out_path = tmp_path / "qs.html"
    caplog.set_level("WARNING")
    out = quantstats_tearsheet(result, out_path)
    assert out is None or out == out_path
    if out is None:
        assert any("quantstats" in r.message.lower() for r in caplog.records)
    else:
        assert out.exists()
        assert out.stat().st_size > 0

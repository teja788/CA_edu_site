"""Warm-up / all-NaN score periods must hold cash, on BOTH engines.

Regression: when a score is configured but every candidate's signal is still
NaN (indicator warm-up window), the engines used to fall back to "everyone
scores 0" — silently buying the alphabetically-first names at full weight.
An all-NaN (or otherwise zero-valid-score) rebalance must instead hold cash;
once the signal warms up, trading must resume as normal.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
from fixtures.synthetic import trading_days

from tradingos.config.schemas import (
    ExecutionSpec,
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
from tradingos.engine.vectorized.engine import VectorizedEngine
from tradingos.strategies.registry import register_signal

_CAPITAL = 1_000_000.0


@register_signal("test_warmup_mom", tier="custom", window=5)
def _warmup_mom(df: pd.DataFrame, **params: object) -> pd.Series:
    """Trailing return over ``window`` bars — NaN until warmed up (causal)."""
    return df["close"].pct_change(int(params["window"]))


def _flat_frame(dates: pd.DatetimeIndex, close: float) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": [close] * len(dates),
            "high": [close + 2] * len(dates),
            "low": [close - 2] * len(dates),
            "close": [close] * len(dates),
            "volume": [10_000_000] * len(dates),
        },
        index=dates,
    )


def _data() -> MarketData:
    dates = trading_days(date(2021, 1, 1), date(2021, 1, 14))  # 10 business days
    frames = {
        "AAA": _flat_frame(dates, 100.0),
        "BBB": _flat_frame(dates, 90.0),
        "CCC": _flat_frame(dates, 80.0),
    }
    return MarketData(frames, timeframe=Timeframe.DAY, snapshot_id="warmup")


def _cfg(window: int) -> StrategyConfig:
    return StrategyConfig(
        name="warmup",
        start=date(2021, 1, 1),
        end=date(2021, 1, 31),
        capital=_CAPITAL,
        universe=UniverseSpec(symbols=["AAA", "BBB", "CCC"], point_in_time=False),
        signals=[SignalSpec(id="mom", name="test_warmup_mom", params={"window": window})],
        score=ScoreSpec(type="single"),
        selection=SelectionSpec(method="top_n", n=1, exit_rank=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.9),
        rebalance=RebalanceSpec(frequency="daily"),
        execution=ExecutionSpec(timing="same_close", slippage_bps=0.0, max_participation=1.0),
    )


# ---------------------------------------------------------------------------
# event engine
# ---------------------------------------------------------------------------


def test_event_engine_holds_cash_while_every_score_is_nan() -> None:
    # window 20 > 10 bars of data: the score never becomes valid -> the whole
    # run must be 100% cash, not "buy AAA because it sorts first".
    res = EventEngine().run(_cfg(window=20), _data(), StaticUniverseResolver())
    assert (res.equity == _CAPITAL).all()
    assert res.trades == []
    assert res.total_costs == 0.0


def test_event_engine_trades_only_after_scores_warm_up() -> None:
    # window 5 becomes valid at bar index 5: bars 0-4 are all-NaN -> cash;
    # the first buy lands at bar 5's close (same_close), moving equity by the
    # charges paid.
    res = EventEngine().run(_cfg(window=5), _data(), StaticUniverseResolver())
    assert (res.equity.iloc[:5] == _CAPITAL).all()
    assert res.equity.iloc[5] < _CAPITAL  # invested, net of charges
    assert res.total_costs > 0.0


# ---------------------------------------------------------------------------
# vectorized engine
# ---------------------------------------------------------------------------


def test_vectorized_engine_holds_cash_while_every_score_is_nan() -> None:
    res = VectorizedEngine().run(_cfg(window=20), _data(), StaticUniverseResolver())
    assert (res.equity == _CAPITAL).all()
    assert res.total_costs == 0.0


def test_vectorized_engine_trades_only_after_scores_warm_up() -> None:
    res = VectorizedEngine().run(_cfg(window=5), _data(), StaticUniverseResolver())
    assert (res.equity.iloc[:5] == _CAPITAL).all()
    assert res.equity.iloc[5] < _CAPITAL
    assert res.total_costs > 0.0

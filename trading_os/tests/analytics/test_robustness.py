"""Parameter-neighborhood robustness: discovery, int rounding, invalid rows.

Deterministic, event-engine only, single-symbol synthetic data. The trend signal
(`test_rb_trend`) is registered with a distinctive prefix so it never collides
with the platform registry.
"""

from __future__ import annotations

import math
from datetime import date

import pandas as pd
import pytest
from fixtures.synthetic import trading_days

from tradingos.analytics.robustness import RobustnessResult, perturbation_grid
from tradingos.config.schemas import (
    EngineMode,
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
from tradingos.strategies.registry import register_signal

# Steps chosen so selection.n=1 mostly COLLAPSES (round(1*0.9)=1, round(1*1.1)=1)
# but the 1.5 step pushes n to 2 while exit_rank stays 1 -> an invalid combo.
_STEPS = (0.8, 0.9, 1.1, 1.5)
_WINDOW_PATH = "signals.trend.params.window"


@register_signal("test_rb_trend", tier="custom", window=50)
def _rb_trend(df: pd.DataFrame, **params: object) -> pd.Series:
    """Trailing return over ``window`` bars (causal: row t uses rows <= t)."""
    window = int(params["window"])
    return df["close"].pct_change(window)


def _data() -> MarketData:
    """One symbol on a steady, low-noise uptrend so the base Sharpe is robustly
    positive (needed for the fragility flag to be meaningful)."""
    dates = trading_days(date(2018, 1, 1), date(2019, 4, 30))
    closes = [100.0]
    for i in range(1, len(dates)):
        closes.append(closes[-1] * (1.01 if i % 2 == 0 else 1.004))
    close = pd.Series(closes, index=dates)
    frame = pd.DataFrame(
        {
            "open": close.shift(1).fillna(close.iloc[0]).to_numpy(),
            "high": (close.to_numpy() + 1.0),
            "low": (close.to_numpy() - 1.0),
            "close": close.to_numpy(),
            "volume": [10_000_000] * len(dates),
        },
        index=dates,
    )
    return MarketData({"AAA": frame}, timeframe=Timeframe.DAY, snapshot_id="rb")


def _base() -> StrategyConfig:
    return StrategyConfig(
        name="rb",
        start=date(2018, 1, 1),
        end=date(2019, 4, 30),
        capital=1_000_000.0,
        universe=UniverseSpec(symbols=["AAA"], point_in_time=False),
        signals=[SignalSpec(id="trend", name="test_rb_trend", params={"window": 50})],
        score=ScoreSpec(type="single"),
        # exit_rank tight (==n) so a single up-perturbation of n makes n>exit_rank.
        selection=SelectionSpec(method="top_n", n=1, exit_rank=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.9),
    )


def _grid(**overrides: object) -> RobustnessResult:
    kwargs: dict[str, object] = dict(
        steps=_STEPS, metric="sharpe", engine_mode=EngineMode.EVENT
    )
    kwargs.update(overrides)
    return perturbation_grid(_base(), _data(), StaticUniverseResolver(), **kwargs)


@pytest.fixture(scope="module")
def rb() -> RobustnessResult:
    return _grid()


# --------------------------------------------------------------------------- #
# auto-discovery, row count, int rounding                                      #
# --------------------------------------------------------------------------- #
def test_auto_discovery_and_non_collapsed_row_count(rb: RobustnessResult) -> None:
    # Discovery finds the numeric signal param plus selection.n (and nothing else).
    assert {r.param for r in rb.rows} == {_WINDOW_PATH, "selection.n"}

    window_rows = [r for r in rb.rows if r.param == _WINDOW_PATH]
    n_rows = [r for r in rb.rows if r.param == "selection.n"]

    # window=50 never collapses across the 4 steps -> 4 rows; selection.n=1
    # collapses on 0.8/0.9/1.1 and only survives on 1.5 -> 1 row. Total 5.
    assert len(window_rows) == 4
    assert len(n_rows) == 1
    assert len(rb.rows) == 5


def test_int_rounding_is_applied_to_window(rb: RobustnessResult) -> None:
    by_step = {r.step: r.value for r in rb.rows if r.param == _WINDOW_PATH}
    assert by_step == {0.8: 40, 0.9: 45, 1.1: 55, 1.5: 75}  # round(50*step), >=1
    assert all(isinstance(v, int) for v in by_step.values())


# --------------------------------------------------------------------------- #
# invalid combos are recorded, not raised                                     #
# --------------------------------------------------------------------------- #
def test_selection_n_over_exit_rank_is_recorded_invalid(rb: RobustnessResult) -> None:
    (row,) = [r for r in rb.rows if r.param == "selection.n"]
    assert row.step == 1.5
    assert row.value == 2  # round(1 * 1.5) -> 2, but exit_rank is 1
    assert row.status == "invalid"  # validation failed, NOT raised
    assert math.isnan(row.score)


# --------------------------------------------------------------------------- #
# cliff / fragility bookkeeping                                                #
# --------------------------------------------------------------------------- #
def test_cliff_and_fragility_are_computed_consistently(rb: RobustnessResult) -> None:
    assert math.isfinite(rb.base_score)
    assert rb.base_score > 0  # steady uptrend -> positive base Sharpe

    ok_scores = [r.score for r in rb.rows if r.status == "ok" and math.isfinite(r.score)]
    assert ok_scores  # the window perturbations all ran successfully

    assert rb.cliff == pytest.approx(rb.base_score - min(ok_scores))
    assert rb.is_fragile == (min(ok_scores) < 0.5 * rb.base_score)
    assert rb.worst_param == _WINDOW_PATH  # the only param with finite ok rows
    assert rb.fragility_note == ""  # positive base score -> flag is meaningful


# --------------------------------------------------------------------------- #
# determinism + explicit-params restriction                                   #
# --------------------------------------------------------------------------- #
def test_perturbation_grid_is_deterministic() -> None:
    r1, r2 = _grid(), _grid()
    key = lambda res: [  # noqa: E731
        (r.param, r.step, r.value, r.status, r.score) for r in res.rows
    ]
    assert key(r1) == key(r2)
    assert r1.base_score == r2.base_score
    assert r1.cliff == r2.cliff or (math.isnan(r1.cliff) and math.isnan(r2.cliff))


def test_explicit_params_restrict_the_sweep() -> None:
    res = _grid(params=["selection.n"])
    assert {r.param for r in res.rows} == {"selection.n"}
    assert len(res.rows) == 1  # only the 1.5 step survives the collapse filter
    assert res.rows[0].status == "invalid"

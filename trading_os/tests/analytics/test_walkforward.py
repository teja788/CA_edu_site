"""Walk-forward analysis: tiling, the honesty property, and seam-free stitching.

Deterministic, event-engine only, tiny synthetic data. A test-local momentum
signal (`test_wf_mom`) is registered with a distinctive prefix so it never
collides with the platform's real registry.
"""

from __future__ import annotations

import math
from datetime import date

import pandas as pd
import pytest
from fixtures.synthetic import synthetic_universe

from tradingos.analytics.metrics import compute_metrics
from tradingos.analytics.walkforward import WalkForwardResult, walk_forward
from tradingos.config.gridexpand import expand_grid
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
from tradingos.engine.event.engine import EventEngine
from tradingos.strategies.registry import register_signal

_START = date(2018, 1, 1)
_END = date(2020, 6, 30)  # 652 business days -> 5 windows (200/100), last is partial
_SWEEP = {"signals.mom.params.window": [20, 40]}
_TRAIN_BARS = 200
_TEST_BARS = 100


@register_signal("test_wf_mom", tier="custom", window=20)
def _wf_mom(df: pd.DataFrame, **params: object) -> pd.Series:
    """Trailing return over ``window`` bars (causal: row t uses rows <= t)."""
    window = int(params["window"])
    return df["close"].pct_change(window)


def _data() -> MarketData:
    frames = synthetic_universe(["AAA", "BBB", "CCC"], start=_START, end=_END)
    return MarketData(frames, timeframe=Timeframe.DAY, snapshot_id="wf")


def _base() -> StrategyConfig:
    return StrategyConfig(
        name="wf",
        start=_START,
        end=_END,
        capital=1_000_000.0,
        universe=UniverseSpec(symbols=["AAA", "BBB", "CCC"], point_in_time=False),
        signals=[SignalSpec(id="mom", name="test_wf_mom", params={"window": 20})],
        score=ScoreSpec(type="single"),
        selection=SelectionSpec(method="top_n", n=1, exit_rank=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.9),
    )


@pytest.fixture(scope="module")
def wf() -> WalkForwardResult:
    return walk_forward(
        _base(),
        _SWEEP,
        _data(),
        StaticUniverseResolver(),
        train_bars=_TRAIN_BARS,
        test_bars=_TEST_BARS,
        metric="sharpe",
        engine_mode=EngineMode.EVENT,
    )


# --------------------------------------------------------------------------- #
# window bookkeeping: the calendar is tiled and selection precedes the test    #
# --------------------------------------------------------------------------- #
def test_windows_tile_calendar_and_preserve_the_honesty_gap(wf: WalkForwardResult) -> None:
    windows = wf.windows
    assert len(windows) == 5  # 652 bars, train=200 test=100 -> 5 rolling windows
    assert not any(w.skipped for w in windows)  # every window selects a variant

    for w in windows:
        # THE honesty property: the train span ends strictly before the OOS span.
        assert w.train_end < w.test_start
        assert w.n_train_bars == _TRAIN_BARS

    # Test segments are ordered, contiguous and non-overlapping (they tile).
    for a, b in zip(windows[:-1], windows[1:], strict=True):
        assert a.test_end < b.test_start  # non-overlapping, ordered

    # Every full window carries exactly test_bars; the FINAL one is partial.
    assert all(w.n_test_bars == _TEST_BARS for w in windows[:-1])
    assert 0 < windows[-1].n_test_bars < _TEST_BARS


def test_selected_overrides_are_real_sweep_combos_with_finite_train_scores(
    wf: WalkForwardResult,
) -> None:
    combos = [v.overrides for v in expand_grid(_base(), _SWEEP)]
    assert combos == [
        {"signals.mom.params.window": 20},
        {"signals.mom.params.window": 40},
    ]
    for w in wf.windows:
        assert not w.skipped
        assert w.best_overrides in combos
        assert math.isfinite(w.train_score)
        assert w.best_variant_name.startswith("wf__")


# --------------------------------------------------------------------------- #
# stitching: index tiling, base-capital start, and seam continuity            #
# --------------------------------------------------------------------------- #
def test_oos_equity_index_is_the_concatenated_test_windows(wf: WalkForwardResult) -> None:
    idx = wf.oos_equity.index
    assert idx.is_monotonic_increasing
    assert not idx.has_duplicates
    assert len(idx) == sum(w.n_test_bars for w in wf.windows)
    assert idx[0] == wf.windows[0].test_start
    assert idx[-1] == wf.windows[-1].test_end


def test_stitching_starts_at_capital_and_has_no_seam_jumps(wf: WalkForwardResult) -> None:
    base = _base()
    data = _data()

    # Reconstruct each OOS segment by re-running the recorded winner on its test
    # span, then chain-link returns exactly as walk_forward documents.
    segments: list[pd.Series] = []
    for w in wf.windows:
        assert not w.skipped
        variant = expand_grid(base, {k: [v] for k, v in w.best_overrides.items()})[0]
        cfg = variant.config.model_copy(
            update={"start": w.test_start.date(), "end": w.test_end.date()}
        )
        segments.append(EventEngine().run(cfg, data, StaticUniverseResolver()).equity)

    prev_end = base.capital
    pieces: list[pd.Series] = []
    seam_starts: list[float] = []
    for eq in segments:
        contribution = prev_end * (eq / eq.iloc[0])
        seam_starts.append(float(contribution.iloc[0]))
        pieces.append(contribution)
        prev_end = float(contribution.iloc[-1])
    reconstructed = pd.concat(pieces)

    # The stitched curve equals the independent reconstruction bar for bar.
    pd.testing.assert_series_equal(wf.oos_equity, reconstructed, check_names=False)

    # Starts at base.capital, then compounds the first segment's first return.
    assert wf.oos_equity.iloc[0] == pytest.approx(base.capital)
    first_ret = float(segments[0].iloc[1] / segments[0].iloc[0])
    assert wf.oos_equity.iloc[1] == pytest.approx(base.capital * first_ret)

    # No seam jumps: each segment's first stitched value equals the previous
    # segment's chained end value (segments after the first).
    ends = [float(p.iloc[-1]) for p in pieces]
    for prev_end_val, seam_start in zip(ends[:-1], seam_starts[1:], strict=True):
        assert seam_start == pytest.approx(prev_end_val)


# --------------------------------------------------------------------------- #
# OOS metrics + determinism                                                    #
# --------------------------------------------------------------------------- #
def test_oos_metrics_have_full_key_set_and_finite_sharpe(wf: WalkForwardResult) -> None:
    reference = compute_metrics(EventEngine().run(_base(), _data(), StaticUniverseResolver()))
    assert set(wf.oos_metrics) == set(reference)
    assert math.isfinite(wf.oos_metrics["sharpe"])
    # The stitched curve carries no trades, so trade-derived metrics are NaN.
    assert math.isnan(wf.oos_metrics["hit_rate"])


def test_stitched_result_carries_real_costs_and_gross(wf: WalkForwardResult) -> None:
    """The stitched result must not claim to be costless: it carries the sum of
    the per-window test runs' real costs and their chain-linked gross curve
    (before the fix it stored net-as-gross with total_costs=0.0)."""
    base = _base()
    data = _data()

    # Re-run each recorded winner on its test span to get the true aggregates.
    expected_costs = 0.0
    gross_segments: list[pd.Series] = []
    for w in wf.windows:
        assert not w.skipped
        variant = expand_grid(base, {k: [v] for k, v in w.best_overrides.items()})[0]
        cfg = variant.config.model_copy(
            update={"start": w.test_start.date(), "end": w.test_end.date()}
        )
        res = EventEngine().run(cfg, data, StaticUniverseResolver())
        expected_costs += res.total_costs
        gross_segments.append(res.gross_equity)

    # Aggregate costs are the real per-window test costs, and they are not zero.
    assert wf.oos_total_costs == pytest.approx(round(expected_costs, 2))
    assert wf.oos_total_costs > 0.0
    assert wf.oos_metrics["total_costs_pct"] == pytest.approx(
        wf.oos_total_costs / base.capital
    )
    assert wf.oos_metrics["total_costs_pct"] > 0.0

    # The gross curve is stitched from the segments' own gross curves, exactly
    # like the net curve — same index, chained growth, and (costs being
    # positive) it ends strictly above the net curve.
    assert wf.oos_gross_equity.index.equals(wf.oos_equity.index)
    prev_end = base.capital
    pieces: list[pd.Series] = []
    for g in gross_segments:
        contribution = prev_end * (g / g.iloc[0])
        pieces.append(contribution)
        prev_end = float(contribution.iloc[-1])
    pd.testing.assert_series_equal(
        wf.oos_gross_equity, pd.concat(pieces), check_names=False
    )
    assert wf.oos_gross_equity.iloc[-1] > wf.oos_equity.iloc[-1]
    # And it is genuinely gross, not the net curve relabelled.
    assert not wf.oos_gross_equity.equals(wf.oos_equity)


def test_walk_forward_is_deterministic() -> None:
    kwargs = dict(train_bars=_TRAIN_BARS, test_bars=_TEST_BARS, metric="sharpe",
                  engine_mode=EngineMode.EVENT)
    r1 = walk_forward(_base(), _SWEEP, _data(), StaticUniverseResolver(), **kwargs)
    r2 = walk_forward(_base(), _SWEEP, _data(), StaticUniverseResolver(), **kwargs)

    assert [w.best_overrides for w in r1.windows] == [w.best_overrides for w in r2.windows]
    assert [w.train_score for w in r1.windows] == [w.train_score for w in r2.windows]
    assert [(w.test_start, w.test_end, w.n_test_bars) for w in r1.windows] == [
        (w.test_start, w.test_end, w.n_test_bars) for w in r2.windows
    ]
    pd.testing.assert_series_equal(r1.oos_equity, r2.oos_equity)

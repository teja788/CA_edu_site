"""Regime-conditioned score weights (Goulding-Harvey-Mazzoleni "signal speed").

When the market is risk-off/transitional (regime fraction ``f < 1``) a slow
12-month momentum window is stale, so the weighted_zscore SCORE reweights from a
``"full"`` bucket (used at ``f == 1``) to a ``"reduced"`` bucket. Covered here:

  * adaptive OFF -> targets byte-identical to a config without the field
    (adaptive_weights absent vs explicitly None);
  * f == 1 uses "full", f < 1 uses "reduced": a benchmark engineered to flip the
    gate on a known date, two signals with OPPOSITE cross-sectional rankings, so
    the selected top-N provably changes with the weight set;
  * validation: unknown signal id -> ConfigError; missing "reduced" bucket,
    unknown bucket key, non-finite weight -> ValidationError; config_hash moves
    when adaptive_weights change;
  * the regime fraction is evaluated exactly ONCE per rebalance (spy).
"""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import pytest
from fixtures.synthetic import trading_days
from pydantic import ValidationError

import tradingos.engine.event.strategy_runtime as rt
from tradingos.config.schemas import (
    RegimeSignalSpec,
    RegimeSpec,
    ScoreSpec,
    SelectionSpec,
    SignalSpec,
    SizingSpec,
    StrategyConfig,
    UniverseSpec,
)
from tradingos.core.errors import ConfigError
from tradingos.core.models import Timeframe
from tradingos.core.timeutils import MARKET_CLOSE
from tradingos.engine.base import StaticUniverseResolver
from tradingos.engine.dataview import DataView, MarketData, SignalStore
from tradingos.engine.event.strategy_runtime import (
    _adaptive_score_weights,
    evaluate_targets,
)
from tradingos.strategies.registry import register_signal


# Two signals with intentionally OPPOSITE cross-sectional rankings: `fast` ranks
# by close (high close first), `slow` by -close (low close first).
@register_signal("adaptive_fast", tier="custom")
def _fast_signal(df: pd.DataFrame, **params: object) -> pd.Series:
    return df["close"].astype("float64")


@register_signal("adaptive_slow", tier="custom")
def _slow_signal(df: pd.DataFrame, **params: object) -> pd.Series:
    return (-df["close"]).astype("float64")


def _frame(dates: pd.DatetimeIndex, closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
            "close": closes,
            "volume": [10_000_000] * len(dates),
        },
        index=dates,
    )


# Benchmark path (from test_exposure_overlays): three positive_return signals
# with windows 1/2/3 give f == 1 at idx 3 and f == 2/3 (< 1) at idx 7.
_BENCH_CLOSES = [
    100.0, 101.0, 102.0, 103.0,   # idx 3  -> (+,+,+) -> f = 1
    110.0, 101.0, 102.0, 103.0,   # idx 7  -> (+,+,-) -> f = 2/3
    110.0, 109.0, 100.0, 101.0,   # idx 11 -> (+,-,-) -> f = 1/3
    110.0, 109.0, 108.0, 107.0,   # idx 15 -> (-,-,-) -> f = 0
]

# Constant, distinct tradeable closes -> deterministic ranking.
_TRADE_CLOSES = {"A": 200.0, "B": 190.0, "C": 180.0, "D": 50.0}


def _three_signal_regime(**extra: object) -> RegimeSpec:
    return RegimeSpec(
        symbol="BENCH",
        signals=[
            RegimeSignalSpec(kind="positive_return", params={"window": 1}),
            RegimeSignalSpec(kind="positive_return", params={"window": 2}),
            RegimeSignalSpec(kind="positive_return", params={"window": 3}),
        ],
        **extra,  # type: ignore[arg-type]
    )


def _data() -> tuple[pd.DatetimeIndex, MarketData]:
    dates = trading_days(date(2021, 1, 1), date(2021, 3, 1))[: len(_BENCH_CLOSES)]
    frames = {"BENCH": _frame(dates, _BENCH_CLOSES)}
    for sym, px in _TRADE_CLOSES.items():
        frames[sym] = _frame(dates, [px] * len(dates))
    return dates, MarketData(frames, timeframe=Timeframe.DAY, snapshot_id="adaptive")


def _cfg(*, adaptive: dict[str, dict[str, float]] | None, **overrides: object) -> StrategyConfig:
    base: dict[str, object] = dict(
        name="adaptive",
        universe=UniverseSpec(symbols=["A", "B", "C", "D"], point_in_time=False),
        signals=[
            SignalSpec(id="fast", name="adaptive_fast"),
            SignalSpec(id="slow", name="adaptive_slow"),
        ],
        score=ScoreSpec(type="weighted_zscore", weights={"fast": 1.0}),
        selection=SelectionSpec(method="top_n", n=2),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.9),
        regime=_three_signal_regime(adaptive_weights=adaptive) if adaptive is not None
        else _three_signal_regime(),
    )
    base.update(overrides)
    return StrategyConfig(**base)  # type: ignore[arg-type]


def _dv_at(dates: pd.DatetimeIndex, data: MarketData, idx: int) -> DataView:
    now = datetime.combine(dates[idx].date(), MARKET_CLOSE)
    return DataView(data, SignalStore(data), now)


# ---------------------------------------------------------------------------
# 1. adaptive OFF => byte-identical to a config without the field
# ---------------------------------------------------------------------------


def test_adaptive_none_is_identical_to_field_absent() -> None:
    dates, data = _data()
    absent = _cfg(adaptive=None)  # regime present, adaptive_weights defaults to None
    explicit_none = StrategyConfig.model_validate(
        {**absent.model_dump(mode="json"), "regime": {
            **absent.model_dump(mode="json")["regime"], "adaptive_weights": None}}
    )
    assert absent.config_hash() == explicit_none.config_hash()

    for idx in (3, 7, 11, 15):
        dv = _dv_at(dates, data, idx)
        t_absent = evaluate_targets(
            absent, dv, StaticUniverseResolver(), data, {}, 1_000_000.0, []
        )
        t_none = evaluate_targets(
            explicit_none, dv, StaticUniverseResolver(), data, {}, 1_000_000.0, []
        )
        assert t_absent == t_none, f"adaptive=None diverged from absent at idx {idx}"


# ---------------------------------------------------------------------------
# 2. f == 1 -> "full"; f < 1 -> "reduced"; selected top-N provably flips
# ---------------------------------------------------------------------------


def test_bucket_selection_flips_top_n_on_gate() -> None:
    dates, data = _data()
    adaptive = {"full": {"fast": 1.0}, "reduced": {"slow": 1.0}}
    cfg = _cfg(adaptive=adaptive)

    # f == 1 (idx 3): "full" ranks by close (fast) -> top-2 = A, B.
    dv_full = _dv_at(dates, data, 3)
    t_full = evaluate_targets(cfg, dv_full, StaticUniverseResolver(), data, {}, 1_000_000.0, [])
    assert set(t_full) == {"A", "B"}, "f==1 must use the 'full' (fast) weights"

    # f == 2/3 (idx 7): "reduced" ranks by -close (slow) -> top-2 = D, C.
    dv_red = _dv_at(dates, data, 7)
    t_red = evaluate_targets(cfg, dv_red, StaticUniverseResolver(), data, {}, 1_000_000.0, [])
    assert set(t_red) == {"C", "D"}, "f<1 must use the 'reduced' (slow) weights"

    assert set(t_full) != set(t_red), "the weight set must move the selected names"


def test_full_bucket_matches_plain_fast_and_reduced_matches_plain_slow() -> None:
    """The adaptive result equals a static config using the picked bucket."""
    dates, data = _data()
    cfg_adaptive = _cfg(adaptive={"full": {"fast": 1.0}, "reduced": {"slow": 1.0}})
    cfg_fast = _cfg(adaptive=None, score=ScoreSpec(type="weighted_zscore", weights={"fast": 1.0}))
    cfg_slow = _cfg(adaptive=None, score=ScoreSpec(type="weighted_zscore", weights={"slow": 1.0}))

    dv_full = _dv_at(dates, data, 3)   # f == 1
    assert evaluate_targets(
        cfg_adaptive, dv_full, StaticUniverseResolver(), data, {}, 1_000_000.0, []
    ) == evaluate_targets(
        cfg_fast, dv_full, StaticUniverseResolver(), data, {}, 1_000_000.0, []
    )

    dv_red = _dv_at(dates, data, 7)    # f < 1; the reduced bucket ranks by slow.
    # Compare the SELECTED names (reduced entries are additionally f-scaled by the
    # regime overlay in cfg_adaptive, so share counts differ; the picks do not).
    got = set(evaluate_targets(cfg_adaptive, dv_red, StaticUniverseResolver(), data, {}, 1e6, []))
    want = set(evaluate_targets(cfg_slow, dv_red, StaticUniverseResolver(), data, {}, 1e6, []))
    assert got == want


def test_adaptive_score_weights_helper() -> None:
    aw = {"full": {"fast": 1.0}, "reduced": {"slow": 1.0}}
    cfg = _cfg(adaptive=aw)
    assert _adaptive_score_weights(cfg, 1.0) == {"fast": 1.0}
    assert _adaptive_score_weights(cfg, 0.5) == {"slow": 1.0}
    assert _adaptive_score_weights(cfg, 0.0) == {"slow": 1.0}
    # None when no adaptive weights / no regime fraction.
    assert _adaptive_score_weights(_cfg(adaptive=None), 0.5) is None
    assert _adaptive_score_weights(cfg, None) is None
    assert _adaptive_score_weights(StrategyConfig(name="x"), 1.0) is None


# ---------------------------------------------------------------------------
# 3. validation + config_hash sensitivity
# ---------------------------------------------------------------------------


def test_unknown_signal_id_in_adaptive_weights_raises_config_error() -> None:
    with pytest.raises(ConfigError):
        _cfg(adaptive={"full": {"fast": 1.0}, "reduced": {"ghost": 1.0}})


def test_missing_reduced_bucket_is_validation_error() -> None:
    with pytest.raises(ValidationError):
        RegimeSpec(
            symbol="BENCH",
            signals=[RegimeSignalSpec(kind="above_ma")],
            adaptive_weights={"full": {"fast": 1.0}},
        )


def test_unknown_bucket_key_is_validation_error() -> None:
    with pytest.raises(ValidationError):
        RegimeSpec(
            symbol="BENCH",
            signals=[RegimeSignalSpec(kind="above_ma")],
            adaptive_weights={"full": {"fast": 1.0}, "medium": {"fast": 1.0}},
        )


def test_empty_bucket_and_non_finite_weight_are_validation_errors() -> None:
    with pytest.raises(ValidationError):
        RegimeSpec(
            symbol="BENCH",
            signals=[RegimeSignalSpec(kind="above_ma")],
            adaptive_weights={"full": {}, "reduced": {"fast": 1.0}},
        )
    with pytest.raises(ValidationError):
        RegimeSpec(
            symbol="BENCH",
            signals=[RegimeSignalSpec(kind="above_ma")],
            adaptive_weights={"full": {"fast": float("nan")}, "reduced": {"fast": 1.0}},
        )


def test_config_hash_changes_with_adaptive_weights() -> None:
    base = _cfg(adaptive=None)
    with_aw = _cfg(adaptive={"full": {"fast": 1.0}, "reduced": {"slow": 1.0}})
    assert base.config_hash() != with_aw.config_hash()

    changed = _cfg(adaptive={"full": {"fast": 1.0}, "reduced": {"slow": 0.5, "fast": 0.5}})
    assert changed.config_hash() != with_aw.config_hash()


# ---------------------------------------------------------------------------
# 4. the regime fraction is evaluated exactly ONCE per rebalance
# ---------------------------------------------------------------------------


def test_regime_fraction_evaluated_once_per_rebalance(monkeypatch: pytest.MonkeyPatch) -> None:
    dates, data = _data()
    cfg = _cfg(adaptive={"full": {"fast": 1.0}, "reduced": {"slow": 1.0}})
    dv = _dv_at(dates, data, 7)  # f < 1 -> both consumers (score weights + overlay) active

    calls: list[int] = []
    original = rt._regime_fraction

    def _spy(spec: RegimeSpec, view: DataView) -> float:
        calls.append(1)
        return original(spec, view)

    monkeypatch.setattr(rt, "_regime_fraction", _spy)
    evaluate_targets(cfg, dv, StaticUniverseResolver(), data, {}, 1_000_000.0, [])
    assert len(calls) == 1, "regime fraction must be computed exactly once per rebalance"

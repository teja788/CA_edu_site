"""Portfolio-level exposure overlays: graded asymmetric regime + vol target.

Batch 2 of docs/momentum_research_notes.md. Both overlays scale target weights
at rebalance (after sizing, before integer-share conversion) and are causal
(bars/equity <= the rebalance decision date only). Covered here:

  * graded fraction: 3 benchmark signals -> f in {0, 1/3, 2/3, 1} on known dates;
  * asymmetry: new entries scaled, held positions untouched, f=0 blocks buys,
    a rank-exit still fires while the book is gated;
  * vol target: known-vol equity path -> exposure = min(max, target/sigma);
    warm-up -> max_exposure; never levers above max_exposure;
  * stacking order: vol_target scales the whole book, regime f scales new
    entries additionally;
  * config round-trip + config_hash sensitivity;
  * look-ahead: the regime fraction at t is invariant to future bars.
"""

from __future__ import annotations

import math
from datetime import date, datetime

import numpy as np
import pandas as pd
import pytest
from fixtures.synthetic import trading_days

from tradingos.config.schemas import (
    RegimeSignalSpec,
    RegimeSpec,
    ScoreSpec,
    SelectionSpec,
    SignalSpec,
    SizingSpec,
    StrategyConfig,
    UniverseSpec,
    VolTargetSpec,
)
from tradingos.core.models import Timeframe
from tradingos.core.timeutils import MARKET_CLOSE
from tradingos.engine.base import StaticUniverseResolver
from tradingos.engine.dataview import DataView, MarketData, SignalStore
from tradingos.engine.event.strategy_runtime import (
    _apply_regime,
    _apply_vol_target,
    _regime_fraction,
    _vol_target_exposure,
    evaluate_targets,
)
from tradingos.strategies.registry import register_signal

_TRADING_DAYS_PER_YEAR = 252.0


@register_signal("test_overlay_close", tier="custom")
def _close_signal(df: pd.DataFrame, **params: object) -> pd.Series:
    """Rank by the latest close (causal)."""
    return df["close"].astype("float64")


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


# ---------------------------------------------------------------------------
# benchmark path engineered for f in {1, 2/3, 1/3, 0} using three
# positive_return signals with windows 1, 2, 3. Each eval only looks back 3
# bars, and the 4 eval points sit in separate 4-bar blocks so they never
# interfere. Closes chosen so the trailing 1/2/3-bar returns are:
#   idx 3  -> (+,+,+)  = 3 true -> f = 1
#   idx 7  -> (+,+,-)  = 2 true -> f = 2/3
#   idx 11 -> (+,-,-)  = 1 true -> f = 1/3
#   idx 15 -> (-,-,-)  = 0 true -> f = 0
# ---------------------------------------------------------------------------
_BENCH_CLOSES = [
    100.0, 101.0, 102.0, 103.0,  # idx 0-3 : eval idx3, all-up -> f=1
    110.0, 101.0, 102.0, 103.0,  # idx 4-7 : eval idx7, 103>102,>101,<110 -> f=2/3
    110.0, 109.0, 100.0, 101.0,  # idx 8-11: eval idx11,101>100,<109,<110 -> f=1/3
    110.0, 109.0, 108.0, 107.0,  # idx 12-15: eval idx15, strictly down -> f=0
]
_EVAL_IDX = {3: 1.0, 7: 2.0 / 3.0, 11: 1.0 / 3.0, 15: 0.0}


def _three_signal_regime() -> RegimeSpec:
    return RegimeSpec(
        symbol="BENCH",
        signals=[
            RegimeSignalSpec(kind="positive_return", params={"window": 1}),
            RegimeSignalSpec(kind="positive_return", params={"window": 2}),
            RegimeSignalSpec(kind="positive_return", params={"window": 3}),
        ],
    )


def _bench_dataview(now_idx: int) -> tuple[DataView, pd.DatetimeIndex]:
    dates = trading_days(date(2021, 1, 1), date(2021, 3, 1))[: len(_BENCH_CLOSES)]
    data = MarketData(
        {"BENCH": _frame(dates, _BENCH_CLOSES)},
        timeframe=Timeframe.DAY,
        snapshot_id="overlay-bench",
    )
    now = datetime.combine(dates[now_idx].date(), MARKET_CLOSE)
    return DataView(data, SignalStore(data), now), dates


# ---------------------------------------------------------------------------
# 1. graded fraction transitions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("now_idx,expected_f", sorted(_EVAL_IDX.items()))
def test_regime_fraction_transitions(now_idx: int, expected_f: float) -> None:
    dv, _ = _bench_dataview(now_idx)
    f = _regime_fraction(_three_signal_regime(), dv)
    assert f == pytest.approx(expected_f), f"f at bar {now_idx} should be {expected_f}"


def test_regime_fraction_above_ma_kind_routes_to_index_above_ma() -> None:
    """`above_ma` regime signal must produce the SAME boolean as the
    index_above_ma filter it routes to (shared PIT routing)."""
    dv, _ = _bench_dataview(now_idx=3)
    spec = RegimeSpec(symbol="BENCH", signals=[RegimeSignalSpec(kind="above_ma", params={"window": 3})])
    # index_above_ma(window=3) on the rising 100..103 head is True at idx 3.
    assert _regime_fraction(spec, dv) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 2. asymmetry at the weight level: new scaled, held untouched, f=0 blocks buys
# ---------------------------------------------------------------------------


def test_apply_regime_scales_new_entries_only() -> None:
    dv, _ = _bench_dataview(now_idx=7)  # f = 2/3
    weights = {"HELD": 0.5, "NEW": 0.5}
    out = _apply_regime(
        StrategyConfig(name="t", regime=_three_signal_regime()),
        dv,
        weights,
        current_holdings={"HELD": 100},
    )
    assert out["HELD"] == pytest.approx(0.5), "held weight must be untouched"
    assert out["NEW"] == pytest.approx(0.5 * (2.0 / 3.0)), "new entry scaled by f"


def test_apply_regime_f_zero_zeroes_new_entries_but_not_held() -> None:
    dv, _ = _bench_dataview(now_idx=15)  # f = 0
    out = _apply_regime(
        StrategyConfig(name="t", regime=_three_signal_regime()),
        dv,
        {"HELD": 0.5, "NEW": 0.5},
        current_holdings={"HELD": 100},
    )
    assert out["HELD"] == pytest.approx(0.5)
    assert out["NEW"] == pytest.approx(0.0)


def test_apply_regime_f_one_is_a_noop() -> None:
    dv, _ = _bench_dataview(now_idx=3)  # f = 1
    weights = {"A": 0.4, "B": 0.6}
    out = _apply_regime(
        StrategyConfig(name="t", regime=_three_signal_regime()), dv, weights, current_holdings={}
    )
    assert out == pytest.approx(weights)


# ---------------------------------------------------------------------------
# 3. asymmetry end-to-end through evaluate_targets:
#    held name is NOT sold when f=0, and a rank-exit still fires.
# ---------------------------------------------------------------------------


def _trade_data() -> tuple[pd.DatetimeIndex, MarketData]:
    dates = trading_days(date(2021, 1, 1), date(2021, 3, 1))[: len(_BENCH_CLOSES)]
    # Flat, distinct price levels -> deterministic ranking by close.
    frames = {
        "BENCH": _frame(dates, _BENCH_CLOSES),
        "H1": _frame(dates, [200.0] * len(dates)),  # rank 1
        "N1": _frame(dates, [190.0] * len(dates)),  # rank 2
        "N2": _frame(dates, [180.0] * len(dates)),  # rank 3
        "H2": _frame(dates, [50.0] * len(dates)),   # rank 4
    }
    return dates, MarketData(frames, timeframe=Timeframe.DAY, snapshot_id="overlay-trade")


def _trade_cfg(**overrides: object) -> StrategyConfig:
    base = dict(
        name="overlay_trade",
        universe=UniverseSpec(symbols=["H1", "N1", "N2", "H2"], point_in_time=False),
        signals=[SignalSpec(id="c", name="test_overlay_close")],
        score=ScoreSpec(type="single"),
        selection=SelectionSpec(method="top_n", n=2, exit_rank=3),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.9),
    )
    base.update(overrides)
    return StrategyConfig(**base)  # type: ignore[arg-type]


def test_regime_gate_holds_positions_but_blocks_new_and_exits_by_rank() -> None:
    dates, data = _trade_data()
    # f = 0 at bar idx 15 (benchmark strictly declining).
    now = datetime.combine(dates[15].date(), MARKET_CLOSE)
    dv = DataView(data, SignalStore(data), now)
    cfg = _trade_cfg(regime=_three_signal_regime())

    # Held book: H1 (rank 1, within exit_rank=3 -> retained) and H2 (rank 4,
    # beyond exit_rank -> a rank exit). Selection = [H1, N1]; N1 is a NEW entry.
    targets = evaluate_targets(
        cfg, dv, StaticUniverseResolver(), data, {"H1": 100, "H2": 40}, 1_000_000.0, []
    )

    assert "H1" in targets, "held name inside the exit buffer must NOT be force-sold by the gate"
    assert "H2" not in targets, "a rank-exit must still fire under the gate"
    assert "N1" not in targets and "N2" not in targets, "f=0 must block ALL new buys"


def test_regime_gate_off_lets_new_entries_through() -> None:
    dates, data = _trade_data()
    now = datetime.combine(dates[3].date(), MARKET_CLOSE)  # f = 1
    dv = DataView(data, SignalStore(data), now)
    cfg = _trade_cfg(regime=_three_signal_regime())
    targets = evaluate_targets(cfg, dv, StaticUniverseResolver(), data, {}, 1_000_000.0, [])
    # f=1 -> normal book: top-2 by close = H1, N1.
    assert set(targets) == {"H1", "N1"}


# ---------------------------------------------------------------------------
# 4. vol target: known-vol equity path -> exposure = min(max, target/sigma)
# ---------------------------------------------------------------------------


def _equity_from_returns(returns: list[float], start: float = 100.0) -> pd.Series:
    """Equity curve whose daily pct_change reproduces `returns` exactly."""
    values = [start]
    for r in returns:
        values.append(values[-1] * (1.0 + r))
    idx = trading_days(date(2020, 1, 1), date(2021, 12, 31))[: len(values)]
    return pd.Series(values, index=idx, dtype="float64")


def test_vol_target_exposure_known_answer() -> None:
    # 6 alternating returns -> mean 0. variance(ddof=1) = sum(r^2)/(n-1)
    #   = 6 * 0.05^2 / 5 = 0.015 / 5 = 0.003 ; std = sqrt(0.003) = 0.0547723
    #   annualized = 0.0547723 * sqrt(252) = 0.869482
    #   exposure = min(1.0, 0.12 / 0.869482) = 0.138011
    returns = [0.05, -0.05, 0.05, -0.05, 0.05, -0.05]
    eq = _equity_from_returns(returns)  # 7 observations
    spec = VolTargetSpec(target_annual_vol=0.12, lookback_bars=6, max_exposure=1.0)

    sigma = float(np.std(np.array(returns), ddof=1)) * math.sqrt(_TRADING_DAYS_PER_YEAR)
    expected = min(1.0, 0.12 / sigma)
    assert _vol_target_exposure(spec, eq) == pytest.approx(expected)
    assert _vol_target_exposure(spec, eq) == pytest.approx(0.138011, abs=1e-5)


def test_vol_target_warmup_returns_max_exposure() -> None:
    eq = _equity_from_returns([0.05, -0.05, 0.05])  # 4 observations < lookback 6
    spec = VolTargetSpec(target_annual_vol=0.12, lookback_bars=6, max_exposure=0.9)
    assert _vol_target_exposure(spec, eq) == 0.9


def test_vol_target_never_levers_above_max_exposure() -> None:
    # Tiny vol -> target/sigma >> 1; the min() must cap at max_exposure.
    returns = [0.0001, -0.0001] * 4  # 8 returns, sigma ~ 0.0016 annualized
    eq = _equity_from_returns(returns)
    assert _vol_target_exposure(
        VolTargetSpec(target_annual_vol=0.12, lookback_bars=8, max_exposure=1.0), eq
    ) == 1.0
    assert _vol_target_exposure(
        VolTargetSpec(target_annual_vol=0.12, lookback_bars=8, max_exposure=0.8), eq
    ) == 0.8


def test_vol_target_zero_vol_returns_max_exposure() -> None:
    eq = _equity_from_returns([0.0] * 8)  # flat -> sigma 0 -> no scaling
    assert _vol_target_exposure(
        VolTargetSpec(target_annual_vol=0.12, lookback_bars=6, max_exposure=1.0), eq
    ) == 1.0


def test_apply_vol_target_scales_all_weights_symmetrically() -> None:
    returns = [0.05, -0.05, 0.05, -0.05, 0.05, -0.05]
    eq = _equity_from_returns(returns)
    # equity_history = all but the last point; the last equity value is `equity`.
    hist = {ts: v for ts, v in eq.iloc[:-1].items()}
    equity = float(eq.iloc[-1])
    now = eq.index[-1]
    spec = VolTargetSpec(target_annual_vol=0.12, lookback_bars=6, max_exposure=1.0)
    cfg = StrategyConfig(name="t", vol_target=spec)

    out = _apply_vol_target(cfg, {"A": 0.5, "B": 0.5}, equity, hist, now)
    exposure = _vol_target_exposure(spec, eq)
    assert out["A"] == pytest.approx(0.5 * exposure)
    assert out["B"] == pytest.approx(0.5 * exposure)  # SAME factor -> symmetric


# ---------------------------------------------------------------------------
# 5. stacking order: vol_target scales whole book, regime f scales new only
# ---------------------------------------------------------------------------


def test_stacking_vol_target_times_regime_on_new_entries() -> None:
    dates, data = _trade_data()
    now = datetime.combine(dates[7].date(), MARKET_CLOSE)  # regime f = 2/3
    dv = DataView(data, SignalStore(data), now)

    # A synthetic equity history so vol_target produces a < 1 exposure. Use a
    # realistic capital scale so integer-share conversion doesn't floor to zero
    # (exposure is scale-invariant). hist = all but the last point; the last
    # equity value is `equity`, so the overlay's series reconstructs eq exactly.
    returns = [0.05, -0.05, 0.05, -0.05, 0.05, -0.05]
    eq = _equity_from_returns(returns, start=10_000_000.0)
    hist = {ts: v for ts, v in eq.iloc[:-1].items()}
    equity = float(eq.iloc[-1])
    vt = VolTargetSpec(target_annual_vol=0.12, lookback_bars=6, max_exposure=1.0)

    # Held H1 (retained), new N1 selected. Book = [H1, N1], base weight 0.5 each.
    holdings = {"H1": 100}

    # (a) vol_target ONLY: both held and new scaled by the same exposure.
    cfg_vt = _trade_cfg(vol_target=vt)
    only_vt = evaluate_targets(
        cfg_vt, dv, StaticUniverseResolver(), data, holdings, equity, [], equity_history=hist
    )

    # (b) both stacked: held scaled by exposure, new scaled by exposure * f.
    cfg_both = _trade_cfg(vol_target=vt, regime=_three_signal_regime())
    both = evaluate_targets(
        cfg_both, dv, StaticUniverseResolver(), data, holdings, equity, [], equity_history=hist
    )

    # Held qty is identical (regime never touches held positions).
    assert both["H1"] == only_vt["H1"]
    # New-entry qty ratio equals the regime fraction f = 2/3 (both share the
    # vol_target exposure, so it cancels in the ratio).
    assert both["N1"] / only_vt["N1"] == pytest.approx(2.0 / 3.0, rel=1e-2)


# ---------------------------------------------------------------------------
# 6. config round-trip + config_hash sensitivity
# ---------------------------------------------------------------------------


def test_config_roundtrip_with_regime_and_vol_target() -> None:
    cfg = StrategyConfig(
        name="stacked",
        regime=_three_signal_regime(),
        vol_target=VolTargetSpec(target_annual_vol=0.12, lookback_bars=126, max_exposure=1.0),
    )
    dumped = cfg.model_dump(mode="json")
    restored = StrategyConfig.model_validate(dumped)
    assert restored.regime is not None and restored.vol_target is not None
    assert restored.regime.symbol == "BENCH"
    assert len(restored.regime.signals) == 3
    assert restored.vol_target.target_annual_vol == 0.12
    assert restored.config_hash() == cfg.config_hash()


def test_config_hash_changes_when_overlay_specs_change() -> None:
    base = StrategyConfig(name="s", regime=_three_signal_regime())
    no_regime = StrategyConfig(name="s")
    assert base.config_hash() != no_regime.config_hash()

    with_vt = StrategyConfig(
        name="s",
        regime=_three_signal_regime(),
        vol_target=VolTargetSpec(target_annual_vol=0.12),
    )
    assert with_vt.config_hash() != base.config_hash()

    changed_vol = StrategyConfig(
        name="s",
        regime=_three_signal_regime(),
        vol_target=VolTargetSpec(target_annual_vol=0.15),
    )
    assert changed_vol.config_hash() != with_vt.config_hash()


def test_regime_requires_at_least_one_signal() -> None:
    with pytest.raises(ValueError):
        RegimeSpec(symbol="BENCH", signals=[])


def test_vol_target_max_exposure_capped_at_one() -> None:
    with pytest.raises(ValueError):
        VolTargetSpec(target_annual_vol=0.12, max_exposure=1.5)


# ---------------------------------------------------------------------------
# 7. look-ahead: the regime fraction at t is invariant to future bars
# ---------------------------------------------------------------------------


def test_regime_fraction_is_invariant_to_future_bars() -> None:
    """Altering bars strictly AFTER the decision date must not change f at t
    (PIT discipline). Altering a bar <= t MUST change it (sanity)."""
    dates = trading_days(date(2021, 1, 1), date(2021, 3, 1))[: len(_BENCH_CLOSES)]
    now_idx = 7  # f = 2/3
    now = datetime.combine(dates[now_idx].date(), MARKET_CLOSE)
    spec = _three_signal_regime()

    base = _frame(dates, _BENCH_CLOSES)
    data_a = MarketData({"BENCH": base}, timeframe=Timeframe.DAY, snapshot_id="la-a")
    f_a = _regime_fraction(spec, DataView(data_a, SignalStore(data_a), now))

    # mutate every bar AFTER now to absurd values -> f at `now` unchanged.
    future = _BENCH_CLOSES.copy()
    for i in range(now_idx + 1, len(future)):
        future[i] = 9_999.0
    data_b = MarketData(
        {"BENCH": _frame(dates, future)}, timeframe=Timeframe.DAY, snapshot_id="la-b"
    )
    f_b = _regime_fraction(spec, DataView(data_b, SignalStore(data_b), now))
    assert f_b == pytest.approx(f_a), "future bars leaked into the regime fraction at t"

    # sanity: mutating a bar <= now DOES move f (the signal actually reads it).
    past = _BENCH_CLOSES.copy()
    past[now_idx] = 50.0  # crash the decision bar -> all trailing returns negative
    data_c = MarketData(
        {"BENCH": _frame(dates, past)}, timeframe=Timeframe.DAY, snapshot_id="la-c"
    )
    f_c = _regime_fraction(spec, DataView(data_c, SignalStore(data_c), now))
    assert f_c == pytest.approx(0.0)

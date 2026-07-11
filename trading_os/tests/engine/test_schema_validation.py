"""Config-schema bounds: every numeric/date/enum field rejects nonsense loudly.

Regression for a batch of validation gaps: capital <= 0, start > end,
trading_day = 0 (which silently rebalanced the LAST day of the period),
max_participation = 0 (nothing would ever fill), unbounded haircut/slippage/
weights/lookbacks, etc. Each case below failed to raise before the fix.
"""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from tradingos.config.schemas import (
    CostSpec,
    DelistingSpec,
    ExecutionSpec,
    FilterSpec,
    GridSpec,
    OverlaySpec,
    RebalanceSpec,
    ScoreSpec,
    SelectionSpec,
    SizingSpec,
    StrategyConfig,
    UniverseSpec,
)


def _cfg(**overrides: object) -> StrategyConfig:
    base: dict[str, object] = {"name": "bounds"}
    base.update(overrides)
    return StrategyConfig(**base)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# StrategyConfig: capital, dates, name
# ---------------------------------------------------------------------------


def test_capital_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        _cfg(capital=0)
    with pytest.raises(ValidationError):
        _cfg(capital=-100_000)
    assert _cfg(capital=1).capital == 1


def test_start_after_end_rejected() -> None:
    with pytest.raises(ValidationError):
        _cfg(start=date(2021, 2, 1), end=date(2021, 1, 1))
    # equal start/end (single-day window) stays legal
    assert _cfg(start=date(2021, 1, 1), end=date(2021, 1, 1)).start == date(2021, 1, 1)


def test_blank_strategy_name_rejected() -> None:
    with pytest.raises(ValidationError):
        StrategyConfig(name="   ")


# ---------------------------------------------------------------------------
# RebalanceSpec: trading_day
# ---------------------------------------------------------------------------


def test_trading_day_zero_or_negative_rejected() -> None:
    # trading_day=0 used to silently rebalance the LAST day of the period.
    with pytest.raises(ValidationError):
        RebalanceSpec(trading_day=0)
    with pytest.raises(ValidationError):
        RebalanceSpec(trading_day=-3)
    assert RebalanceSpec(trading_day=1).trading_day == 1


# ---------------------------------------------------------------------------
# ExecutionSpec: max_participation, slippage_bps
# ---------------------------------------------------------------------------


def test_max_participation_bounds() -> None:
    with pytest.raises(ValidationError):
        ExecutionSpec(max_participation=0.0)  # nothing would ever fill
    with pytest.raises(ValidationError):
        ExecutionSpec(max_participation=-0.05)
    with pytest.raises(ValidationError):
        ExecutionSpec(max_participation=1.5)
    assert ExecutionSpec(max_participation=1.0).max_participation == 1.0


def test_slippage_bps_bounds() -> None:
    with pytest.raises(ValidationError):
        ExecutionSpec(slippage_bps=-1.0)
    with pytest.raises(ValidationError):
        ExecutionSpec(slippage_bps=20_000.0)  # > 100%
    assert ExecutionSpec(slippage_bps=0.0).slippage_bps == 0.0
    assert ExecutionSpec(slippage_bps=None).slippage_bps is None


# ---------------------------------------------------------------------------
# DelistingSpec: haircut
# ---------------------------------------------------------------------------


def test_haircut_pct_bounds() -> None:
    with pytest.raises(ValidationError):
        DelistingSpec(haircut_pct=-0.1)
    with pytest.raises(ValidationError):
        DelistingSpec(haircut_pct=1.5)
    assert DelistingSpec(haircut_pct=0.0).haircut_pct == 0.0
    assert DelistingSpec(haircut_pct=1.0).haircut_pct == 1.0


# ---------------------------------------------------------------------------
# SelectionSpec: n, percentile, exit_rank
# ---------------------------------------------------------------------------


def test_selection_n_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        SelectionSpec(n=0)
    with pytest.raises(ValidationError):
        SelectionSpec(n=-5)


def test_percentile_bounds_and_required_for_top_percentile() -> None:
    with pytest.raises(ValidationError):
        SelectionSpec(method="top_percentile", percentile=0.0)
    with pytest.raises(ValidationError):
        SelectionSpec(method="top_percentile", percentile=1.5)
    with pytest.raises(ValidationError):
        SelectionSpec(method="top_percentile")  # percentile missing
    assert SelectionSpec(method="top_percentile", percentile=0.2).percentile == 0.2


def test_exit_rank_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        SelectionSpec(n=1, exit_rank=0)


# ---------------------------------------------------------------------------
# SizingSpec: weights, lookbacks, method-specific params
# ---------------------------------------------------------------------------


def test_max_position_pct_bounds() -> None:
    with pytest.raises(ValidationError):
        SizingSpec(max_position_pct=0.0)
    with pytest.raises(ValidationError):
        SizingSpec(max_position_pct=1.5)
    assert SizingSpec(max_position_pct=1.0).max_position_pct == 1.0


def test_max_sector_pct_bounds() -> None:
    with pytest.raises(ValidationError):
        SizingSpec(max_sector_pct=0.0)
    with pytest.raises(ValidationError):
        SizingSpec(max_sector_pct=1.2)


def test_vol_lookback_days_needs_two_returns() -> None:
    with pytest.raises(ValidationError):
        SizingSpec(vol_lookback_days=1)
    with pytest.raises(ValidationError):
        SizingSpec(vol_lookback_days=0)


def test_volatility_target_requires_positive_target_vol() -> None:
    with pytest.raises(ValidationError):
        SizingSpec(method="volatility_target")  # target_vol missing
    with pytest.raises(ValidationError):
        SizingSpec(method="volatility_target", target_vol=0.0)
    with pytest.raises(ValidationError):
        SizingSpec(method="volatility_target", target_vol=-0.15)
    assert SizingSpec(method="volatility_target", target_vol=0.15).target_vol == 0.15


def test_fixed_fractional_requires_fraction_in_unit_interval() -> None:
    with pytest.raises(ValidationError):
        SizingSpec(method="fixed_fractional")  # fraction missing
    with pytest.raises(ValidationError):
        SizingSpec(method="fixed_fractional", fraction=0.0)
    with pytest.raises(ValidationError):
        SizingSpec(method="fixed_fractional", fraction=1.5)
    assert SizingSpec(method="fixed_fractional", fraction=0.1).fraction == 0.1


# ---------------------------------------------------------------------------
# UniverseSpec: liquidity filter, symbols, index
# ---------------------------------------------------------------------------


def test_min_median_traded_value_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        UniverseSpec(min_median_traded_value=0.0)
    with pytest.raises(ValidationError):
        UniverseSpec(min_median_traded_value=-1.0)


def test_liquidity_lookback_days_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        UniverseSpec(liquidity_lookback_days=0)


def test_empty_symbol_list_rejected() -> None:
    # an empty explicit list means "no candidates, ever" — reject it loudly
    with pytest.raises(ValidationError):
        UniverseSpec(symbols=[])
    assert UniverseSpec(symbols=None).symbols is None


def test_blank_index_rejected() -> None:
    with pytest.raises(ValidationError):
        UniverseSpec(index="  ")


# ---------------------------------------------------------------------------
# ScoreSpec: weights must be finite and not all zero
# ---------------------------------------------------------------------------


def test_all_zero_weights_rejected() -> None:
    with pytest.raises(ValidationError):
        ScoreSpec(type="weighted_zscore", weights={"a": 0.0, "b": 0.0})


def test_non_finite_weight_rejected() -> None:
    with pytest.raises(ValidationError):
        ScoreSpec(type="weighted_zscore", weights={"a": float("inf")})
    with pytest.raises(ValidationError):
        ScoreSpec(type="weighted_zscore", weights={"a": float("nan")})
    # negative weights stay legal (e.g. penalising volatility)
    assert ScoreSpec(type="weighted_zscore", weights={"a": -0.3, "b": 0.7}).weights["a"] == -0.3


# ---------------------------------------------------------------------------
# CostSpec / component names / GridSpec
# ---------------------------------------------------------------------------


def test_stcg_tax_rate_bounds() -> None:
    with pytest.raises(ValidationError):
        CostSpec(stcg_tax_rate=-0.1)
    with pytest.raises(ValidationError):
        CostSpec(stcg_tax_rate=1.0)
    assert CostSpec(stcg_tax_rate=0.20).stcg_tax_rate == 0.20


def test_blank_cost_schedule_rejected() -> None:
    with pytest.raises(ValidationError):
        CostSpec(schedule="  ")


def test_blank_filter_and_overlay_names_rejected() -> None:
    with pytest.raises(ValidationError):
        FilterSpec(name=" ")
    with pytest.raises(ValidationError):
        OverlaySpec(name="")


def test_gridspec_bounds() -> None:
    with pytest.raises(ValidationError):
        GridSpec(name="  ", base=_cfg())
    with pytest.raises(ValidationError):
        GridSpec(name="g", base=_cfg(), max_parallel=-1)
    assert GridSpec(name="g", base=_cfg(), max_parallel=0).max_parallel == 0

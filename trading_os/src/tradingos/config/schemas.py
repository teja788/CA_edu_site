"""Pydantic schemas for strategy / experiment YAML configs.

A strategy is fully declarative: it references registered components by name.
Adding a new strategy must never require touching engine code.
"""

from __future__ import annotations

import enum
import hashlib
import json
import math
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from tradingos.core.models import Product, Timeframe


class EngineMode(enum.StrEnum):
    VECTORIZED = "vectorized"  # vectorbt: fast, bar-close approximations
    EVENT = "event"  # custom event-driven: realistic fills


class UniverseSpec(BaseModel):
    """Which stocks are candidates. Point-in-time index membership by default."""

    index: str = "NIFTY500"
    point_in_time: bool = True
    # explicit symbol list overrides index membership (for tests / small runs).
    # An EMPTY list would mean "no candidates, ever" — rejected loudly.
    symbols: list[str] | None = Field(default=None, min_length=1)
    # liquidity filter: minimum median daily traded value in rupees over lookback
    min_median_traded_value: float | None = Field(default=None, gt=0)
    liquidity_lookback_days: int = Field(default=63, ge=1)

    @field_validator("index")
    @classmethod
    def _index_non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("universe index must be non-blank")
        return v


class SignalSpec(BaseModel):
    """One indicator/signal instance: registry name + params.

    `id` is how the score/filters refer to it. `timeframe` allows cross-timeframe
    use (e.g. daily indicator consumed by an intraday strategy)."""

    id: str
    name: str  # registered signal name, e.g. "rsi", "return_over_window"
    params: dict[str, Any] = Field(default_factory=dict)
    timeframe: Timeframe = Timeframe.DAY

    @field_validator("id", "name")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must be non-empty")
        return v


class ScoreSpec(BaseModel):
    """Combine signal values into one ranking score. Default: weighted z-scores
    (cross-sectional z-score of each signal at each rebalance, then weighted sum)."""

    type: Literal["weighted_zscore", "single"] = "weighted_zscore"
    weights: dict[str, float] = Field(default_factory=dict)  # signal id -> weight

    @model_validator(mode="after")
    def _check_weights(self) -> ScoreSpec:
        if self.type == "weighted_zscore" and not self.weights:
            raise ValueError("weighted_zscore score requires non-empty weights")
        for sig_id, w in self.weights.items():
            if not math.isfinite(w):
                raise ValueError(f"score weight for {sig_id!r} must be finite, got {w}")
        # Negative weights are legal (penalising a factor); ALL-zero is a no-op
        # score that would silently rank by symbol name — reject it.
        if self.weights and all(w == 0.0 for w in self.weights.values()):
            raise ValueError("score weights must not all be zero")
        return self


class FilterSpec(BaseModel):
    """Regime/eligibility filter, referenced by registered name."""

    name: str
    params: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def _name_non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("filter name must be non-blank")
        return v


class SelectionSpec(BaseModel):
    """Top-N with an exit buffer to reduce churn: enter while rank <= n,
    hold until rank > exit_rank."""

    method: Literal["top_n", "top_percentile"] = "top_n"
    n: int = Field(default=25, ge=1)
    percentile: float | None = Field(default=None, gt=0, le=1)
    exit_rank: int | None = Field(default=None, ge=1)  # default: same as n (no buffer)

    @model_validator(mode="after")
    def _defaults(self) -> SelectionSpec:
        if self.method == "top_percentile" and self.percentile is None:
            raise ValueError("top_percentile selection requires percentile in (0, 1]")
        if self.exit_rank is None:
            self.exit_rank = self.n
        if self.exit_rank < self.n:
            raise ValueError("exit_rank must be >= n (buffer zone)")
        return self


class SizingSpec(BaseModel):
    method: Literal[
        "equal_weight", "inverse_volatility", "volatility_target", "fixed_fractional"
    ] = "equal_weight"
    # volatility_target: annualized portfolio vol target (e.g. 0.15)
    target_vol: float | None = Field(default=None, gt=0)
    fraction: float | None = Field(default=None, gt=0, le=1)  # fixed_fractional
    vol_lookback_days: int = Field(default=63, ge=2)  # a vol needs >= 2 returns
    max_position_pct: float = Field(default=0.10, gt=0, le=1)
    max_sector_pct: float | None = Field(default=None, gt=0, le=1)

    @model_validator(mode="after")
    def _method_params(self) -> SizingSpec:
        if self.method == "volatility_target" and self.target_vol is None:
            raise ValueError("volatility_target sizing requires target_vol > 0")
        if self.method == "fixed_fractional" and self.fraction is None:
            raise ValueError("fixed_fractional sizing requires fraction in (0, 1]")
        return self


class RebalanceSpec(BaseModel):
    frequency: Literal["daily", "weekly", "monthly", "quarterly", "event"] = "monthly"
    # Nth trading day of the period (1-based; 0 used to silently mean the LAST
    # day of the period via negative indexing — rejected now)
    trading_day: int = Field(default=1, ge=1)


class OverlaySpec(BaseModel):
    """Risk overlay, e.g. trailing stops, portfolio kill switch."""

    name: str  # e.g. "trailing_stop_atr", "trailing_stop_pct", "portfolio_drawdown_stop"
    params: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def _name_non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("overlay name must be non-blank")
        return v


class ExecutionSpec(BaseModel):
    """When signals become orders. Look-ahead guarantee: signals from data up to
    and including bar T affect orders executed at T+1 open (default)."""

    timing: Literal["next_open", "same_close"] = "next_open"
    # None -> cost schedule defaults by liquidity tier; 10_000 bps == 100%
    slippage_bps: float | None = Field(default=None, ge=0, le=10_000)
    # partial fills above this fraction of bar volume; 0 would never fill anything
    max_participation: float = Field(default=0.05, gt=0, le=1)


class CostSpec(BaseModel):
    schedule: str = "zerodha_2026"
    product: Product = Product.CNC
    stcg_tax_rate: float = Field(default=0.20, ge=0, lt=1)  # informational line in reports

    @field_validator("schedule")
    @classmethod
    def _schedule_non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("cost schedule must be non-blank")
        return v


class DelistingSpec(BaseModel):
    """If a held stock is delisted/suspended: exit at last traded price minus haircut."""

    haircut_pct: float = Field(default=0.20, ge=0, le=1)


class StrategyConfig(BaseModel):
    name: str
    description: str = ""
    timeframe: Timeframe = Timeframe.DAY
    engine: EngineMode = EngineMode.EVENT
    start: date | None = None
    end: date | None = None
    capital: float = Field(default=1_000_000.0, gt=0)

    @field_validator("name")
    @classmethod
    def _name_non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("strategy name must be non-blank")
        return v

    @model_validator(mode="after")
    def _window_ordered(self) -> StrategyConfig:
        if self.start is not None and self.end is not None and self.start > self.end:
            raise ValueError(f"start {self.start} is after end {self.end}")
        return self

    universe: UniverseSpec = Field(default_factory=UniverseSpec)
    signals: list[SignalSpec] = Field(default_factory=list)
    score: ScoreSpec | None = None
    filters: list[FilterSpec] = Field(default_factory=list)
    selection: SelectionSpec = Field(default_factory=SelectionSpec)
    sizing: SizingSpec = Field(default_factory=SizingSpec)
    rebalance: RebalanceSpec = Field(default_factory=RebalanceSpec)
    overlays: list[OverlaySpec] = Field(default_factory=list)
    execution: ExecutionSpec = Field(default_factory=ExecutionSpec)
    costs: CostSpec = Field(default_factory=CostSpec)
    delisting: DelistingSpec = Field(default_factory=DelistingSpec)

    @model_validator(mode="after")
    def _signal_ids_unique(self) -> StrategyConfig:
        ids = [s.id for s in self.signals]
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate signal ids in {self.name}")
        if self.score is not None:
            unknown = set(self.score.weights) - set(ids)
            if unknown:
                raise ValueError(f"score references unknown signal ids: {sorted(unknown)}")
        return self

    def config_hash(self) -> str:
        """Stable hash for reproducibility tracking in the experiments DB."""
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


class GridSpec(BaseModel):
    """Experiment grid: a base strategy plus parameter sweeps.

    `sweep` maps dotted config paths to lists of values, e.g.
    ``{"signals.mom.params.window": [126, 189, 252], "selection.n": [20, 25, 30]}``.
    Signal params are addressed as ``signals.<signal_id>.params.<key>``."""

    name: str
    base: StrategyConfig
    sweep: dict[str, list[Any]] = Field(default_factory=dict)
    engine: EngineMode = EngineMode.VECTORIZED
    max_parallel: int = Field(default=0, ge=0)  # 0 -> cpu_count

    @field_validator("name")
    @classmethod
    def _name_non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("grid name must be non-blank")
        return v

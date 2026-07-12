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

from tradingos.core.errors import ConfigError
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
    # Dynamic traded-value universe: rank the `symbols` POOL by trailing median
    # close*volume each rebalance and keep the top `dynamic_top_n`. This is a
    # point-in-time-safe alternative to index membership for pools that have no
    # historical constituent table (e.g. a broad NSE list). It composes with
    # `min_median_traded_value` (that threshold is applied downstream, as usual)
    # and is MUTUALLY EXCLUSIVE with index/point-in-time membership — see
    # `_check_dynamic`. When set, `symbols` is the candidate pool.
    dynamic_top_n: int | None = Field(default=None, ge=1)
    # trailing window (bars) for the rank metric; also the seasoning minimum.
    rank_lookback: int = Field(default=126, ge=1)
    # listing-age gate: the rank metric is masked to NaN until a symbol has this
    # many bars of history. Defaults to `rank_lookback` when unset; if set it
    # must be >= `rank_lookback` (a shorter gate would be a no-op).
    min_history: int | None = Field(default=None, ge=1)

    @field_validator("index")
    @classmethod
    def _index_non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("universe index must be non-blank")
        return v

    @model_validator(mode="after")
    def _check_dynamic(self) -> UniverseSpec:
        """Gate the dynamic-universe knobs (raises ConfigError on bad combos).

        `dynamic_top_n` derives candidates by ranking an explicit pool, so it
        needs `symbols` and cannot also resolve from an index / point-in-time
        membership table. `min_history` must not undercut `rank_lookback`.
        """
        if self.dynamic_top_n is None:
            return self  # the other knobs are inert without dynamic_top_n
        if self.symbols is None:
            raise ConfigError(
                "universe.dynamic_top_n requires an explicit `symbols` pool to "
                "rank; it cannot derive candidates from index membership"
            )
        if self.point_in_time:
            raise ConfigError(
                "universe.dynamic_top_n is incompatible with point-in-time index "
                "membership; set point_in_time: false (the dynamic rank IS the "
                "point-in-time universe here)"
            )
        if self.min_history is not None and self.min_history < self.rank_lookback:
            raise ConfigError(
                f"universe.min_history ({self.min_history}) must be >= "
                f"rank_lookback ({self.rank_lookback})"
            )
        return self


class SignalSpec(BaseModel):
    """One indicator/signal instance: registry name + params.

    `id` is how the score/filters refer to it. `timeframe` allows cross-timeframe
    use (e.g. daily indicator consumed by an intraday strategy).

    `benchmark` (optional) names a second symbol whose close the engine joins
    onto the traded symbol's frame as a `benchmark_close` column — aligned on
    the frame's index, NaN where the benchmark has no bar, and causal (the
    joined value at row t is the benchmark's bar at ts <= that row's ts) —
    before the signal function is called. Signals that need a benchmark frame
    (e.g. `residual_momentum`, which regresses the stock on the index) declare
    it here; signals without `benchmark` see no change to their input frame."""

    id: str
    name: str  # registered signal name, e.g. "rsi", "return_over_window"
    params: dict[str, Any] = Field(default_factory=dict)
    timeframe: Timeframe = Timeframe.DAY
    benchmark: str | None = None  # second-frame routing (see docstring)

    @field_validator("id", "name")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must be non-empty")
        return v

    @field_validator("benchmark")
    @classmethod
    def _benchmark_non_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("benchmark, when set, must be a non-blank symbol")
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


class RegimeSignalSpec(BaseModel):
    """One benchmark regime signal, evaluated on the RegimeSpec's benchmark frame.

    ``kind`` selects a causal boolean indicator; ``params`` are its knobs:
      * ``above_ma``        -> ``window`` (SMA length; default 200)
      * ``positive_return`` -> ``window`` (trailing-return lookback in bars, e.g. 252)
      * ``supertrend``      -> ``period`` (ATR length; default 10),
                               ``multiplier`` (band width in ATRs; default 3.0).
                               An ATR-adaptive fast trend flag — flips quicker
                               than a fixed SMA in volatility spikes.
    """

    kind: Literal["above_ma", "positive_return", "supertrend"]
    params: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_window(self) -> RegimeSignalSpec:
        window = self.params.get("window")
        if window is not None and (not isinstance(window, int) or window < 1):
            raise ValueError(f"regime signal window must be a positive int, got {window!r}")
        period = self.params.get("period")
        if period is not None and (not isinstance(period, int) or period < 1):
            raise ValueError(f"regime signal period must be a positive int, got {period!r}")
        multiplier = self.params.get("multiplier")
        if multiplier is not None and (
            not isinstance(multiplier, (int, float)) or multiplier <= 0
        ):
            raise ValueError(
                f"regime signal multiplier must be a positive number, got {multiplier!r}"
            )
        return self


class RegimeSpec(BaseModel):
    """Graded, asymmetric regime exposure (engine overlay, not a strategy).

    At each rebalance the engine evaluates every ``signals`` entry on the
    ``symbol`` benchmark frame (point-in-time, via the same routing the
    ``index_above_ma`` regime filter uses) and forms the fraction
    ``f = (# true) / (# signals)``. ``f`` scales NEW entries only — held
    positions keep their normal target weight and are never force-sold
    (they still exit via exit_rank / normal rebalance mechanics). ``f == 0``
    blocks all new buys; the freed capital stays in cash.
    """

    symbol: str
    signals: list[RegimeSignalSpec] = Field(min_length=1)
    mode: Literal["graded_asymmetric"] = "graded_asymmetric"

    @field_validator("symbol")
    @classmethod
    def _symbol_non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("regime benchmark symbol must be non-blank")
        return v


class VolTargetSpec(BaseModel):
    """Portfolio-level volatility targeting (Barroso & Santa-Clara 2015).

    At each rebalance the engine scales the WHOLE book's target weights by
    ``exposure = min(max_exposure, target_annual_vol / sigma_hat)`` where
    ``sigma_hat`` is the annualized std of the strategy's OWN net daily equity
    returns over the trailing ``lookback_bars`` bars. Long-only cash overlay:
    de-lever only (``max_exposure <= 1``), never lever up; remainder is cash.
    During warm-up (< ``lookback_bars`` equity observations) exposure is
    ``max_exposure`` (no scaling).
    """

    target_annual_vol: float = Field(gt=0)  # e.g. 0.12
    lookback_bars: int = Field(default=126, ge=2)  # a vol needs >= 2 returns
    max_exposure: float = Field(default=1.0, gt=0, le=1)  # de-lever only


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
    # portfolio-level exposure overlays (engine capabilities, not strategies).
    # When both are set the vol-target exposure scales the whole book and the
    # regime fraction additionally scales new entries — see strategy_runtime.
    regime: RegimeSpec | None = None
    vol_target: VolTargetSpec | None = None
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

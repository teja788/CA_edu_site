"""Parameter-neighborhood robustness — the "performance cliff" defense.

A backtest that only looks good at one exact parameter tuple is overfit: the
honest question is whether performance survives SMALL perturbations of each
parameter. This module answers it with a ONE-AT-A-TIME neighborhood sweep (not a
cartesian grid): every perturbable parameter is nudged multiplicatively through
``steps`` while all others stay at their base value, so each row isolates one
parameter's sensitivity.

Design guarantees:

* **No dotted-path setting is re-implemented.** Every perturbed config is built
  through :func:`tradingos.config.gridexpand.expand_grid` with a single
  ``{path: [value]}`` sweep, so it runs the exact same pydantic validation a
  hand-written YAML would. A combo that fails validation (e.g. ``selection.n``
  pushed above ``exit_rank``) is RECORDED as ``status="invalid"`` with a NaN
  score — never raised, never silently skipped, so the sweep's row count stays
  faithful.
* **Auto-discovery is causal and total.** When ``params is None`` every NUMERIC
  (int/float; bool excluded) value in each signal's ``params`` dict is
  discovered as ``signals.<id>.params.<key>``, plus ``selection.n``. A caller may
  instead pass explicit dotted paths to restrict the sweep.
* **Integer parameters stay integers.** An int base value perturbs to
  ``round(original * step)`` clamped to ``>= 1``; a step that collapses back onto
  the base value (e.g. ``2 * 0.9 = 1.8 -> 2``) is skipped so it is not double-
  counted as the base. Float parameters perturb to ``original * step``.
* **The sweep survives engine failures.** An engine exception for one variant
  becomes ``status="error"`` with a NaN score; the remaining variants still run.

The fragility flag mirrors the spec's performance-cliff rule: with a positive
base score, the strategy ``is_fragile`` when the worst surviving neighbor earns
less than half the base score. When the base score is <= 0 or NaN the flag is not
meaningful (you cannot halve a non-positive edge), so it is forced ``False`` and
``fragility_note`` explains why.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from tradingos.analytics.metrics import compute_metrics
from tradingos.config.gridexpand import expand_grid
from tradingos.config.schemas import EngineMode, StrategyConfig
from tradingos.core.errors import ConfigError
from tradingos.core.logging import get_logger
from tradingos.engine import EventEngine, VectorizedEngine
from tradingos.engine.base import UniverseResolver
from tradingos.engine.dataview import MarketData
from tradingos.engine.result import BacktestResult

logger = get_logger(__name__)

_DEFAULT_STEPS: tuple[float, ...] = (0.8, 0.9, 1.1, 1.2)


@dataclass
class PerturbationRow:
    """One neighborhood point: which parameter, the multiplicative step, the
    resulting value, its metric score, and how the run resolved.

    ``status`` is ``"ok"`` (ran, metric computed), ``"invalid"`` (the perturbed
    config failed validation) or ``"error"`` (the engine raised).
    """

    param: str
    step: float
    value: Any
    score: float
    status: str  # "ok" | "invalid" | "error"


@dataclass
class RobustnessResult:
    """Base score plus the one-at-a-time neighborhood and its fragility verdict."""

    base_score: float
    rows: list[PerturbationRow]
    worst_param: str | None
    cliff: float
    is_fragile: bool
    fragility_note: str
    metric: str


def _make_engine(mode: EngineMode) -> EventEngine | VectorizedEngine:
    """Map an :class:`EngineMode` to a fresh engine instance (vectorbt stays
    lazy, so EVENT-mode callers never import it)."""
    if mode == EngineMode.EVENT:
        return EventEngine()
    if mode == EngineMode.VECTORIZED:
        return VectorizedEngine()
    raise ConfigError(f"unsupported engine mode {mode!r}")


def _read_dotted(config: StrategyConfig, path: str) -> Any:
    """Read the current value at a dotted config ``path``.

    Mirrors the addressing in :func:`tradingos.config.gridexpand` (writes go
    through ``expand_grid``; only reads are done here): ``signals.<id>....``
    matches the SignalSpec by its ``id`` (not list position); every other path
    walks nested mappings key by key.
    """
    dump = config.model_dump(mode="python")
    parts = path.split(".")
    if not all(parts):
        raise ConfigError(f"malformed param path {path!r}")

    node: Any = dump
    if parts[0] == "signals":
        if len(parts) < 3:
            raise ConfigError(f"param path {path!r} must be signals.<id>.<field...>")
        sig_id = parts[1]
        matches = [s for s in dump.get("signals", []) if s.get("id") == sig_id]
        if not matches:
            known = [s.get("id") for s in dump.get("signals", [])]
            raise ConfigError(f"param path {path!r}: no signal with id {sig_id!r} (have {known})")
        node = matches[0]
        parts = parts[2:]

    for key in parts:
        if not isinstance(node, dict) or key not in node:
            raise ConfigError(f"param path {path!r}: {key!r} does not exist in the config")
        node = node[key]
    return node


def _discover_params(config: StrategyConfig) -> list[str]:
    """Auto-discover perturbable numeric parameters, sorted deterministically.

    Every int/float (bool excluded — ``isinstance(True, int)`` is True, so bools
    are filtered first) value in each signal's ``params`` dict becomes
    ``signals.<id>.params.<key>``; ``selection.n`` is always included.
    """
    paths: set[str] = {"selection.n"}
    for sig in config.signals:
        for key, val in sig.params.items():
            if isinstance(val, bool):
                continue
            if isinstance(val, (int, float)):
                paths.add(f"signals.{sig.id}.params.{key}")
    return sorted(paths)


def _perturbed_value(original: Any, step: float) -> tuple[Any, bool]:
    """Derive the perturbed value and whether it COLLAPSED onto the base value.

    Int -> ``round(original * step)`` clamped to ``>= 1``; collapses (skip) if it
    equals the original. Float -> ``original * step`` (never treated as a
    collapse). Bools/non-numerics are rejected loudly — they are not perturbable.
    """
    if isinstance(original, bool):
        raise ConfigError(f"cannot perturb a boolean parameter (value {original!r})")
    if isinstance(original, int):
        value = max(1, round(original * step))
        return value, value == original
    if isinstance(original, float):
        return original * step, False
    raise ConfigError(f"cannot perturb non-numeric parameter (value {original!r})")


def perturbation_grid(
    config: StrategyConfig,
    data: MarketData,
    universe: UniverseResolver,
    *,
    steps: tuple[float, ...] = _DEFAULT_STEPS,
    params: list[str] | None = None,
    metric: str = "sharpe",
    engine_mode: EngineMode = EngineMode.EVENT,
) -> RobustnessResult:
    """Run a one-at-a-time parameter-neighborhood robustness sweep.

    Parameters
    ----------
    config
        The base strategy whose neighborhood is probed.
    data, universe
        Market data and universe resolver, passed unchanged to every run.
    steps
        Multiplicative perturbation factors applied to each parameter.
    params
        Explicit dotted paths to perturb; when ``None`` they are auto-discovered
        (numeric signal params + ``selection.n``).
    metric
        Metric key from :func:`compute_metrics` used to score every run.
    engine_mode
        Which engine to run every simulation on.

    Returns
    -------
    RobustnessResult
        The base score, one row per (param, step) neighborhood point in
        deterministic order (params sorted, steps in the given order), the worst
        parameter, the performance cliff and the fragility verdict.
    """
    engine = _make_engine(engine_mode)
    param_list = sorted(params) if params is not None else _discover_params(config)

    base_score = _score_of(engine.run(config, data, universe), metric)

    total = len(param_list) * len(steps)
    logger.info(
        "robustness: up to %d perturbations (%d params x %d steps) + 1 base run on "
        "the %s engine (metric=%s, base_score=%.4f)",
        total,
        len(param_list),
        len(steps),
        engine_mode.value,
        metric,
        base_score,
    )

    rows: list[PerturbationRow] = []
    for path in param_list:
        original = _read_dotted(config, path)
        for step in steps:
            value, collapsed = _perturbed_value(original, step)
            if collapsed:
                continue  # int perturbation landed back on the base value
            rows.append(_run_one(engine, config, data, universe, path, step, value, metric))

    ok_scores = [r.score for r in rows if r.status == "ok" and math.isfinite(r.score)]
    worst_param = _worst_param(rows)
    cliff = (
        base_score - min(ok_scores)
        if (ok_scores and math.isfinite(base_score))
        else math.nan
    )
    is_fragile, fragility_note = _fragility(base_score, ok_scores)

    return RobustnessResult(
        base_score=base_score,
        rows=rows,
        worst_param=worst_param,
        cliff=cliff,
        is_fragile=is_fragile,
        fragility_note=fragility_note,
        metric=metric,
    )


def _run_one(
    engine: EventEngine | VectorizedEngine,
    config: StrategyConfig,
    data: MarketData,
    universe: UniverseResolver,
    path: str,
    step: float,
    value: Any,
    metric: str,
) -> PerturbationRow:
    """Build (via expand_grid), run and score ONE perturbation.

    A validation failure -> ``invalid``; an engine exception -> ``error``. Either
    way the row carries a NaN score and the caller's sweep continues.
    """
    try:
        variant = expand_grid(config, {path: [value]})[0]
    except ConfigError:
        return PerturbationRow(param=path, step=step, value=value, score=math.nan, status="invalid")
    try:
        result = engine.run(variant.config, data, universe)
        score = _score_of(result, metric)
    except Exception:  # noqa: BLE001 — any engine failure must not kill the sweep
        logger.exception("robustness: engine failed for %s=%s (step %s)", path, value, step)
        return PerturbationRow(param=path, step=step, value=value, score=math.nan, status="error")
    return PerturbationRow(param=path, step=step, value=value, score=score, status="ok")


def _score_of(result: BacktestResult, metric: str) -> float:
    """The single selection metric for a result, validating the metric name."""
    metrics = compute_metrics(result)
    if metric not in metrics:
        raise ConfigError(f"unknown metric {metric!r}; available: {sorted(metrics)}")
    return float(metrics[metric])


def _worst_param(rows: list[PerturbationRow]) -> str | None:
    """The parameter whose worst (lowest) finite ok-score is the lowest overall.

    Only ``ok`` rows with finite scores count; ``None`` when none qualify.
    """
    worst_by_param: dict[str, float] = {}
    for r in rows:
        if r.status != "ok" or not math.isfinite(r.score):
            continue
        cur = worst_by_param.get(r.param)
        if cur is None or r.score < cur:
            worst_by_param[r.param] = r.score
    if not worst_by_param:
        return None
    # Deterministic on ties: lowest score first, then param name.
    return min(worst_by_param, key=lambda p: (worst_by_param[p], p))


def _fragility(base_score: float, ok_scores: list[float]) -> tuple[bool, str]:
    """The performance-cliff verdict and (when not meaningful) an explanation.

    Fragile iff ``base_score > 0`` and the worst surviving neighbor earns
    ``< 0.5 * base_score``. For a non-positive or NaN base score the halving test
    is meaningless, so the flag is ``False`` and the note says why.
    """
    if math.isnan(base_score):
        return False, "base_score is NaN; the performance-cliff flag is not meaningful"
    if base_score <= 0:
        return (
            False,
            f"base_score {base_score:.4f} <= 0; the >50%-drawdown-of-edge cliff test "
            "is only meaningful for a positive base score",
        )
    if not ok_scores:
        return False, "no perturbation produced a finite ok score; fragility could not be assessed"
    return (min(ok_scores) < 0.5 * base_score), ""


__all__ = [
    "PerturbationRow",
    "RobustnessResult",
    "perturbation_grid",
]

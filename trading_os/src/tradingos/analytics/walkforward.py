"""Walk-forward analysis — rolling out-of-sample parameter selection.

This is an OVERFITTING DEFENSE, so out-of-sample honesty is the entire point.
The one property that makes a walk-forward result trustworthy is that the
parameter chosen for a test segment is selected using ONLY data that precedes
that segment. We enforce that structurally, not by convention:

* The window calendar is ``data.union_index()`` clipped to ``[base.start,
  base.end]`` with the engines' own semantics (start inclusive; end via a strict
  ``< end + 1 day`` bound).
* Rolling contiguous windows tile the calendar: window ``k`` **trains** on bars
  ``[k*test_bars, k*test_bars + train_bars)`` and **tests** on the next
  ``test_bars`` bars; the step equals ``test_bars`` so the test segments tile
  with no gap and no overlap.
* For each window every sweep variant is scored on the TRAIN segment only; the
  single winner is then re-run on the TEST segment. The test run happens strictly
  after selection and can never feed back into it — ``train_end < test_start`` for
  every window (asserted in the tests via window bookkeeping).

**No look-ahead from full-history warm-up.** The engines always see each symbol's
full OHLCV frame and precompute signals over all of it, then slice every read
through ``DataView``'s visibility cutoff at each bar ``t``. Data that lies BEFORE
a window's start is PAST relative to that window and is exactly the warm-up a
trailing indicator needs — it is *not* a leak. Data that lies after a window's
end exists in the frame but is never visible during that window's run because the
run's calendar stops at the window end. Do not "fix" the full-frame warm-up: it
is correct.

**Stitching (levels are discarded, returns are chained).** Each test segment is a
fresh backtest that starts from ``base.capital``, so segment equity *levels* are
not continuable across windows — only the bar-to-bar *returns* are. Segment ``i``
contributes ``prev_end * (seg_i / seg_i.iloc[0])`` to a single OOS curve, where
``prev_end`` is the stitched end-value of the previous segment (``base.capital``
for the first). The first bar of each segment therefore lands exactly on the
previous segment's chained end (no seam jump); because each test run restarts
from cash, that first bar is genuinely flat, so this loses no real return.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from tradingos.analytics.metrics import compute_metrics
from tradingos.config.gridexpand import GridVariant, expand_grid
from tradingos.config.schemas import EngineMode, StrategyConfig
from tradingos.core.errors import ConfigError
from tradingos.core.logging import get_logger
from tradingos.engine import EventEngine, VectorizedEngine
from tradingos.engine.base import UniverseResolver
from tradingos.engine.dataview import MarketData
from tradingos.engine.result import BacktestResult

logger = get_logger(__name__)


@dataclass
class WalkForwardWindow:
    """Bookkeeping for one rolling window: the train span, the OOS test span, the
    variant selected on train, and the metrics that variant then earned on test.

    ``train_end < test_start`` always holds — that gap IS the honesty property.
    """

    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    n_train_bars: int
    n_test_bars: int
    best_overrides: dict
    best_variant_name: str
    train_score: float
    test_metrics: dict[str, float]
    skipped: bool = False
    reason: str = ""


@dataclass
class WalkForwardResult:
    """Full walk-forward output: per-window records plus the stitched OOS curve.

    Cost honesty: ``oos_total_costs`` is the REAL aggregate — the sum of the
    per-window test runs' ``total_costs`` (each test run starts from
    ``base.capital``, so the rupee figures are on a common scale) — and
    ``oos_gross_equity`` is the test runs' gross (pre-cost) curves chain-linked
    exactly like ``oos_equity``. When a test run does not provide a gross curve
    aligned to its net curve, ``oos_gross_equity`` is an EMPTY series — gross is
    explicitly unavailable, never fabricated from the net curve.
    """

    windows: list[WalkForwardWindow]
    oos_equity: pd.Series
    oos_metrics: dict[str, float]
    metric: str
    oos_gross_equity: pd.Series = field(default_factory=lambda: pd.Series(dtype="float64"))
    oos_total_costs: float = 0.0


def _make_engine(mode: EngineMode) -> EventEngine | VectorizedEngine:
    """Map an :class:`EngineMode` to a fresh engine instance.

    Importing ``VectorizedEngine`` does NOT import vectorbt (the heavy numba
    import stays lazy inside ``run``), so this is safe to call for EVENT-mode
    runs that never touch the vectorized path.
    """
    if mode == EngineMode.EVENT:
        return EventEngine()
    if mode == EngineMode.VECTORIZED:
        return VectorizedEngine()
    raise ConfigError(f"unsupported engine mode {mode!r}")


def _clip_calendar(
    union: pd.DatetimeIndex, start: date | None, end: date | None
) -> pd.DatetimeIndex:
    """Clip a union index to ``[start, end]`` with the engines' exact semantics.

    ``start`` is inclusive; ``end`` uses a strict ``< end + 1 day`` bound so a bar
    stamped anywhere ON the end date is kept but a bar dated ``end + 1`` never is.
    """
    cal = union
    if start is not None:
        cal = cal[cal >= pd.Timestamp(start)]
    if end is not None:
        cal = cal[cal < pd.Timestamp(end) + pd.Timedelta(days=1)]
    return cal.sort_values()


def _window_slices(
    calendar: pd.DatetimeIndex, train_bars: int, test_bars: int
) -> list[tuple[pd.DatetimeIndex, pd.DatetimeIndex]]:
    """Rolling (train_idx, test_idx) pairs that tile ``calendar``.

    Window ``k`` trains on ``[k*test_bars, k*test_bars + train_bars)`` and tests on
    the next ``test_bars`` bars; step is ``test_bars``. A window is generated only
    when its train span is complete AND its test span is non-empty
    (``k*test_bars + train_bars < len(calendar)``). The final test span may be
    PARTIAL (fewer than ``test_bars`` remaining) — real OOS data is never thrown
    away — and its true bar count is recorded via ``len(test_idx)``.
    """
    n = len(calendar)
    slices: list[tuple[pd.DatetimeIndex, pd.DatetimeIndex]] = []
    k = 0
    while k * test_bars + train_bars < n:
        train_lo = k * test_bars
        train_hi = train_lo + train_bars  # exclusive
        test_lo = train_hi
        test_hi = min(test_lo + test_bars, n)  # partial final window clamps here
        slices.append((calendar[train_lo:train_hi], calendar[test_lo:test_hi]))
        k += 1
    return slices


def _score_of(result: BacktestResult, metric: str) -> tuple[float, dict[str, float]]:
    """Full metric dict for a result plus the single selection score.

    Raises loudly if ``metric`` is not a real metric key (a config error, not a
    silent NaN that would look like a degenerate score).
    """
    metrics = compute_metrics(result)
    if metric not in metrics:
        raise ConfigError(
            f"unknown metric {metric!r}; available: {sorted(metrics)}"
        )
    return float(metrics[metric]), metrics


def _stitch(segments: list[pd.Series], capital: float) -> pd.Series:
    """Chain-link each test segment's returns onto one OOS curve from ``capital``.

    Segment ``i`` contributes ``prev_end * (seg / seg.iloc[0])`` (its own level is
    discarded; only its normalized growth is used). ``prev_end`` starts at
    ``capital`` and becomes each contribution's last value, so consecutive
    segments join with no seam jump. The concatenated index is the tiling of the
    test-window bar timestamps (strictly increasing, no overlaps).
    """
    if not segments:
        return pd.Series(dtype="float64")
    pieces: list[pd.Series] = []
    prev_end = float(capital)
    for eq in segments:
        base0 = float(eq.iloc[0])
        if math.isfinite(base0) and base0 != 0.0:
            growth = eq / base0
        else:  # degenerate segment start -> treat as flat rather than divide by 0
            growth = pd.Series(1.0, index=eq.index)
        contribution = prev_end * growth
        pieces.append(contribution)
        prev_end = float(contribution.iloc[-1])
    return pd.concat(pieces)


def walk_forward(
    base: StrategyConfig,
    sweep: dict[str, list],
    data: MarketData,
    universe: UniverseResolver,
    *,
    train_bars: int = 756,
    test_bars: int = 252,
    metric: str = "sharpe",
    engine_mode: EngineMode = EngineMode.EVENT,
) -> WalkForwardResult:
    """Rolling walk-forward: pick each window's parameters on train, score on test.

    Parameters
    ----------
    base
        The base strategy; ``base.start``/``base.end`` clip the window calendar.
    sweep
        Dotted-path -> value-list parameter grid (see
        :func:`tradingos.config.gridexpand.expand_grid`). Expanded ONCE, in the
        grid's deterministic variant order.
    data, universe
        Market data and the universe resolver, passed unchanged to every run.
    train_bars, test_bars
        Rolling window lengths in bars. The step equals ``test_bars`` so the test
        segments tile the calendar contiguously.
    metric
        The metric key from :func:`compute_metrics` used for selection AND
        reported OOS scoring (e.g. ``"sharpe"``). NaN scores are excluded from
        selection.
    engine_mode
        Which engine to run every train and test simulation on.

    Returns
    -------
    WalkForwardResult
        Per-window records, the stitched OOS equity curve, and the OOS metrics of
        that curve. Trade-derived OOS metrics are NaN by construction (the
        stitched curve carries no trades) and that is correct.
    """
    variants: list[GridVariant] = expand_grid(base, sweep)
    calendar = _clip_calendar(data.union_index(), base.start, base.end)
    slices = _window_slices(calendar, train_bars, test_bars)
    engine = _make_engine(engine_mode)

    n_windows = len(slices)
    n_variants = len(variants)
    logger.info(
        "walk-forward: %d windows x %d variants = %d train runs (+ up to %d test "
        "runs) on the %s engine (metric=%s, train_bars=%d, test_bars=%d)",
        n_windows,
        n_variants,
        n_windows * n_variants,
        n_windows,
        engine_mode.value,
        metric,
        train_bars,
        test_bars,
    )

    windows: list[WalkForwardWindow] = []
    oos_segments: list[pd.Series] = []
    oos_gross_segments: list[pd.Series] = []
    gross_available = True
    oos_total_costs = 0.0

    for train_idx, test_idx in slices:
        train_start, train_end = train_idx[0], train_idx[-1]
        test_start, test_end = test_idx[0], test_idx[-1]

        # --- SELECT on train only: score every variant, pick the best ---------
        best_i: int | None = None
        best_score = -math.inf
        for i, variant in enumerate(variants):
            train_cfg = variant.config.model_copy(
                update={"start": train_start.date(), "end": train_end.date()}
            )
            result = engine.run(train_cfg, data, universe)
            score, _ = _score_of(result, metric)
            if math.isnan(score):
                continue
            # Strict '>' keeps the earlier variant on a tie -> deterministic order.
            if best_i is None or score > best_score:
                best_i, best_score = i, score

        if best_i is None:
            windows.append(
                WalkForwardWindow(
                    train_start=train_start,
                    train_end=train_end,
                    test_start=test_start,
                    test_end=test_end,
                    n_train_bars=len(train_idx),
                    n_test_bars=len(test_idx),
                    best_overrides={},
                    best_variant_name="",
                    train_score=math.nan,
                    test_metrics={},
                    skipped=True,
                    reason=f"all {n_variants} variants scored NaN on the train window",
                )
            )
            continue

        # --- TEST the winner (selection is already frozen) --------------------
        winner = variants[best_i]
        test_cfg = winner.config.model_copy(
            update={"start": test_start.date(), "end": test_end.date()}
        )
        test_result = engine.run(test_cfg, data, universe)
        _, test_metrics = _score_of(test_result, metric)

        if len(test_result.equity) >= 1:
            oos_segments.append(test_result.equity)
            oos_total_costs += float(test_result.total_costs)
            gross = test_result.gross_equity
            if gross is not None and len(gross) and gross.index.equals(test_result.equity.index):
                oos_gross_segments.append(gross)
            else:  # no aligned gross for this segment -> gross is unavailable overall
                gross_available = False

        windows.append(
            WalkForwardWindow(
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
                n_train_bars=len(train_idx),
                n_test_bars=len(test_idx),
                best_overrides=dict(winner.overrides),
                best_variant_name=winner.config.name,
                train_score=best_score,
                test_metrics=test_metrics,
                skipped=False,
                reason="",
            )
        )

    oos_equity = _stitch(oos_segments, base.capital)
    if gross_available:
        oos_gross_equity = _stitch(oos_gross_segments, base.capital)
    else:
        logger.warning(
            "walk-forward: a test segment carried no gross curve aligned to its "
            "net curve; the stitched gross curve is marked unavailable (empty)"
        )
        oos_gross_equity = pd.Series(dtype="float64")
    oos_total_costs = round(oos_total_costs, 2)
    oos_metrics = _oos_metrics(oos_equity, oos_gross_equity, oos_total_costs, base, engine_mode)

    return WalkForwardResult(
        windows=windows,
        oos_equity=oos_equity,
        oos_metrics=oos_metrics,
        metric=metric,
        oos_gross_equity=oos_gross_equity,
        oos_total_costs=oos_total_costs,
    )


def _oos_metrics(
    oos_equity: pd.Series,
    oos_gross_equity: pd.Series,
    oos_total_costs: float,
    base: StrategyConfig,
    engine_mode: EngineMode,
) -> dict[str, float]:
    """Metrics of the stitched OOS curve via a minimal synthetic BacktestResult.

    ``trades=[]`` so trade-derived metrics (hit_rate, turnover, exposure, ...) are
    NaN — the stitched curve has no trade ledger, and that is documented as
    correct, not a bug. ``total_costs`` and ``gross_equity`` carry the REAL
    aggregates from the test runs (so e.g. ``total_costs_pct`` is honest);
    ``gross_equity`` is the possibly-empty stitched gross curve, never a copy of
    the net curve masquerading as gross.
    """
    if len(oos_equity):
        start = oos_equity.index[0].date()
        end = oos_equity.index[-1].date()
    else:
        start = base.start or date(1970, 1, 1)
        end = base.end or start
    synthetic = BacktestResult(
        config=base,
        engine=engine_mode,
        start=start,
        end=end,
        capital=base.capital,
        equity=oos_equity,
        gross_equity=oos_gross_equity,
        trades=[],
        total_costs=oos_total_costs,
        warnings=["walk-forward stitched out-of-sample curve; trades not carried"],
        meta={"kind": "walk_forward_oos"},
    )
    return compute_metrics(synthetic)


__all__ = [
    "WalkForwardWindow",
    "WalkForwardResult",
    "walk_forward",
]

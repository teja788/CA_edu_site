"""Declarative strategy pipeline, evaluated at a single rebalance timestamp.

Given a :class:`~tradingos.engine.dataview.DataView` bound to ``now`` (the
rebalancing bar's 15:30 close) this module turns a
:class:`~tradingos.config.schemas.StrategyConfig` into a set of **target share
holdings**. It reads ONLY through the DataView, so every value it consumes is
point-in-time safe by construction.

Pipeline (each stage documented inline):

    candidates  (UniverseResolver.resolve, intersected with available data)
      -> delisting exclusion     (frame ended before the run's final bar -> out)
      -> liquidity filter        (median close*volume >= min_median_traded_value)
      -> per-signal latest values (dv.signal)
      -> score                   (weighted cross-sectional z, or single raw value)
      -> regime / eligibility filters (symbol-routed => whole book to cash)
      -> selection               (top-N with an exit-rank buffer)
      -> sizing                  (target rupee weights -> integer share targets)

Cross-sectional z uses population std (ddof=0); std==0 -> z=0; any symbol with a
NaN signal is dropped before ranking — and when a score is configured but NO
candidate has a valid value yet (warm-up), the whole book holds cash. Integer
share targets use the last visible close: ``qty = floor(weight * equity / close)``.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from tradingos.config.schemas import SizingSpec, StrategyConfig
from tradingos.core.errors import ConfigError
from tradingos.core.logging import get_logger
from tradingos.engine.base import UniverseResolver
from tradingos.engine.dataview import DataView, MarketData
from tradingos.strategies.registry import get_filter

logger = get_logger(__name__)

_TRADING_DAYS_PER_YEAR = 252.0


def evaluate_targets(
    config: StrategyConfig,
    dv: DataView,
    resolver: UniverseResolver,
    data: MarketData,
    current_holdings: dict[str, int],
    equity: float,
    warnings: list[str],
    run_end: pd.Timestamp | None = None,
) -> dict[str, int]:
    """Return desired holdings ``{symbol: share_qty}`` for this rebalance.

    An empty dict means "hold no positions" — either nothing qualified or a
    symbol-routed regime filter gated the whole book to cash.

    ``run_end`` (backtests only; the final bar of the simulation calendar)
    enables delisting exclusion: a symbol whose frame ends before the run does
    is dropped from the candidate set from its last bar onward, so a frozen
    final score can neither re-buy a delisted name nor hog a top-N slot.
    """
    # -- candidates ---------------------------------------------------------
    resolved = resolver.resolve(config.universe, dv.now.date(), data)
    available = set(data.symbols)
    candidates = sorted(s for s in resolved if s in available)
    candidates = _exclude_delisted(candidates, data, dv.now, run_end)
    if not candidates:
        return {}

    # -- liquidity filter ---------------------------------------------------
    candidates = _liquidity_filter(config, dv, candidates)
    if not candidates:
        return {}

    # -- signal values + score ---------------------------------------------
    if config.score is None:
        # No score configured is legal (e.g. a single-symbol trend strategy):
        # every candidate scores 0 and selection falls back to symbol order.
        scores = {s: 0.0 for s in candidates}
    else:
        scores = _score(config, dv, candidates)  # excludes NaN-signal symbols
        if not scores:
            # A score IS configured but not one candidate has a valid value
            # (indicator warm-up window): hold cash. Falling back to zeros
            # here used to buy the alphabetically-first names at full weight.
            return {}

    # -- regime / eligibility filters --------------------------------------
    eligible, to_cash = _apply_filters(config, dv, list(scores.keys()))
    if to_cash:
        return {}
    if not eligible:
        return {}

    # -- selection (top-N with exit-rank buffer) ---------------------------
    selected = _select(config, eligible, scores, current_holdings)
    if not selected:
        return {}

    # -- sizing -------------------------------------------------------------
    weights = _size(config, dv, selected, warnings)
    return _weights_to_shares(dv, weights, equity)


# ---------------------------------------------------------------------------
# delisting exclusion
# ---------------------------------------------------------------------------


def _exclude_delisted(
    candidates: list[str],
    data: MarketData,
    now: pd.Timestamp,
    run_end: pd.Timestamp | None,
) -> list[str]:
    """Drop symbols delisted as of ``now``: frame ends before the run does AND
    the final bar is already behind us.

    This mirrors the event engine's force-exit model (a frame ending at bar
    ``t`` while the run continues is treated as a delisting effective ``t`` —
    in reality delistings are announced in advance, so acting on it at that
    bar's close is not look-ahead). ``run_end=None`` (paper/live) disables the
    check: a live frame simply ends "today" for every symbol.
    """
    if run_end is None:
        return candidates
    kept: list[str] = []
    for sym in candidates:
        idx = data.full_frame(sym).index
        if len(idx) == 0:
            continue
        last = idx[-1]
        if last < run_end and last <= now:
            continue  # delisted as of `now` — never a buy/selection candidate
        kept.append(sym)
    return kept


# ---------------------------------------------------------------------------
# liquidity
# ---------------------------------------------------------------------------


def _liquidity_filter(config: StrategyConfig, dv: DataView, candidates: list[str]) -> list[str]:
    spec = config.universe
    if spec.min_median_traded_value is None:
        return candidates
    lookback = spec.liquidity_lookback_days
    kept: list[str] = []
    for sym in candidates:
        df = dv.history(sym, n=lookback)
        if df.empty:
            continue
        traded_value = (df["close"] * df["volume"]).median()
        if pd.notna(traded_value) and float(traded_value) >= spec.min_median_traded_value:
            kept.append(sym)
    return kept


# ---------------------------------------------------------------------------
# scoring
# ---------------------------------------------------------------------------


def _score(config: StrategyConfig, dv: DataView, candidates: list[str]) -> dict[str, float]:
    """Latest signal values -> per-symbol score. NaN-signal symbols are dropped.

    Returns ``{}`` when no score is configured (the caller then defaults every
    candidate to 0).
    """
    if config.score is None:
        return {}

    # latest visible value of every signal for every candidate
    values: dict[str, dict[str, float]] = {}
    excluded: set[str] = set()
    for sig in config.signals:
        col: dict[str, float] = {}
        for sym in candidates:
            v = dv.signal(sym, sig.name, sig.params, sig.timeframe)
            if v is None or (isinstance(v, float) and math.isnan(v)):
                excluded.add(sym)
            else:
                col[sym] = float(v)
        values[sig.id] = col
    ranked = [s for s in candidates if s not in excluded]
    if not ranked:
        return {}

    if config.score.type == "single":
        if len(config.signals) != 1:
            raise ConfigError("score type 'single' requires exactly one signal")
        only = config.signals[0].id
        return {s: values[only][s] for s in ranked}

    # weighted_zscore
    scores: dict[str, float] = {s: 0.0 for s in ranked}
    for sig_id, weight in config.score.weights.items():
        xs = np.array([values[sig_id][s] for s in ranked], dtype="float64")
        mean = float(xs.mean())
        std = float(xs.std(ddof=0))  # population std per spec
        if std == 0.0:
            z = np.zeros_like(xs)
        else:
            z = (xs - mean) / std
        for sym, zi in zip(ranked, z, strict=True):
            scores[sym] += weight * float(zi)
    return scores


# ---------------------------------------------------------------------------
# filters (regime routing + per-candidate eligibility)
# ---------------------------------------------------------------------------


def _latest_bool(series: pd.Series) -> bool:
    if series.empty:
        return False
    return bool(series.iloc[-1])


def _apply_filters(
    config: StrategyConfig, dv: DataView, candidates: list[str]
) -> tuple[list[str], bool]:
    """Apply every filter. Returns ``(eligible, to_cash)``.

    A filter whose params carry the reserved key ``symbol`` is a *regime* filter
    evaluated on that symbol's own frame: latest value False sends the whole book
    to cash (``to_cash=True``). Otherwise it is an *eligibility* filter evaluated
    per-candidate on its own frame: latest value False drops that candidate.
    """
    eligible = set(candidates)
    for fspec in config.filters:
        params = dict(fspec.params)
        routed = params.pop("symbol", None)  # reserved key popped by the ENGINE
        fdef = get_filter(fspec.name)
        if routed is not None:
            df = dv.history(routed)
            passed = _latest_bool(fdef.fn(df, **params)) if not df.empty else False
            if not passed:
                return [], True
        else:
            for sym in list(eligible):
                df = dv.history(sym)
                ok = _latest_bool(fdef.fn(df, **params)) if not df.empty else False
                if not ok:
                    eligible.discard(sym)
    return sorted(eligible), False


# ---------------------------------------------------------------------------
# selection
# ---------------------------------------------------------------------------


def _select(
    config: StrategyConfig,
    eligible: list[str],
    scores: dict[str, float],
    current_holdings: dict[str, int],
) -> list[str]:
    """Top-N with a rank buffer. Held names ranked <= exit_rank keep their slot;
    remaining slots are filled from the top."""
    sel = config.selection
    ranked = sorted(eligible, key=lambda s: (-scores[s], s))
    rank = {s: i + 1 for i, s in enumerate(ranked)}

    if sel.method == "top_percentile" and sel.percentile is not None:
        n = max(1, int(math.ceil(sel.percentile * len(ranked))))
        exit_rank = n  # percentile mode has no separate buffer
    else:
        n = sel.n
        exit_rank = sel.exit_rank if sel.exit_rank is not None else sel.n

    held = set(current_holdings)
    retained = [s for s in ranked if s in held and rank[s] <= exit_rank]
    selected = retained[:n]
    for s in ranked:
        if len(selected) >= n:
            break
        if s not in selected:
            selected.append(s)
    return selected


# ---------------------------------------------------------------------------
# sizing
# ---------------------------------------------------------------------------


def _realized_vol(dv: DataView, sym: str, lookback: int) -> float | None:
    closes = dv.history(sym)["close"]
    if len(closes) < 2:
        return None
    rets = closes.pct_change().dropna().tail(lookback)
    if len(rets) < 2:
        return None
    v = float(rets.std(ddof=1))
    if not math.isfinite(v) or v <= 0.0:
        return None
    return v


def _size(
    config: StrategyConfig, dv: DataView, selected: list[str], warnings: list[str]
) -> dict[str, float]:
    sizing = config.sizing
    if sizing.max_sector_pct is not None:
        msg = "sector caps not enforced: no sector table yet"
        logger.warning(msg)
        if msg not in warnings:
            warnings.append(msg)

    if sizing.method == "equal_weight":
        return _size_equal_weight(selected, sizing.max_position_pct)
    if sizing.method == "inverse_volatility":
        return _size_inverse_vol(dv, selected, sizing)
    if sizing.method == "volatility_target":
        return _size_vol_target(dv, selected, sizing)
    if sizing.method == "fixed_fractional":
        if sizing.fraction is None:
            raise ConfigError("fixed_fractional sizing requires 'fraction'")
        return {s: sizing.fraction for s in selected}
    raise ConfigError(f"unknown sizing method {sizing.method!r}")


def _size_equal_weight(selected: list[str], max_position_pct: float) -> dict[str, float]:
    k = len(selected)
    if k == 0:
        return {}
    w = min(1.0 / k, max_position_pct)
    return {s: w for s in selected}


def _size_inverse_vol(dv: DataView, selected: list[str], sizing: SizingSpec) -> dict[str, float]:
    vols = {s: _realized_vol(dv, s, sizing.vol_lookback_days) for s in selected}
    inv = {s: 1.0 / v for s, v in vols.items() if v is not None}
    total = sum(inv.values())
    if total <= 0:
        return {}
    # Normalise to sum 1, then cap each position; residual stays cash (no
    # redistribution) per spec.
    return {s: min(w / total, sizing.max_position_pct) for s, w in inv.items()}


def _size_vol_target(dv: DataView, selected: list[str], sizing: SizingSpec) -> dict[str, float]:
    if sizing.target_vol is None:
        raise ConfigError("volatility_target sizing requires 'target_vol'")
    base = _size_equal_weight(selected, sizing.max_position_pct)
    if not base:
        return {}
    series: dict[str, pd.Series] = {}
    for s in selected:
        rets = dv.history(s)["close"].pct_change().dropna().tail(sizing.vol_lookback_days)
        if len(rets) >= 2:
            series[s] = rets
    if not series:
        return base
    port_ret = pd.DataFrame(series).mean(axis=1).dropna()  # equal-weighted basket return
    if len(port_ret) < 2:
        return base
    vol_annual = float(port_ret.std(ddof=1)) * math.sqrt(_TRADING_DAYS_PER_YEAR)
    if vol_annual <= 0.0:
        return base
    scale = sizing.target_vol / vol_annual
    base_sum = sum(base.values())
    if base_sum > 0:
        scale = min(scale, 1.0 / base_sum)  # cap total exposure at 100% (no leverage)
    scale = max(scale, 0.0)
    return {s: w * scale for s, w in base.items()}


def _weights_to_shares(dv: DataView, weights: dict[str, float], equity: float) -> dict[str, int]:
    targets: dict[str, int] = {}
    for sym, w in weights.items():
        close = dv.close(sym)
        if close is None or close <= 0:
            continue
        qty = int(math.floor(w * equity / close))
        if qty > 0:
            targets[sym] = qty
    return targets


__all__ = ["evaluate_targets"]

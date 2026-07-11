"""Vectorized (fast / screening) backtest engine, built on vectorbt.

Implements :class:`tradingos.engine.base.Engine`. This is the *screening* engine:
it trades accuracy for speed and its results are explicit approximations of the
event-driven engine. It is meant for parameter grids and idea triage; every run
loudly warns that results must be re-validated on the event engine before paper
or live trading.

Design (kept deliberately consistent with the event engine so only *execution*
differs from it):

1. **Same trading calendar and rebalance dates.** The calendar is
   ``data.union_index()`` clipped to the config window, and rebalance timestamps
   come from the *shared* ``engine.event.engine._rebalance_dates`` helper — the
   same Nth-trading-day-of-period semantics as the event engine (leading
   underscore is accepted shared-internal reuse, not a private reach-in).

2. **Identical decision logic.** Target weights at each rebalance are produced by
   the *same* declarative pipeline helpers the event engine uses
   (``engine.event.strategy_runtime._liquidity_filter / _score / _apply_filters
   / _select / _size``), driven by a :class:`DataView` bound to that bar's 15:30
   close. Buffer/retention logic tracks the previously selected set (weights > 0)
   in lieu of a ledger.

3. **Weights panel.** A per-rebalance target-weight vector is placed on each
   rebalance row (and 0.0 for every other tradable symbol on that row, so a
   dropped name is sold); non-rebalance rows are left NaN so positions simply
   drift (held) between rebalances. A symbol-routed regime filter that gates to
   cash yields an all-zero rebalance row (whole book to cash until the next one).

4. **Execution via vectorbt.** ``Portfolio.from_orders`` with
   ``size_type='targetpercent'``, ``size_granularity=1`` (integer shares),
   ``cash_sharing=True`` and ``call_seq='auto'`` (sells fund same-bar buys) fills
   at the SAME bar's close as the decision — the documented fast-engine
   approximation of the event engine's execution. Slippage is applied by
   vectorbt against the trader exactly as the event engine's FillSimulator does.

5. **Costs.** Charges are never re-implemented: per-order turnover
   (``size × fill price``) is extracted from the simulation records and priced
   through :class:`~tradingos.engine.event.execution.ChargeCalculator` (the same
   DP-per-scrip-per-day bookkeeping the event engine uses). The vectorbt sim runs
   cost-free, so its portfolio value is the *gross* equity; net equity is
   ``gross − cumulative charges``. (Unlike the event engine, the cost drag is not
   compounded back into position sizing — a declared approximation.)

Lazy import: ``vectorbt`` (numba, ~30s cold) is imported inside :meth:`run`,
never at module import time.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from tradingos.config.schemas import EngineMode, StrategyConfig
from tradingos.core.errors import ConfigError
from tradingos.core.logging import get_logger
from tradingos.core.models import Product, Side, Timeframe
from tradingos.core.timeutils import MARKET_CLOSE
from tradingos.costs.model import CostModel
from tradingos.engine.base import UniverseResolver, clip_calendar
from tradingos.engine.dataview import DataView, MarketData, SignalStore
from tradingos.engine.event.engine import _rebalance_dates
from tradingos.engine.event.execution import ChargeCalculator
from tradingos.engine.event.strategy_runtime import (
    _apply_filters,
    _exclude_delisted,
    _liquidity_filter,
    _score,
    _select,
    _size,
)
from tradingos.engine.result import BacktestResult

logger = get_logger(__name__)

_CLOSE_OFFSET = pd.Timedelta(hours=MARKET_CLOSE.hour, minutes=MARKET_CLOSE.minute)

# The single mandatory disclaimer — always the first warning on a fast-engine run.
_FAST_ENGINE_WARNING = (
    "VECTORIZED (fast) engine: results are approximations for screening only and "
    "MUST be validated on the event engine before paper or live trading."
)
_APPROX_WARNINGS = (
    "Fills are at the SAME bar's close as the rebalance decision (fast-engine "
    "approximation of the event engine's execution); no order book, no partial "
    "fills, and no volume-participation cap are modeled.",
    "Transaction costs are computed per order via CostModel and subtracted from a "
    "cost-free gross-equity simulation; the cost drag on buying power is NOT "
    "compounded into position sizing (net = gross - cumulative charges).",
    "Per-trade round trips are not emitted by the fast engine (result.trades is "
    "empty); total_costs is authoritative at the portfolio level. Use the event "
    "engine for trade-level analytics.",
    "Delisting/suspension force-exits and risk overlays (stops, kill switch) are "
    "not modeled by the fast engine.",
)


class VectorizedEngine:
    """Fast, vectorbt-backed backtester. Approximate by design; see module docs."""

    def run(
        self,
        config: StrategyConfig,
        data: MarketData,
        universe: UniverseResolver,
    ) -> BacktestResult:
        if config.timeframe == Timeframe.MINUTE:
            raise NotImplementedError(
                "vectorized engine minute timeframe is not yet supported (daily only)"
            )
        if config.rebalance.frequency == "event":
            raise ConfigError(
                "rebalance frequency 'event' is not supported in the backtest engine"
            )

        warnings: list[str] = [_FAST_ENGINE_WARNING, *_APPROX_WARNINGS]
        if config.overlays:
            names = ", ".join(o.name for o in config.overlays)
            warnings.append(f"IGNORED overlays on the fast engine: {names}.")

        # -- calendar (shared helper keeps both engines identical) -------------
        calendar = clip_calendar(data.union_index(), config.start, config.end)

        if len(calendar) == 0:
            return self._empty_result(config, data, warnings)

        rebalance_dates = _rebalance_dates(
            calendar, config.rebalance.frequency, config.rebalance.trading_day
        )

        # -- target weights per rebalance date --------------------------------
        signal_store = SignalStore(data)
        base_dv = DataView(data, signal_store, datetime(1970, 1, 1))
        weights_by_date: dict[pd.Timestamp, dict[str, float]] = {}
        prev_selected: set[str] = set()
        for t in calendar:
            if t not in rebalance_dates:
                continue
            dv_t = base_dv.at((t.normalize() + _CLOSE_OFFSET).to_pydatetime())
            w = self._target_weights(
                config, dv_t, universe, data, prev_selected, warnings, run_end=calendar[-1]
            )
            weights_by_date[t] = w
            prev_selected = {s for s, wi in w.items() if wi > 0.0}

        for msg in universe.warnings:
            if msg not in warnings:
                warnings.append(msg)

        traded = sorted({s for w in weights_by_date.values() for s in w})
        if not traded:
            # Nothing is ever bought: portfolio is all cash for the whole run.
            flat = pd.Series(config.capital, index=calendar, dtype="float64")
            return self._result(config, data, calendar, flat, flat, 0.0, warnings)

        # Warn if any tradable name's frame ends before the run does (a potential
        # delisting the fast engine will silently keep marking at its last close).
        frames = {s: data.full_frame(s) for s in traded}
        if any(len(df) and df.index[-1] < calendar[-1] for df in frames.values()):
            warnings.append(
                "One or more held symbols' data ends before the run does; the fast "
                "engine keeps marking them at their last close (no delisting model)."
            )

        # -- price + size panels ----------------------------------------------
        close = pd.DataFrame(
            {s: frames[s]["close"].reindex(calendar) for s in traded}, index=calendar
        )
        # Forward-fill gaps so vectorbt can value/hold across missing bars; leading
        # NaNs (before a symbol's first bar) only ever multiply a zero position, so
        # back-filling them is economically inert and never leaks a future price
        # into a held valuation.
        close = close.ffill().bfill()

        size = pd.DataFrame(float("nan"), index=calendar, columns=traded)
        for t, w in weights_by_date.items():
            row = {s: 0.0 for s in traded}  # dropped names -> target 0% -> sold
            for s, wi in w.items():
                px = close.at[t, s]
                if pd.notna(px) and px > 0:
                    row[s] = wi
            size.loc[t, traded] = [row[s] for s in traded]

        slippage_bps = (
            config.execution.slippage_bps
            if config.execution.slippage_bps is not None
            else CostModel(config.costs.schedule).schedule.slippage.other_bps
        )

        # -- simulate (lazy vectorbt import) ----------------------------------
        import vectorbt as vbt

        pf = vbt.Portfolio.from_orders(
            close=close,
            size=size,
            size_type="targetpercent",
            direction="longonly",
            price=close,
            fees=0.0,  # charges are priced separately via CostModel
            slippage=slippage_bps / 10_000.0,
            size_granularity=1.0,  # integer shares (no fractional lots)
            init_cash=float(config.capital),
            cash_sharing=True,
            call_seq="auto",  # sells fund same-bar buys, deterministic
            group_by=True,
            freq="1D",
        )

        gross = pf.value()  # cost-free portfolio value == gross equity
        if isinstance(gross, pd.DataFrame):  # single group -> collapse to Series
            gross = gross.iloc[:, 0]
        gross = gross.reindex(calendar).astype("float64")

        # -- costs: price every order's turnover through the shared CostModel -
        charges_per_bar, total_costs = self._order_charges(
            pf, config.costs.product, config.costs.schedule, calendar
        )
        cum_charges = charges_per_bar.cumsum()
        net = gross - cum_charges

        return self._result(config, data, calendar, net, gross, total_costs, warnings)

    # -- pipeline (weights, not shares) ------------------------------------

    @staticmethod
    def _target_weights(
        config: StrategyConfig,
        dv: DataView,
        resolver: UniverseResolver,
        data: MarketData,
        prev_selected: set[str],
        warnings: list[str],
        run_end: pd.Timestamp | None = None,
    ) -> dict[str, float]:
        """Mirror ``strategy_runtime.evaluate_targets`` but stop at rupee weights.

        Returns ``{symbol: weight}`` (fractions of equity); an empty dict means the
        whole book is in cash (nothing qualified or a regime filter gated to cash).
        ``run_end`` (the run's final calendar bar) enables the same delisting
        exclusion the event engine applies: a symbol whose frame ended is dropped
        from the candidate set, so its frozen final score cannot hold a phantom
        flat-priced position until the end of the run.
        """
        resolved = resolver.resolve(config.universe, dv.now.date(), data)
        available = set(data.symbols)
        candidates = sorted(s for s in resolved if s in available)
        candidates = _exclude_delisted(candidates, data, dv.now, run_end)
        if not candidates:
            return {}

        candidates = _liquidity_filter(config, dv, candidates)
        if not candidates:
            return {}

        if config.score is None:
            # No score configured is legal (e.g. a single-symbol trend strategy):
            # every candidate scores 0 and selection falls back to symbol order.
            scores = {s: 0.0 for s in candidates}
        else:
            scores = _score(config, dv, candidates)  # excludes NaN-signal symbols
            if not scores:
                # A score IS configured but not one candidate has a valid value
                # (indicator warm-up window): hold cash, mirroring
                # strategy_runtime.evaluate_targets.
                return {}

        eligible, to_cash = _apply_filters(config, dv, list(scores.keys()))
        if to_cash or not eligible:
            return {}

        holdings = {s: 1 for s in prev_selected}  # buffer logic needs the held SET
        selected = _select(config, eligible, scores, holdings)
        if not selected:
            return {}

        weights = _size(config, dv, selected, warnings)
        # Drop any symbol without a usable close, mirroring _weights_to_shares.
        return {s: w for s, w in weights.items() if w > 0 and (dv.close(s) or 0) > 0}

    # -- costs -------------------------------------------------------------

    @staticmethod
    def _order_charges(
        pf: object,
        product: Product,
        schedule: str,
        calendar: pd.DatetimeIndex,
    ) -> tuple[pd.Series, float]:
        """Per-bar charge series (aligned to ``calendar``) and the total charges.

        Turnover for each executed order is ``size × fill price`` (the fill price
        already carries slippage). Orders are priced through the same
        :class:`ChargeCalculator` the event engine uses, so the DP-per-scrip-per-
        day charge is applied identically.
        """
        charge_calc = ChargeCalculator(CostModel(schedule), product)
        per_bar = pd.Series(0.0, index=calendar, dtype="float64")

        orders = pf.orders.records_readable  # type: ignore[attr-defined]
        if len(orders) == 0:
            return per_bar, 0.0

        orders = orders.sort_values(
            by=["Timestamp", "Side", "Column"],
            key=lambda c: c.map({"Buy": 1, "Sell": 0}) if c.name == "Side" else c,
        )
        total = 0.0
        for row in orders.itertuples(index=False):
            ts = pd.Timestamp(row.Timestamp)
            symbol = str(row.Column)
            side = Side.SELL if str(row.Side) == "Sell" else Side.BUY
            value = float(row.Size) * float(row.Price)
            charge = charge_calc.charges(side, symbol, value, ts.to_pydatetime())
            per_bar.at[ts] += charge
            total += charge
        return per_bar, round(total, 2)

    # -- result construction ----------------------------------------------

    @staticmethod
    def _result(
        config: StrategyConfig,
        data: MarketData,
        calendar: pd.DatetimeIndex,
        net: pd.Series,
        gross: pd.Series,
        total_costs: float,
        warnings: list[str],
    ) -> BacktestResult:
        return BacktestResult(
            config=config,
            engine=EngineMode.VECTORIZED,
            start=calendar[0].date(),
            end=calendar[-1].date(),
            capital=config.capital,
            equity=net.round(2),
            gross_equity=gross.round(2),
            trades=[],  # fast engine emits no per-trade round trips (see warnings)
            total_costs=total_costs,
            warnings=warnings,
            meta={"snapshot_id": data.snapshot_id},
        )

    @staticmethod
    def _empty_result(
        config: StrategyConfig, data: MarketData, warnings: list[str]
    ) -> BacktestResult:
        empty = pd.Series(dtype="float64")
        start = config.start or datetime(1970, 1, 1).date()
        end = config.end or start
        return BacktestResult(
            config=config,
            engine=EngineMode.VECTORIZED,
            start=start,
            end=end,
            capital=config.capital,
            equity=empty,
            gross_equity=empty,
            trades=[],
            total_costs=0.0,
            warnings=warnings,
            meta={"snapshot_id": data.snapshot_id},
        )


__all__ = ["VectorizedEngine"]

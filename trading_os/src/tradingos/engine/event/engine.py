"""Event-driven backtest engine (Phase 3).

Implements :class:`tradingos.engine.base.Engine`. The engine walks a daily
trading calendar (the union of every symbol's bar timestamps, clipped to the
config window) and, at each bar ``t``, runs a fixed sequence:

    1. OPEN(t)     execute the working order book at the open (T+1 fills land
                   here); sells are applied before buys so proceeds fund buys.
    2. MARK        mark every held symbol at close(t) (no bar -> keep last mark).
    3. DELIST      any held symbol whose frame ENDS at t (and the run continues)
                   is force-exited at close(t)*(1-haircut) with a warning.
    4. OVERLAYS    at close(t): trailing stops queue exits for the next open; the
                   portfolio kill switch liquidates and halts all new entries.
    5. REBALANCE   on scheduled days (and only if not halted): cancel the working
                   book (cancel-and-replace) and evaluate the declarative
                   strategy pipeline at now = t 15:30, queueing target orders.
    6. RECORD      record net equity(t); gross_equity(t) = equity + Σ costs.

**Look-ahead guarantee.** Every strategy/overlay read goes through a DataView
bound to ``t`` 15:30, so signals computed on data through close(T) can only move
fills at T+1 open. The engine never hands strategy code a view beyond that.

**Execution timing.** ``next_open`` (default) queues orders that fill at step 1
of ``t+1``; ``same_close`` fills them against bar ``t`` at the close.

**Gross-equity approximation.** ``gross_equity(t) = net_equity(t) + cumulative
costs(t)`` — i.e. the same fills are assumed and only the charges are added back.
This is the standard, documented approximation (identical execution paths).
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from tradingos.config.schemas import EngineMode, StrategyConfig
from tradingos.core.errors import ConfigError
from tradingos.core.logging import get_logger
from tradingos.core.models import (
    Fill,
    Order,
    OrderStatus,
    OrderType,
    Product,
    Side,
    Timeframe,
)
from tradingos.core.timeutils import MARKET_CLOSE, MARKET_OPEN
from tradingos.costs.model import CostModel
from tradingos.engine.base import UniverseResolver, clip_calendar
from tradingos.engine.dataview import DataView, MarketData, SignalStore
from tradingos.engine.event.execution import ChargeCalculator, FillSimulator
from tradingos.engine.event.overlays import OverlayContext, make_overlay
from tradingos.engine.event.portfolio import Ledger
from tradingos.engine.event.strategy_runtime import evaluate_targets
from tradingos.engine.result import BacktestResult

logger = get_logger(__name__)

_OPEN_OFFSET = pd.Timedelta(hours=MARKET_OPEN.hour, minutes=MARKET_OPEN.minute)
_CLOSE_OFFSET = pd.Timedelta(hours=MARKET_CLOSE.hour, minutes=MARKET_CLOSE.minute)


def _period_key(t: pd.Timestamp, freq: str) -> tuple[int, int]:
    if freq == "weekly":
        iso = t.isocalendar()
        return (int(iso.year), int(iso.week))
    if freq == "monthly":
        return (t.year, t.month)
    if freq == "quarterly":
        return (t.year, (t.month - 1) // 3)
    raise ConfigError(f"unsupported rebalance frequency {freq!r}")


def _rebalance_dates(calendar: pd.DatetimeIndex, freq: str, trading_day: int) -> set[pd.Timestamp]:
    """Timestamps on which a rebalance fires.

    ``daily`` fires every bar; ``weekly``/``monthly``/``quarterly`` fire on the
    Nth trading day of each calendar period (clamped to the last available day
    when a period is shorter than N). ``event`` is not supported in a backtest.
    """
    if freq == "daily":
        return set(calendar)
    if freq == "event":
        raise ConfigError("rebalance frequency 'event' is not supported in the backtest engine")
    groups: dict[tuple[int, int], list[pd.Timestamp]] = {}
    for t in calendar:  # calendar is ascending -> each group's list is ascending
        groups.setdefault(_period_key(t, freq), []).append(t)
    dates: set[pd.Timestamp] = set()
    for days in groups.values():
        idx = min(trading_day - 1, len(days) - 1)
        dates.add(days[idx])
    return dates


class EventEngine:
    """Realistic, look-ahead-safe event-driven backtester for NSE cash equities."""

    def run(
        self,
        config: StrategyConfig,
        data: MarketData,
        universe: UniverseResolver,
    ) -> BacktestResult:
        if config.timeframe == Timeframe.MINUTE:
            raise NotImplementedError(
                "event engine minute timeframe is not yet supported (daily only)"
            )
        if config.rebalance.frequency == "event":
            raise ConfigError("rebalance frequency 'event' is not supported in the backtest engine")

        # -- run-scoped collaborators --------------------------------------
        cost_model = CostModel(config.costs.schedule)
        product: Product = config.costs.product
        charge_calc = ChargeCalculator(cost_model, product)
        slippage_bps = (
            config.execution.slippage_bps
            if config.execution.slippage_bps is not None
            else cost_model.schedule.slippage.other_bps
        )
        fill_sim = FillSimulator(
            charge_calc, slippage_bps, config.execution.max_participation, product
        )
        ledger = Ledger(config.capital, strategy_id=config.name)
        signal_store = SignalStore(data)
        base_dv = DataView(data, signal_store, datetime(1970, 1, 1))
        overlays = [make_overlay(spec) for spec in config.overlays]

        warnings: list[str] = []

        # -- calendar (shared helper keeps both engines identical) ----------
        calendar = clip_calendar(data.union_index(), config.start, config.end)

        frames = {s: data.full_frame(s) for s in data.symbols}
        last_ts = {s: df.index[-1] for s, df in frames.items() if len(df)}

        def bar_at(symbol: str, t: pd.Timestamp) -> pd.Series | None:
            df = frames[symbol]
            if t in df.index:
                return df.loc[t]
            return None

        if len(calendar) == 0:
            return self._empty_result(config, data, warnings)

        # -- order-book helpers --------------------------------------------
        working: list[Order] = []
        id_to_order: dict[str, Order] = {}
        trades: list = []

        def queue(order: Order) -> None:
            order.transition(OrderStatus.OPEN)
            working.append(order)
            id_to_order[order.client_order_id] = order

        def cancel_all() -> None:
            for o in working:
                o.transition(OrderStatus.CANCELLED)
            working.clear()
            id_to_order.clear()

        def cancel_for_rebalance() -> None:
            """Cancel-and-replace scope of a rebalance: every working order
            EXCEPT risk-exit sells (overlay stops etc. — any SELL not tagged
            "rebalance"). A risk exit queued at this bar's close must survive
            the same-bar rebalance, or frequent (e.g. daily) rebalancing
            cancels every stop before it can fill and overlays never act."""
            for o in working:
                if o.side == Side.SELL and o.tag != "rebalance":
                    continue
                o.transition(OrderStatus.CANCELLED)
            _prune_working()

        def cancel_symbol(symbol: str) -> None:
            for o in working:
                if o.symbol == symbol:
                    o.transition(OrderStatus.CANCELLED)
            _prune_working()

        def _prune_working() -> None:
            nonlocal working
            working = [o for o in working if not o.status.is_terminal]
            id_to_order.clear()
            id_to_order.update({o.client_order_id: o for o in working})

        def execute(bars: dict[str, pd.Series], fill_ts: datetime, basis: str) -> None:
            fills = fill_sim.execute(working, bars, fill_ts, basis)
            for fill in fills:
                order = id_to_order.get(fill.client_order_id)
                reason = order.tag if order is not None else ""
                trade = ledger.apply_fill(fill, reason or "")
                if trade is not None:
                    trades.append(trade)
            _prune_working()

        def make_order(symbol: str, side: Side, qty: int, tag: str, when: pd.Timestamp) -> Order:
            return Order(
                symbol=symbol,
                side=side,
                qty=qty,
                order_type=OrderType.MARKET,
                product=product,
                strategy_id=config.name,
                tag=tag,
                created_at=when.to_pydatetime(),
            )

        def delta_orders(targets: dict[str, int], when: pd.Timestamp) -> list[Order]:
            current = ledger.holdings()
            out: list[Order] = []
            for sym in sorted(set(targets) | set(current)):
                delta = targets.get(sym, 0) - current.get(sym, 0)
                if delta == 0:
                    continue
                side = Side.BUY if delta > 0 else Side.SELL
                out.append(make_order(sym, side, abs(delta), "rebalance", when))
            return out

        rebalance_dates = _rebalance_dates(
            calendar, config.rebalance.frequency, config.rebalance.trading_day
        )

        # -- main loop -----------------------------------------------------
        equity_records: dict[pd.Timestamp, float] = {}
        gross_records: dict[pd.Timestamp, float] = {}
        halted = False
        last_index = len(calendar) - 1

        for i, t in enumerate(calendar):
            open_ts = (t.normalize() + _OPEN_OFFSET).to_pydatetime()
            close_ts_pd = t.normalize() + _CLOSE_OFFSET
            close_ts = close_ts_pd.to_pydatetime()

            # 1. OPEN(t): execute the working book at the open.
            if working:
                bars_open: dict[str, pd.Series] = {}
                for o in working:
                    if o.symbol not in bars_open:
                        bar = bar_at(o.symbol, t)
                        if bar is not None:
                            bars_open[o.symbol] = bar
                execute(bars_open, open_ts, "open")

            # 2. MARK positions at close(t).
            for sym in list(ledger.positions):
                bar = bar_at(sym, t)
                if bar is not None:
                    ledger.mark(sym, float(bar["close"]))

            # 3. DELISTING: frame ends at t while the run continues past t.
            if i != last_index:
                for sym in list(ledger.positions):
                    if last_ts.get(sym) == t:
                        self._force_delist(
                            sym, t, close_ts, ledger, charge_calc, product, config, trades, warnings
                        )
                        cancel_symbol(sym)

            dv_t = base_dv.at(close_ts)

            # 4. OVERLAYS at close(t).
            if overlays and not halted:
                ctx = OverlayContext(
                    now=t,
                    dv=dv_t,
                    holdings=ledger.holdings(),
                    entry_ts=ledger.entry_ts_map(),
                    equity=ledger.equity(),
                )
                exits_all: dict[str, str] = {}
                liquidate = False
                halt = False
                for ov in overlays:
                    dec = ov.evaluate(ctx)
                    exits_all.update(dec.exits)
                    liquidate = liquidate or dec.liquidate_all
                    halt = halt or dec.halt_entries
                    for w in dec.warnings:
                        if w not in warnings:
                            warnings.append(w)
                if liquidate:
                    cancel_all()
                    for sym, qty in sorted(ledger.holdings().items()):
                        if qty > 0:
                            queue(make_order(sym, Side.SELL, qty, "kill_switch", t))
                    halted = True
                else:
                    halted = halted or halt
                    # A risk exit must also cancel the symbol's working BUYs
                    # (e.g. a participation-capped rebalance remainder), or the
                    # leftover buy refills the position right after the stop
                    # fills — stop/re-buy ping-pong bleeding charges.
                    if exits_all:
                        for o in working:
                            if o.symbol in exits_all and o.side == Side.BUY:
                                o.transition(OrderStatus.CANCELLED)
                        _prune_working()
                    for sym in sorted(exits_all):
                        qty = ledger.holdings().get(sym, 0)
                        # A stop that fired on an earlier bar may still be
                        # working (participation-capped partial fills); only
                        # queue the quantity not already covered by a working
                        # sell, or the book would oversell the position.
                        qty -= sum(
                            o.remaining_qty
                            for o in working
                            if o.symbol == sym and o.side == Side.SELL
                        )
                        if qty > 0:
                            queue(make_order(sym, Side.SELL, qty, exits_all[sym], t))

            # 5. REBALANCE (cancel-and-replace) on scheduled days.
            if (t in rebalance_dates) and not halted:
                cancel_for_rebalance()
                # After cancel_for_rebalance the only survivors are risk-exit
                # sells; those symbols are mid-exit and get NO rebalance order
                # this bar (neither a competing sell that would oversell the
                # position, nor a re-buy that would fight the stop). They are
                # flat and re-selectable from the next rebalance onward.
                risk_exit_syms = {o.symbol for o in working}
                targets = evaluate_targets(
                    config,
                    dv_t,
                    universe,
                    data,
                    ledger.holdings(),
                    ledger.equity(),
                    warnings,
                    run_end=calendar[-1],  # enables delisting exclusion (backtests only)
                    # running NET equity for bars < t (this bar not recorded until
                    # step 6); feeds the vol_target overlay's realized-vol estimate.
                    equity_history=equity_records,
                )
                new_orders = [
                    o for o in delta_orders(targets, t) if o.symbol not in risk_exit_syms
                ]
                for o in new_orders:
                    queue(o)
                if config.execution.timing == "same_close":
                    bars_close: dict[str, pd.Series] = {}
                    for o in new_orders:
                        if o.symbol not in bars_close:
                            bar = bar_at(o.symbol, t)
                            if bar is not None:
                                bars_close[o.symbol] = bar
                    execute(bars_close, close_ts, "close")
                    for sym in list(ledger.positions):
                        bar = bar_at(sym, t)
                        if bar is not None:
                            ledger.mark(sym, float(bar["close"]))

            # 6. RECORD equity at the end of the bar.
            equity = ledger.equity()
            equity_records[t] = equity
            gross_records[t] = round(equity + ledger.total_costs, 2)

        # Orders still working at run end (e.g. participation-capped fills that
        # never completed) are forced holds the caller must see on the result.
        for o in working:
            if not o.status.is_terminal:
                msg = (
                    f"unfilled working order at run end: {o.side.value} "
                    f"{o.remaining_qty}/{o.qty} {o.symbol} ({o.tag or 'untagged'})"
                )
                logger.warning(msg)
                warnings.append(msg)

        # Ledger accounting anomalies (oversell clips, ignored sells) surface too.
        for w in ledger.warnings:
            if w not in warnings:
                warnings.append(w)

        for w in universe.warnings:
            if w not in warnings:
                warnings.append(w)

        equity_series = pd.Series(equity_records).sort_index()
        gross_series = pd.Series(gross_records).sort_index()
        return BacktestResult(
            config=config,
            engine=EngineMode.EVENT,
            start=calendar[0].date(),
            end=calendar[-1].date(),
            capital=config.capital,
            equity=equity_series,
            gross_equity=gross_series,
            trades=trades,
            total_costs=ledger.total_costs,
            warnings=warnings,
            meta={"snapshot_id": data.snapshot_id},
        )

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _force_delist(
        symbol: str,
        t: pd.Timestamp,
        close_ts: datetime,
        ledger: Ledger,
        charge_calc: ChargeCalculator,
        product: Product,
        config: StrategyConfig,
        trades: list,
        warnings: list[str],
    ) -> None:
        pos = ledger.positions[symbol]
        qty = pos.qty
        mark = pos.last_price if pos.last_price is not None else pos.avg_price
        price = round(mark * (1.0 - config.delisting.haircut_pct), 2)
        value = qty * price
        charges = charge_calc.charges(Side.SELL, symbol, value, close_ts)
        fill = Fill(
            client_order_id=f"delist-{symbol}",
            symbol=symbol,
            side=Side.SELL,
            qty=qty,
            price=price,
            ts=close_ts,
            charges=charges,
            product=product,
        )
        trade = ledger.apply_fill(fill, "delisted")
        if trade is not None:
            trades.append(trade)
        msg = (
            f"DELISTING: {symbol} last bar {t.date()}; force-exited {qty} @ "
            f"{price} (close*(1-{config.delisting.haircut_pct}))."
        )
        logger.warning(msg)
        warnings.append(msg)

    @staticmethod
    def _empty_result(
        config: StrategyConfig, data: MarketData, warnings: list[str]
    ) -> BacktestResult:
        empty = pd.Series(dtype="float64")
        start = config.start or datetime(1970, 1, 1).date()
        end = config.end or start
        return BacktestResult(
            config=config,
            engine=EngineMode.EVENT,
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


__all__ = ["EventEngine"]

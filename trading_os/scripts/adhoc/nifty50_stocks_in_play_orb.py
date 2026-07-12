"""Replication of Zarattini-Barbon-Aziz five-minute Stocks-in-Play ORB."""

from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, dataclass
from datetime import datetime, time

import numpy as np
import pandas as pd
from nifty50_gap_up_orb import END, START, SYMBOLS, _regular_session

from tradingos.config.settings import get_settings
from tradingos.core.models import Product, Side, Timeframe
from tradingos.costs.model import CostModel
from tradingos.data.store import BarStore

INITIAL_CAPITAL = 1_000_000.0
RISK_FRACTION = 0.01
MAX_LEVERAGE = 4.0
SLIPPAGE_BPS = float(os.environ.get("ORB_SLIPPAGE_BPS", "10"))


@dataclass
class Setup:
    symbol: str
    session: str
    relative_volume: float
    direction: str
    entry_level: float
    atr14: float
    bars: pd.DataFrame


@dataclass
class Trade:
    variant: str
    symbol: str
    session: str
    relative_volume: float
    direction: str
    entry_ts: str
    entry: float
    exit_ts: str
    exit: float
    reason: str
    qty: int
    gross_pnl: float
    charges: float
    net_pnl: float
    r_multiple: float


def _charges(model: CostModel, side: Side, value: float, ts: pd.Timestamp) -> float:
    return model.order_charges(
        side, Product.MIS, value, first_sell_of_scrip_today=True, trade_date=ts.date()
    ).total


def _fill(price: float, side: Side) -> float:
    direction = 1.0 if side == Side.BUY else -1.0
    return round(price * (1.0 + direction * SLIPPAGE_BPS / 10_000.0), 2)


def _setups() -> dict[str, list[Setup]]:
    store = BarStore(get_settings())
    by_day: dict[str, list[Setup]] = {}
    for symbol in SYMBOLS:
        frame = store.read_raw(
            symbol,
            Timeframe.MINUTE,
            datetime.combine(START, time.min),
            datetime.combine(END, time.max),
        ).to_pandas()
        frame["ts"] = pd.to_datetime(frame["ts"])
        frame["session"] = frame["ts"].dt.date
        first5_volumes: list[float] = []
        prev_close: float | None = None
        atr: float | None = None
        for session_day, raw_day in frame.groupby("session", sort=True):
            day = _regular_session(raw_day).copy()
            if day.empty:
                continue
            high, low, close = float(day.high.max()), float(day.low.min()), float(day.iloc[-1].close)
            tr = high - low if prev_close is None else max(high - low, abs(high - prev_close), abs(low - prev_close))
            prior_atr = atr
            atr = tr if atr is None else ((13.0 * atr + tr) / 14.0)
            prev_close = close
            tod = day.ts.dt.time
            opening = day[(tod >= time(9, 15)) & (tod < time(9, 20))]
            expected = {time(9, 15 + minute) for minute in range(5)}
            if set(opening.ts.dt.time) != expected:
                continue
            opening_volume = float(opening.volume.sum())
            relative_volume = (
                opening_volume / (sum(first5_volumes[-14:]) / 14.0)
                if len(first5_volumes) >= 14 and sum(first5_volumes[-14:]) > 0
                else None
            )
            first5_volumes.append(opening_volume)
            if relative_volume is None or relative_volume < 1.0 or prior_atr is None:
                continue
            first_open = float(opening.iloc[0].open)
            first_close = float(opening.iloc[-1].close)
            if first_close == first_open:
                continue
            direction = "long" if first_close > first_open else "short"
            entry_level = float(opening.high.max() if direction == "long" else opening.low.min())
            later = day[(tod >= time(9, 20)) & (tod <= time(15, 15))].copy()
            if later[later.ts.dt.time == time(15, 15)].empty:
                continue
            by_day.setdefault(str(session_day), []).append(
                Setup(symbol, str(session_day), relative_volume, direction, entry_level, prior_atr, later)
            )
    return by_day


def _execute(setup: Setup, qty: int, variant: str, model: CostModel) -> Trade | None:
    bars = setup.bars
    if setup.direction == "long":
        triggered = bars[bars.high > setup.entry_level]
    else:
        triggered = bars[bars.low < setup.entry_level]
    if triggered.empty:
        return None
    entry_idx = triggered.index[0]
    entry_bar = bars.loc[entry_idx]
    entry_side = Side.BUY if setup.direction == "long" else Side.SELL
    exit_side = Side.SELL if setup.direction == "long" else Side.BUY
    raw_entry = (
        max(setup.entry_level, float(entry_bar.open))
        if setup.direction == "long"
        else min(setup.entry_level, float(entry_bar.open))
    )
    entry = _fill(raw_entry, entry_side)
    stop_distance = 0.10 * setup.atr14
    stop = entry - stop_distance if setup.direction == "long" else entry + stop_distance
    # A one-minute OHLC bar does not reveal whether its low/high occurred before
    # or after the breakout trigger. Start stop evaluation on the next minute
    # rather than fabricating an immediate same-bar stop after entry.
    entry_pos = bars.index.get_loc(entry_idx)
    after = bars.iloc[entry_pos + 1 :]
    if after.empty:
        return None
    time_bar = after[after.ts.dt.time == time(15, 15)].iloc[0]
    raw_exit = float(time_bar.close)
    exit_ts = pd.Timestamp(time_bar.ts)
    reason = "time"
    for _, bar in after.iterrows():
        hit = float(bar.low) <= stop if setup.direction == "long" else float(bar.high) >= stop
        if hit:
            raw_exit = stop
            exit_ts = pd.Timestamp(bar.ts)
            reason = "stop"
            break
        if pd.Timestamp(bar.ts).time() == time(15, 15):
            break
    exit_px = _fill(raw_exit, exit_side)
    signed_move = exit_px - entry if setup.direction == "long" else entry - exit_px
    gross = qty * signed_move
    entry_ts = pd.Timestamp(entry_bar.ts)
    costs = _charges(model, entry_side, qty * entry, entry_ts) + _charges(
        model, exit_side, qty * exit_px, exit_ts
    )
    net = gross - costs
    return Trade(
        variant, setup.symbol, setup.session, round(setup.relative_volume, 4),
        setup.direction, str(entry_ts), entry, str(exit_ts), exit_px, reason, qty,
        round(gross, 2), round(costs, 2), round(net, 2),
        round(net / (qty * stop_distance), 4),
    )


def run() -> None:
    all_setups = _setups()
    model = CostModel("zerodha_2026")
    trade_rows: list[Trade] = []
    summaries: list[dict[str, object]] = []
    equity_curves: dict[str, pd.Series] = {}

    for name, top_n in (("top3_rvol", 3), ("top5_rvol", 5), ("all_rvol_ge1", None)):
        capital = INITIAL_CAPITAL
        daily_equity: dict[str, float] = {}
        variant_trades: list[Trade] = []
        for session_day in sorted(all_setups):
            selected = sorted(
                all_setups[session_day], key=lambda setup: setup.relative_volume, reverse=True
            )
            if top_n is not None:
                selected = selected[:top_n]
            provisional: list[tuple[Setup, int]] = []
            for setup in selected:
                stop_distance = 0.10 * setup.atr14
                qty = math.floor((capital * RISK_FRACTION) / stop_distance)
                if qty > 0:
                    provisional.append((setup, qty))
            gross_exposure = sum(qty * setup.entry_level for setup, qty in provisional)
            scale = min(1.0, (MAX_LEVERAGE * capital / gross_exposure)) if gross_exposure else 1.0
            day_pnl = 0.0
            for setup, provisional_qty in provisional:
                qty = math.floor(provisional_qty * scale)
                if qty <= 0:
                    continue
                trade = _execute(setup, qty, name, model)
                if trade is not None:
                    variant_trades.append(trade)
                    trade_rows.append(trade)
                    day_pnl += trade.net_pnl
            capital += day_pnl
            daily_equity[session_day] = capital
        equity = pd.Series(daily_equity, dtype=float)
        equity_curves[name] = equity
        returns = equity.pct_change().dropna()
        drawdown = equity / equity.cummax() - 1.0
        net_values = pd.Series([trade.net_pnl for trade in variant_trades], dtype=float)
        summaries.append({
            "variant": name,
            "trades": len(variant_trades),
            "longs": sum(trade.direction == "long" for trade in variant_trades),
            "shorts": sum(trade.direction == "short" for trade in variant_trades),
            "win_rate_pct": round(float((net_values > 0).mean() * 100), 2),
            "final_equity": round(capital, 2),
            "net_return_pct": round((capital / INITIAL_CAPITAL - 1.0) * 100, 2),
            "max_drawdown_pct": round(float(drawdown.min() * 100), 2),
            "sharpe": round(float(returns.mean() / returns.std() * np.sqrt(252)), 3)
            if returns.std() > 0 else None,
            "avg_r": round(float(np.mean([trade.r_multiple for trade in variant_trades])), 4),
            "charges": round(sum(trade.charges for trade in variant_trades), 2),
        })

    out = (
        get_settings().artifacts_dir
        / "adhoc"
        / "nifty50_stocks_in_play_orb"
        / f"{SLIPPAGE_BPS:g}bps"
        / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    )
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([asdict(trade) for trade in trade_rows]).to_csv(out / "trades.csv", index=False)
    pd.DataFrame(equity_curves).to_csv(out / "equity.csv")
    report = {
        "window": {"start": str(START), "end": str(END)},
        "rules": {
            "opening_range_minutes": 5,
            "direction": "first five-minute candle direction; doji skipped",
            "relative_volume": "first 5m volume / prior 14-session first 5m average; minimum 1",
            "stop": "10% of causal Wilder ATR(14)",
            "exit": "stop or 15:15",
            "risk_per_setup_pct": 1.0,
            "max_leverage": 4.0,
            "costs": f"MIS plus {SLIPPAGE_BPS:g} bps slippage each side",
        },
        "variants": summaries,
        "caveats": [
            "current Nifty 50 constituents applied historically",
            "Nifty 50 is much narrower than the paper's roughly 7,000-stock universe",
            "same-minute stop/entry ambiguity is resolved conservatively",
        ],
    }
    (out / "summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print(f"artifacts -> {out}")


if __name__ == "__main__":
    run()

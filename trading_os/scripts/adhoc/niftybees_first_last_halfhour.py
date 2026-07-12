"""Replication of first-to-last-half-hour intraday market momentum."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, time

import numpy as np
import pandas as pd
from nifty50_gap_up_orb import END, START, _regular_session, _slipped

from tradingos.config.settings import get_settings
from tradingos.core.models import Product, Side, Timeframe
from tradingos.costs.model import CostModel
from tradingos.data.store import BarStore

INITIAL_CAPITAL = 1_000_000.0


@dataclass
class DaySignal:
    session: str
    direction: str
    first_return: float
    first_volume: float
    first_range_pct: float
    volume_threshold: float | None
    volatility_threshold: float | None
    entry_ts: pd.Timestamp
    entry_raw: float
    exit_ts: pd.Timestamp
    exit_raw: float


@dataclass
class Trade:
    variant: str
    session: str
    direction: str
    first_return_pct: float
    qty: int
    entry: float
    exit: float
    gross_pnl: float
    charges: float
    net_pnl: float


def _charges(model: CostModel, side: Side, value: float, ts: pd.Timestamp) -> float:
    return model.order_charges(
        side, Product.MIS, value, first_sell_of_scrip_today=True, trade_date=ts.date()
    ).total


def _signals() -> list[DaySignal]:
    frame = BarStore(get_settings()).read_raw(
        "NIFTYBEES",
        Timeframe.MINUTE,
        datetime.combine(START, time.min),
        datetime.combine(END, time.max),
    ).to_pandas()
    frame["ts"] = pd.to_datetime(frame["ts"])
    frame["session"] = frame.ts.dt.date
    prior_close: float | None = None
    prior_volumes: list[float] = []
    prior_ranges: list[float] = []
    signals: list[DaySignal] = []
    for session_day, raw_day in frame.groupby("session", sort=True):
        day = _regular_session(raw_day)
        if day.empty:
            continue
        tod = day.ts.dt.time
        first = day[(tod >= time(9, 15)) & (tod < time(9, 45))]
        entry_bar = day[tod == time(15, 0)]
        exit_bar = day[tod == time(15, 29)]
        expected = {time(9, 15 + minute) for minute in range(30)}
        complete = set(first.ts.dt.time) == expected and not entry_bar.empty and not exit_bar.empty
        close = float(day.iloc[-1].close)
        if not complete or prior_close is None:
            prior_close = close
            continue
        first_volume = float(first.volume.sum())
        first_range = (float(first.high.max()) - float(first.low.min())) / prior_close
        volume_threshold = (
            sum(prior_volumes[-20:]) / 20.0 if len(prior_volumes) >= 20 else None
        )
        volatility_threshold = (
            float(np.median(prior_ranges[-20:])) if len(prior_ranges) >= 20 else None
        )
        prior_volumes.append(first_volume)
        prior_ranges.append(first_range)
        first_return = float(first.iloc[-1].close) / prior_close - 1.0
        prior_close = close
        if first_return == 0:
            continue
        eb, xb = entry_bar.iloc[0], exit_bar.iloc[0]
        signals.append(DaySignal(
            str(session_day), "long" if first_return > 0 else "short", first_return,
            first_volume, first_range, volume_threshold, volatility_threshold,
            pd.Timestamp(eb.ts), float(eb.open), pd.Timestamp(xb.ts), float(xb.close),
        ))
    return signals


def run() -> None:
    signals = _signals()
    model = CostModel("zerodha_2026")
    variants = {
        "all_days": lambda signal: True,
        "high_first_half_volume": lambda signal: (
            signal.volume_threshold is not None and signal.first_volume > signal.volume_threshold
        ),
        "high_first_half_volatility": lambda signal: (
            signal.volatility_threshold is not None
            and signal.first_range_pct > signal.volatility_threshold
        ),
    }
    rows: list[Trade] = []
    summaries: list[dict[str, object]] = []
    curves: dict[str, pd.Series] = {}
    for name, eligible in variants.items():
        capital = INITIAL_CAPITAL
        curve: dict[str, float] = {}
        trades: list[Trade] = []
        for signal in signals:
            if not eligible(signal):
                curve[signal.session] = capital
                continue
            entry_side = Side.BUY if signal.direction == "long" else Side.SELL
            exit_side = Side.SELL if signal.direction == "long" else Side.BUY
            entry = _slipped(signal.entry_raw, entry_side)
            exit_px = _slipped(signal.exit_raw, exit_side)
            qty = math.floor(capital / entry)
            signed_move = exit_px - entry if signal.direction == "long" else entry - exit_px
            gross = qty * signed_move
            costs = _charges(model, entry_side, qty * entry, signal.entry_ts) + _charges(
                model, exit_side, qty * exit_px, signal.exit_ts
            )
            net = gross - costs
            capital += net
            trade = Trade(
                name, signal.session, signal.direction, round(signal.first_return * 100, 4),
                qty, entry, exit_px, round(gross, 2), round(costs, 2), round(net, 2),
            )
            trades.append(trade)
            rows.append(trade)
            curve[signal.session] = capital
        equity = pd.Series(curve, dtype=float)
        curves[name] = equity
        returns = equity.pct_change().dropna()
        drawdown = equity / equity.cummax() - 1.0
        net_values = pd.Series([trade.net_pnl for trade in trades], dtype=float)
        summaries.append({
            "variant": name,
            "trades": len(trades),
            "longs": sum(trade.direction == "long" for trade in trades),
            "shorts": sum(trade.direction == "short" for trade in trades),
            "win_rate_pct": round(float((net_values > 0).mean() * 100), 2),
            "final_equity": round(capital, 2),
            "net_return_pct": round((capital / INITIAL_CAPITAL - 1.0) * 100, 2),
            "max_drawdown_pct": round(float(drawdown.min() * 100), 2),
            "sharpe": round(float(returns.mean() / returns.std() * np.sqrt(252)), 3)
            if returns.std() > 0 else None,
            "charges": round(sum(trade.charges for trade in trades), 2),
        })
    out = get_settings().artifacts_dir / "adhoc" / "niftybees_first_last_halfhour" / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([asdict(row) for row in rows]).to_csv(out / "trades.csv", index=False)
    pd.DataFrame(curves).to_csv(out / "equity.csv")
    report = {
        "window": {"start": str(START), "end": str(END)},
        "rules": {
            "signal": "previous close through 09:44 close",
            "trade": "same direction from 15:00 open through 15:29 close",
            "position": "one-times current equity",
            "costs": "MIS plus 10 bps slippage each side",
            "conditional_thresholds": "causal trailing 20-session mean volume / median range",
        },
        "variants": summaries,
    }
    (out / "summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print(f"artifacts -> {out}")


if __name__ == "__main__":
    run()

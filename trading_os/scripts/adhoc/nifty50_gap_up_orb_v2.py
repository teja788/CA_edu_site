"""Predeclared gap-and-go refinements of the Nifty 50 gap-up ORB study."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, time

import pandas as pd
from nifty50_gap_up_orb import END, GAP_MIN, NOTIONAL, START, SYMBOLS, _regular_session, _slipped

from tradingos.config.settings import get_settings
from tradingos.core.models import Product, Side, Timeframe
from tradingos.costs.model import CostModel
from tradingos.data.store import BarStore


@dataclass(frozen=True)
class Variant:
    name: str
    midpoint_stop: bool
    partial_exit: bool


VARIANTS = (
    Variant("confirm_orlow", midpoint_stop=False, partial_exit=False),
    Variant("confirm_midstop", midpoint_stop=True, partial_exit=False),
    Variant("confirm_midstop_partial", midpoint_stop=True, partial_exit=True),
)


@dataclass
class ResultRow:
    variant: str
    symbol: str
    session: str
    gap_pct: float
    entry_ts: str
    entry: float
    stop: float
    qty: int
    exit_reason: str
    gross_pnl: float
    charges: float
    net_pnl: float
    r_multiple: float


def _charges(model: CostModel, side: Side, value: float, ts: pd.Timestamp) -> float:
    return model.order_charges(
        side,
        Product.MIS,
        value,
        first_sell_of_scrip_today=True,
        trade_date=ts.date(),
    ).total


def _simulate(
    variant: Variant,
    symbol: str,
    session_day: object,
    gap: float,
    later: pd.DataFrame,
    entry_i: int,
    range_high: float,
    range_low: float,
    model: CostModel,
) -> ResultRow | None:
    entry_bar = later.loc[entry_i]
    entry_ts = pd.Timestamp(entry_bar["ts"])
    entry = _slipped(max(range_high, float(entry_bar["open"])), Side.BUY)
    stop = (range_high + range_low) / 2.0 if variant.midpoint_stop else range_low
    risk = entry - stop
    qty = math.floor(NOTIONAL / entry)
    if risk <= 0 or qty < 2:
        return None

    one_r = entry + risk
    two_r = entry + 2.0 * risk
    after = later.loc[entry_i:]
    time_bar = after[after["ts"].dt.time == time(15, 15)]
    if time_bar.empty:
        return None

    exits: list[tuple[int, float, pd.Timestamp, str]] = []
    remaining = qty
    partial_done = False
    for _, bar in after.iterrows():
        ts = pd.Timestamp(bar["ts"])
        low = float(bar["low"])
        high = float(bar["high"])
        active_stop = entry if partial_done else stop
        if low <= active_stop:
            exits.append((remaining, active_stop, ts, "breakeven" if partial_done else "stop"))
            remaining = 0
            break
        if variant.partial_exit and not partial_done and high >= one_r:
            first_qty = qty // 2
            exits.append((first_qty, one_r, ts, "partial_1r"))
            remaining -= first_qty
            partial_done = True
            if ts.time() == time(15, 15):
                exits.append((remaining, float(bar["close"]), ts, "time"))
                remaining = 0
                break
            # Do not assume the same minute subsequently reached 2R; its path is
            # unknown. The remainder starts evaluating from the next minute.
            continue
        if high >= two_r:
            exits.append((remaining, two_r, ts, "target_2r"))
            remaining = 0
            break
        if ts.time() == time(15, 15):
            exits.append((remaining, float(bar["close"]), ts, "time"))
            remaining = 0
            break
    if remaining:
        return None

    entry_cost = _charges(model, Side.BUY, qty * entry, entry_ts)
    gross = 0.0
    exit_cost = 0.0
    reasons: list[str] = []
    for exit_qty, raw_px, ts, reason in exits:
        px = _slipped(raw_px, Side.SELL)
        gross += exit_qty * (px - entry)
        exit_cost += _charges(model, Side.SELL, exit_qty * px, ts)
        reasons.append(reason)
    total_cost = entry_cost + exit_cost
    net = gross - total_cost
    return ResultRow(
        variant=variant.name,
        symbol=symbol,
        session=str(session_day),
        gap_pct=round(gap * 100, 4),
        entry_ts=str(entry_ts),
        entry=entry,
        stop=round(stop, 2),
        qty=qty,
        exit_reason="+".join(reasons),
        gross_pnl=round(gross, 2),
        charges=round(total_cost, 2),
        net_pnl=round(net, 2),
        r_multiple=round(net / (qty * risk), 4),
    )


def run() -> None:
    settings = get_settings()
    store = BarStore(settings)
    model = CostModel("zerodha_2026")
    rows: list[ResultRow] = []
    filter_counts = {"gap_days": 0, "strong_close": 0, "high_volume": 0, "breakout": 0}

    for symbol in SYMBOLS:
        frame = store.read_raw(
            symbol,
            Timeframe.MINUTE,
            datetime.combine(START, time.min),
            datetime.combine(END, time.max),
        ).to_pandas()
        frame["ts"] = pd.to_datetime(frame["ts"])
        frame["session"] = frame["ts"].dt.date
        prior_close: float | None = None
        prior_or_volumes: list[float] = []
        for session_day, raw_day in frame.groupby("session", sort=True):
            day = _regular_session(raw_day)
            if day.empty:
                continue
            tod = day["ts"].dt.time
            opening = day[(tod >= time(9, 15)) & (tod < time(9, 30))]
            expected = {time(9, 15 + minute) for minute in range(15)}
            if set(opening["ts"].dt.time) != expected:
                prior_close = float(day.iloc[-1]["close"])
                continue
            or_volume = float(opening["volume"].sum())
            volume_average = (
                sum(prior_or_volumes[-20:]) / 20.0 if len(prior_or_volumes) >= 20 else None
            )
            prior_or_volumes.append(or_volume)
            open_px = float(opening.iloc[0]["open"])
            if prior_close is None:
                prior_close = float(day.iloc[-1]["close"])
                continue
            gap = open_px / prior_close - 1.0
            prior_close = float(day.iloc[-1]["close"])
            if gap < GAP_MIN:
                continue
            filter_counts["gap_days"] += 1
            range_high = float(opening["high"].max())
            range_low = float(opening["low"].min())
            range_width = range_high - range_low
            if range_width <= 0 or float(opening.iloc[-1]["close"]) < range_low + 0.75 * range_width:
                continue
            filter_counts["strong_close"] += 1
            if volume_average is None or or_volume <= volume_average:
                continue
            filter_counts["high_volume"] += 1
            later = day[(tod >= time(9, 30)) & (tod <= time(15, 15))].copy()
            breakout = later[
                (later["ts"].dt.time <= time(10, 30)) & (later["high"] > range_high)
            ]
            if breakout.empty:
                continue
            filter_counts["breakout"] += 1
            entry_i = int(breakout.index[0])
            for variant in VARIANTS:
                result = _simulate(
                    variant, symbol, session_day, gap, later, entry_i,
                    range_high, range_low, model,
                )
                if result is not None:
                    rows.append(result)

    results = pd.DataFrame([asdict(row) for row in rows])
    out = settings.artifacts_dir / "adhoc" / "nifty50_gap_up_orb_v2" / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    results.to_csv(out / "trades.csv", index=False)
    summaries: list[dict[str, object]] = []
    for variant, group in results.groupby("variant"):
        positive = group.loc[group.net_pnl > 0, "net_pnl"].sum()
        negative = -group.loc[group.net_pnl < 0, "net_pnl"].sum()
        summaries.append({
            "variant": variant,
            "trades": len(group),
            "wins": int((group.net_pnl > 0).sum()),
            "win_rate_pct": round(float((group.net_pnl > 0).mean() * 100), 2),
            "gross_after_slippage": round(float(group.gross_pnl.sum()), 2),
            "charges": round(float(group.charges.sum()), 2),
            "net_pnl": round(float(group.net_pnl.sum()), 2),
            "avg_r": round(float(group.r_multiple.mean()), 4),
            "profit_factor": round(float(positive / negative), 3) if negative else None,
            "profitable_symbols": int((group.groupby("symbol").net_pnl.sum() > 0).sum()),
        })
    report = {
        "window": {"start": str(START), "end": str(END)},
        "common_filters": {
            "gap_min_pct": 1.0,
            "opening_range_close_location_min": 0.75,
            "opening_range_volume": "above trailing 20-session mean",
            "breakout_deadline": "10:30",
            "slippage_bps_each_side": 10.0,
            "product": "MIS",
        },
        "filter_counts": filter_counts,
        "variants": summaries,
        "caveats": [
            "current Nifty 50 constituents applied historically",
            "₹1L independent notional per signal; simultaneous capital unconstrained",
            "same-minute ambiguity is resolved conservatively",
        ],
    }
    (out / "summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print(f"artifacts -> {out}")


if __name__ == "__main__":
    run()

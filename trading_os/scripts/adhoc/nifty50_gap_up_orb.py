"""Fetch and backtest a gap-up 15-minute opening-range breakout on Nifty 50.

Rules fixed for this study:
* current Nifty 50 constituents (survivorship caveat applies)
* gap >= 1% versus the prior session's final minute close
* range = 09:15..09:29; enter on the first later bar that breaks its high
* stop = opening-range low; target = 2R; pessimistic stop-first same-bar rule
* otherwise exit on the 15:15 bar close; one trade per symbol/session
* ₹100,000 notional per trade, integer shares, Zerodha CNC charges and default
  schedule slippage on both entry and exit
"""

from __future__ import annotations

import argparse
import json
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import date, datetime, time
from pathlib import Path

import pandas as pd

from tradingos.config.settings import get_settings
from tradingos.core.models import Product, Side, Timeframe
from tradingos.costs.model import CostModel
from tradingos.data.auth import KiteAuth
from tradingos.data.fetcher import HistoricalFetcher
from tradingos.data.instruments import sync_instruments, token_for
from tradingos.data.ratelimit import TokenBucket
from tradingos.data.store import BarStore
from tradingos.engine.event.execution import ChargeCalculator

SYMBOLS = [
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK",
    "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BEL", "BHARTIARTL",
    "CIPLA", "COALINDIA", "DRREDDY", "EICHERMOT", "ETERNAL", "GRASIM",
    "HCLTECH", "HDFCBANK", "HDFCLIFE", "HINDALCO", "HINDUNILVR",
    "ICICIBANK", "INDIGO", "INFY", "ITC", "JIOFIN", "JSWSTEEL",
    "KOTAKBANK", "LT", "M&M", "MARUTI", "MAXHEALTH", "NESTLEIND",
    "NTPC", "ONGC", "POWERGRID", "RELIANCE", "SBILIFE", "SHRIRAMFIN",
    "SBIN", "SUNPHARMA", "TCS", "TATACONSUM", "TMPV", "TATASTEEL",
    "TECHM", "TITAN", "TRENT", "ULTRACEMCO", "WIPRO",
]

START = date(2024, 7, 13)
END = date(2026, 7, 10)
NOTIONAL = 100_000.0
GAP_MIN = 0.01
SLIPPAGE_BPS = 10.0  # zerodha_2026 large-cap default; all names are Nifty 50


@dataclass
class TradeRow:
    symbol: str
    session: str
    gap_pct: float
    entry_ts: str
    entry: float
    stop: float
    target: float
    exit_ts: str
    exit: float
    reason: str
    qty: int
    gross_pnl: float
    charges: float
    net_pnl: float
    r_multiple: float


def fetch_data() -> None:
    settings = get_settings()
    kite = KiteAuth(settings).kite()
    sync_instruments(kite, settings)
    store = BarStore(settings)
    fetcher = HistoricalFetcher(kite, TokenBucket(rate=3.0, capacity=3))
    def fetch_one(i: int, symbol: str) -> str:
        path = settings.raw_dir / Timeframe.MINUTE.value / f"{symbol}.parquet"
        if path.exists():
            timestamps = pd.to_datetime(pd.read_parquet(path, columns=["ts"])["ts"])
            # START is a Saturday; the first expected session is the following
            # Monday. Do not mistake an unrelated/partial minute file for full
            # two-year coverage when resuming a download.
            if (
                not timestamps.empty
                and timestamps.min().date() <= date(2024, 7, 15)
                and timestamps.max().date() >= END
            ):
                return f"[{i:02d}/50] {symbol}: already complete"
        try:
            frame = fetcher.fetch(symbol, token_for(symbol, settings), Timeframe.MINUTE, START, END)
            added = store.write_raw(symbol, Timeframe.MINUTE, frame)
            return f"[{i:02d}/50] {symbol}: {added:,} bars"
        except Exception as exc:  # one unavailable constituent must not lose the batch
            return f"[{i:02d}/50] {symbol}: ERROR {exc}"

    # HTTP response latency dominates a sequential download. Three workers keep
    # requests in flight while the shared TokenBucket still enforces Kite's
    # account-wide historical-data limit of three requests per second.
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            pool.submit(fetch_one, i, symbol): symbol
            for i, symbol in enumerate(SYMBOLS, 1)
        }
        for future in as_completed(futures):
            print(future.result(), flush=True)


def _slipped(price: float, side: Side) -> float:
    direction = 1.0 if side == Side.BUY else -1.0
    return round(price * (1.0 + direction * SLIPPAGE_BPS / 10_000.0), 2)


def _regular_session(day: pd.DataFrame) -> pd.DataFrame:
    """Return NSE continuous-session bars only, ordered and de-duplicated."""
    ordered = day.sort_values("ts").drop_duplicates("ts", keep="last")
    tod = ordered["ts"].dt.time
    return ordered[(tod >= time(9, 15)) & (tod <= time(15, 29))]


def backtest() -> Path:
    settings = get_settings()
    store = BarStore(settings)
    costs = ChargeCalculator(CostModel("zerodha_2026"), Product.MIS)
    trades: list[TradeRow] = []
    coverage: dict[str, dict[str, object]] = {}

    for symbol in SYMBOLS:
        if not store.has_raw(symbol, Timeframe.MINUTE):
            coverage[symbol] = {"status": "missing"}
            continue
        frame = store.read_raw(
            symbol,
            Timeframe.MINUTE,
            datetime.combine(START, time.min),
            datetime.combine(END, time.max),
        ).to_pandas()
        if frame.empty:
            coverage[symbol] = {"status": "empty"}
            continue
        frame["ts"] = pd.to_datetime(frame["ts"])
        frame["session"] = frame["ts"].dt.date
        days = list(frame.groupby("session", sort=True))
        coverage[symbol] = {
            "status": "ok",
            "first": str(days[0][0]),
            "last": str(days[-1][0]),
            "sessions": len(days),
            "bars": len(frame),
        }
        prior_close: float | None = None
        for session_day, day in days:
            day = _regular_session(day)
            if day.empty:
                continue
            if prior_close is None:
                prior_close = float(day.iloc[-1]["close"])
                continue
            # Do not let pre-open/post-close records redefine the gap. A
            # missing 09:15 bar makes both the gap and opening range invalid.
            open_bar = day[day["ts"].dt.time == time(9, 15)]
            if open_bar.empty:
                prior_close = float(day.iloc[-1]["close"])
                continue
            open_px = float(open_bar.iloc[0]["open"])
            gap = open_px / prior_close - 1.0
            prior_close = float(day.iloc[-1]["close"])
            if gap < GAP_MIN:
                continue
            tod = day["ts"].dt.time
            opening = day[(tod >= time(9, 15)) & (tod < time(9, 30))]
            later = day[(tod >= time(9, 30)) & (tod <= time(15, 15))]
            # Require every opening-range minute and the stipulated time-exit
            # candle; otherwise silently using an incomplete range or an
            # earlier close changes the strategy being tested.
            opening_minutes = set(opening["ts"].dt.time)
            required_opening = {time(9, minute) for minute in range(15, 30)}
            if opening_minutes != required_opening or time(15, 15) not in set(later["ts"].dt.time):
                continue
            range_high = float(opening["high"].max())
            range_low = float(opening["low"].min())
            breakout = later[later["high"] > range_high]
            if breakout.empty:
                continue
            entry_i = breakout.index[0]
            entry_bar = day.loc[entry_i]
            raw_entry = max(range_high, float(entry_bar["open"]))
            entry = _slipped(raw_entry, Side.BUY)
            risk = entry - range_low
            if risk <= 0:
                continue
            target = entry + 2.0 * risk
            qty = math.floor(NOTIONAL / entry)
            if qty <= 0:
                continue
            after = later.loc[entry_i:]
            exit_raw = float(after.iloc[-1]["close"])
            exit_ts = pd.Timestamp(after.iloc[-1]["ts"])
            reason = "time"
            for _, bar in after.iterrows():
                # Conservative ambiguity policy: if both touch in one minute,
                # assume the stop was reached first.
                if float(bar["low"]) <= range_low:
                    exit_raw = range_low
                    exit_ts = pd.Timestamp(bar["ts"])
                    reason = "stop"
                    break
                if float(bar["high"]) >= target:
                    exit_raw = target
                    exit_ts = pd.Timestamp(bar["ts"])
                    reason = "target"
                    break
            exit_px = _slipped(exit_raw, Side.SELL)
            entry_value = qty * entry
            exit_value = qty * exit_px
            entry_cost = costs.charges(Side.BUY, symbol, entry_value, pd.Timestamp(entry_bar["ts"]).to_pydatetime())
            exit_cost = costs.charges(Side.SELL, symbol, exit_value, exit_ts.to_pydatetime())
            gross = qty * (exit_px - entry)
            total_cost = entry_cost + exit_cost
            net = gross - total_cost
            trades.append(TradeRow(
                symbol=symbol, session=str(session_day), gap_pct=gap * 100,
                entry_ts=str(entry_bar["ts"]), entry=entry, stop=range_low,
                target=round(target, 2), exit_ts=str(exit_ts), exit=exit_px,
                reason=reason, qty=qty, gross_pnl=round(gross, 2),
                charges=round(total_cost, 2), net_pnl=round(net, 2),
                r_multiple=round(net / (qty * risk), 4),
            ))

    out = settings.artifacts_dir / "adhoc" / "nifty50_gap_up_orb" / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    trade_frame = pd.DataFrame([asdict(t) for t in trades])
    trade_frame.to_csv(out / "trades.csv", index=False)
    if trade_frame.empty:
        summary = {"trades": 0, "coverage": coverage}
    else:
        daily = trade_frame.groupby("session")["net_pnl"].sum()
        equity = NOTIONAL + daily.cumsum()
        summary = {
            "rules": {"gap_min_pct": 1.0, "opening_range_minutes": 15, "target_r": 2.0,
                      "time_exit": "15:15", "notional_per_trade": NOTIONAL,
                      "slippage_bps_each_side": SLIPPAGE_BPS,
                      "product": "MIS",
                      "same_bar_ambiguity": "stop_first"},
            "window": {"start": str(START), "end": str(END)},
            "trades": len(trade_frame),
            "wins": int((trade_frame["net_pnl"] > 0).sum()),
            "win_rate_pct": round(float((trade_frame["net_pnl"] > 0).mean() * 100), 2),
            "net_pnl": round(float(trade_frame["net_pnl"].sum()), 2),
            "avg_net_pnl": round(float(trade_frame["net_pnl"].mean()), 2),
            "avg_r": round(float(trade_frame["r_multiple"].mean()), 4),
            "profit_factor": round(float(trade_frame.loc[trade_frame.net_pnl > 0, "net_pnl"].sum() /
                                         -trade_frame.loc[trade_frame.net_pnl < 0, "net_pnl"].sum()), 3),
            "max_cumulative_drawdown_rupees": round(
                float((daily.cumsum() - daily.cumsum().cummax()).min()), 2
            ),
            "exit_reasons": trade_frame["reason"].value_counts().to_dict(),
            "total_charges": round(float(trade_frame["charges"].sum()), 2),
            "coverage": coverage,
            "caveats": [
                "current Nifty 50 constituents are applied historically (survivorship bias)",
                "₹1L independent notional per signal; simultaneous portfolio capital is not constrained",
                "minute bars do not reveal intrabar path; stop is assumed before target when both touch",
            ],
        }
        equity.rename("equity").to_csv(out / "daily_equity.csv")
        trade_frame.groupby("symbol").agg(
            trades=("net_pnl", "size"), net_pnl=("net_pnl", "sum"),
            win_rate=("net_pnl", lambda x: (x > 0).mean()), avg_r=("r_multiple", "mean"),
        ).sort_values("net_pnl", ascending=False).to_csv(out / "per_symbol.csv")
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps({k: v for k, v in summary.items() if k != "coverage"}, indent=2))
    print(f"artifacts -> {out}")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    if args.fetch:
        fetch_data()
    backtest()


if __name__ == "__main__":
    main()

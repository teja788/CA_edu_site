"""Deterministic synthetic tick generators for tests (mirrors synthetic.py).

Never call live APIs from tests -- build fixtures here. All generators are
seeded and pure: same args -> same data.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any

import numpy as np

from tradingos.core.models import Tick


def synthetic_ticks(
    symbol: str = "TEST",
    token: int = 1001,
    day: date = date(2024, 1, 15),
    n: int = 200,
    s0: float = 100.0,
    spread_bps: float = 5.0,
    seed: int | None = None,
) -> list[Tick]:
    """Random-walk ticks between 09:15:01 and 15:29:59 IST.

    Monotonically increasing `ts`, `bid < last_price < ask`, cumulative volume.
    Seed defaults to a stable hash of the symbol so different symbols get
    different but reproducible paths.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    if seed is None:
        seed = int.from_bytes(symbol.encode(), "little") % (2**31)
    rng = np.random.default_rng(seed)

    start = datetime.combine(day, time(9, 15, 1))
    end = datetime.combine(day, time(15, 29, 59))
    span_seconds = (end - start).total_seconds()

    # Strictly increasing offsets: cumulative positive gaps, rescaled to span.
    gaps = rng.uniform(0.05, 1.0, size=n)
    offsets = np.cumsum(gaps)
    offsets = offsets / offsets[-1] * span_seconds
    timestamps = [start + timedelta(seconds=float(o)) for o in offsets]

    tick_vol = 0.0006
    rets = tick_vol * rng.standard_normal(n)
    price = s0 * np.exp(np.cumsum(rets))

    half_spread_frac = (spread_bps / 1e4) / 2.0
    half_spread = np.maximum(price * half_spread_frac, 0.01)
    bid = price - half_spread
    ask = price + half_spread

    price = np.round(price, 2)
    bid = np.round(bid, 2)
    ask = np.round(ask, 2)
    # Guard against rounding collapsing the spread to zero.
    bid = np.minimum(bid, price - 0.01)
    ask = np.maximum(ask, price + 0.01)

    volume_increments = rng.integers(1, 50, size=n)
    cum_volume = np.cumsum(volume_increments)

    return [
        Tick(
            symbol=symbol,
            instrument_token=token,
            ts=timestamps[i],
            last_price=float(price[i]),
            bid=float(bid[i]),
            ask=float(ask[i]),
            volume=int(cum_volume[i]),
        )
        for i in range(n)
    ]


def kite_tick_dicts(ticks: list[Tick]) -> list[dict[str, Any]]:
    """Render `ticks` in raw Kite WebSocket payload shape.

    Shape matches what `TickStreamer` maps from: instrument_token, last_price,
    volume_traded, exchange_timestamp, depth.buy/sell (first level only).
    """
    dicts: list[dict[str, Any]] = []
    for t in ticks:
        depth: dict[str, list[dict[str, Any]]] = {"buy": [], "sell": []}
        if t.bid is not None:
            depth["buy"].append({"price": t.bid, "quantity": 1, "orders": 1})
        if t.ask is not None:
            depth["sell"].append({"price": t.ask, "quantity": 1, "orders": 1})
        dicts.append(
            {
                "tradable": True,
                "mode": "full",
                "instrument_token": t.instrument_token,
                "last_price": t.last_price,
                "volume_traded": t.volume,
                "exchange_timestamp": t.ts,
                "last_trade_time": t.ts,
                "depth": depth,
            }
        )
    return dicts

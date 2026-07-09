"""Deterministic synthetic OHLCV generators for tests.

Never call live APIs from tests — build fixtures here. All generators are
seeded and pure: same args -> same data.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

import numpy as np
import pandas as pd


def trading_days(start: date, end: date, holidays: set[date] | None = None) -> pd.DatetimeIndex:
    """Mon-Fri days in [start, end] minus holidays, as tz-naive timestamps."""
    holidays = holidays or set()
    days = pd.date_range(start, end, freq="B")
    return pd.DatetimeIndex([d for d in days if d.date() not in holidays])


def synthetic_daily(
    symbol: str = "TEST",
    start: date = date(2015, 1, 1),
    end: date = date(2024, 12, 31),
    seed: int | None = None,
    s0: float = 100.0,
    drift: float = 0.08,
    vol: float = 0.22,
    volume_base: int = 500_000,
    holidays: set[date] | None = None,
) -> pd.DataFrame:
    """Geometric-Brownian daily OHLCV, indexed by tz-naive IST DatetimeIndex.

    Seed defaults to a stable hash of the symbol so different symbols get
    different but reproducible paths.
    """
    idx = trading_days(start, end, holidays)
    n = len(idx)
    if seed is None:
        seed = abs(hash(symbol)) % (2**31)
        seed = int.from_bytes(symbol.encode(), "little") % (2**31)  # hash() is salted; stable
    rng = np.random.default_rng(seed)
    dt = 1.0 / 252.0
    rets = (drift - 0.5 * vol**2) * dt + vol * np.sqrt(dt) * rng.standard_normal(n)
    close = s0 * np.exp(np.cumsum(rets))
    open_ = np.empty(n)
    open_[0] = s0
    open_[1:] = close[:-1] * np.exp(vol * np.sqrt(dt) * 0.3 * rng.standard_normal(n - 1))
    spread = np.abs(rng.standard_normal(n)) * vol * np.sqrt(dt) * close
    high = np.maximum(open_, close) + spread
    low = np.minimum(open_, close) - spread
    low = np.maximum(low, 0.05)
    volume = (volume_base * np.exp(0.5 * rng.standard_normal(n))).astype(np.int64)
    return pd.DataFrame(
        {
            "open": np.round(open_, 2),
            "high": np.round(high, 2),
            "low": np.round(low, 2),
            "close": np.round(close, 2),
            "volume": volume,
        },
        index=idx,
    )


def synthetic_universe(
    symbols: list[str],
    start: date = date(2015, 1, 1),
    end: date = date(2024, 12, 31),
    holidays: set[date] | None = None,
) -> dict[str, pd.DataFrame]:
    return {s: synthetic_daily(s, start, end, holidays=holidays) for s in symbols}


def synthetic_minute(
    symbol: str = "TEST",
    day: date = date(2024, 1, 15),
    seed: int | None = None,
    s0: float = 100.0,
    vol: float = 0.18,
) -> pd.DataFrame:
    """One session (09:15-15:29 bar opens) of minute OHLCV."""
    if seed is None:
        seed = int.from_bytes(symbol.encode(), "little") % (2**31)
    rng = np.random.default_rng(seed + day.toordinal())
    start_ts = datetime.combine(day, time(9, 15))
    idx = pd.DatetimeIndex([start_ts + timedelta(minutes=i) for i in range(375)])
    n = len(idx)
    dt = 1.0 / (252.0 * 375.0)
    rets = vol * np.sqrt(dt) * rng.standard_normal(n)
    close = s0 * np.exp(np.cumsum(rets))
    open_ = np.empty(n)
    open_[0] = s0
    open_[1:] = close[:-1]
    spread = np.abs(rng.standard_normal(n)) * vol * np.sqrt(dt) * close * 0.5
    high = np.maximum(open_, close) + spread
    low = np.minimum(open_, close) - spread
    volume = (2000 * np.exp(0.8 * rng.standard_normal(n))).astype(np.int64)
    return pd.DataFrame(
        {
            "open": np.round(open_, 2),
            "high": np.round(high, 2),
            "low": np.round(low, 2),
            "close": np.round(close, 2),
            "volume": volume,
        },
        index=idx,
    )

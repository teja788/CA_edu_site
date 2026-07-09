"""Uniform signal/indicator registry.

Three tiers, one namespace:
  1. built-in pandas-ta wrappers (registered in strategies/signals/builtin.py)
  2. custom quant/factor signals   (strategies/signals/factors.py)
  3. user plugins                   (strategies/signals/custom/*.py, auto-discovered)

A signal function takes a per-symbol OHLCV pandas DataFrame (index: tz-naive IST
DatetimeIndex; columns open/high/low/close/volume, plus optionally
total_return_close) and params, and returns a pandas Series aligned to the
input index. Row t may use ONLY data at rows <= t — the look-ahead detector
test enforces this for every registered signal.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import pkgutil
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from tradingos.core.errors import ConfigError
from tradingos.core.logging import get_logger

logger = get_logger(__name__)

SignalFn = Callable[..., pd.Series]


@dataclass
class SignalDef:
    name: str
    fn: SignalFn
    description: str = ""
    defaults: dict[str, Any] = field(default_factory=dict)
    tier: str = "custom"  # builtin | factor | custom


_REGISTRY: dict[str, SignalDef] = {}
_DISCOVERED = False


def register_signal(
    name: str, description: str = "", tier: str = "custom", **defaults: Any
) -> Callable[[SignalFn], SignalFn]:
    """Decorator: @register_signal("my_indicator") on fn(df, **params) -> pd.Series."""

    def deco(fn: SignalFn) -> SignalFn:
        key = name.lower()
        if key in _REGISTRY:
            logger.warning("signal %r re-registered, overriding", key)
        _REGISTRY[key] = SignalDef(
            name=key, fn=fn, description=description, defaults=defaults, tier=tier
        )
        return fn

    return deco


def get_signal(name: str) -> SignalDef:
    ensure_discovered()
    key = name.lower()
    if key not in _REGISTRY:
        raise ConfigError(
            f"unknown signal {name!r}. Registered: {', '.join(sorted(_REGISTRY)[:30])} ..."
        )
    return _REGISTRY[key]


def list_signals() -> list[SignalDef]:
    ensure_discovered()
    return sorted(_REGISTRY.values(), key=lambda d: (d.tier, d.name))


def compute_signal(name: str, df: pd.DataFrame, params: dict[str, Any]) -> pd.Series:
    """Compute one signal on one symbol's OHLCV frame."""
    sig = get_signal(name)
    merged = {**sig.defaults, **params}
    out = sig.fn(df, **merged)
    if not isinstance(out, pd.Series):
        raise ConfigError(f"signal {name!r} returned {type(out).__name__}, expected pd.Series")
    if len(out) != len(df):
        raise ConfigError(f"signal {name!r} returned wrong length {len(out)} != {len(df)}")
    out.index = df.index
    return out.astype("float64")


def signal_cache_key(symbol: str, name: str, params: dict[str, Any], snapshot_id: str) -> str:
    """Stable cache key so parameter-grid runs never recompute identical signals."""
    payload = json.dumps({"n": name.lower(), "p": params}, sort_keys=True, default=str)
    h = hashlib.sha256(f"{symbol}|{payload}|{snapshot_id}".encode()).hexdigest()[:20]
    return f"{symbol}_{name.lower()}_{h}"


def ensure_discovered() -> None:
    """Import built-in signal modules and auto-discover user plugins in
    strategies/signals/custom/. Idempotent; called lazily on first lookup."""
    global _DISCOVERED
    if _DISCOVERED:
        return
    _DISCOVERED = True
    import tradingos.strategies.filters  # noqa: F401
    import tradingos.strategies.signals.builtin  # noqa: F401
    import tradingos.strategies.signals.custom as custom_pkg
    import tradingos.strategies.signals.factors  # noqa: F401

    for mod in pkgutil.iter_modules(custom_pkg.__path__):
        if mod.name.startswith("_"):
            continue
        importlib.import_module(f"tradingos.strategies.signals.custom.{mod.name}")
        logger.info("discovered custom signal module: %s", mod.name)


# ---- filters (regime / eligibility) share the same pattern ----

FilterFn = Callable[..., pd.Series]  # returns boolean Series
_FILTERS: dict[str, FilterDef] = {}


@dataclass
class FilterDef:
    name: str
    fn: FilterFn
    description: str = ""


def register_filter(name: str, description: str = "") -> Callable[[FilterFn], FilterFn]:
    def deco(fn: FilterFn) -> FilterFn:
        _FILTERS[name.lower()] = FilterDef(name=name.lower(), fn=fn, description=description)
        return fn

    return deco


def get_filter(name: str) -> FilterDef:
    ensure_discovered()
    key = name.lower()
    if key not in _FILTERS:
        raise ConfigError(f"unknown filter {name!r}. Registered: {sorted(_FILTERS)}")
    return _FILTERS[key]

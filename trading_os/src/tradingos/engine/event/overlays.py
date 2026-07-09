"""Risk overlays for the event-driven engine.

Overlays run at every bar *close* (through a :class:`DataView` bound to that
bar's 15:30 visibility) and can either exit individual positions or halt the
whole book. They are stateful objects — instantiated once per run so a trailing
stop can ratchet across bars — registered by name in a small local registry
(the same pattern as ``register_filter``), and configured from
:class:`~tradingos.config.schemas.OverlaySpec`.

Two families:

* **Per-position trailing stops** (``trailing_stop_atr``, ``trailing_stop_pct``)
  produce exit orders queued for the next open. Both are *monotone*: the stop
  level never loosens over the life of a position, and resets when the position
  is re-entered (a new lot ``entry_ts``).
* **Portfolio kill switch** (``portfolio_drawdown_stop``) liquidates everything
  and halts all new entries for the remainder of the run once the equity
  drawdown from the run's peak breaches ``max_dd``.

ATR is computed by a *local, causal* helper (``_atr``) rather than the signal
registry, so this module has no dependency on the concurrently-edited signal
modules.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

import pandas as pd

from tradingos.config.schemas import OverlaySpec
from tradingos.core.errors import ConfigError
from tradingos.core.logging import get_logger
from tradingos.engine.dataview import DataView

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# context / decision value objects
# ---------------------------------------------------------------------------


@dataclass
class OverlayContext:
    """Everything an overlay may read at a bar close (all point-in-time)."""

    now: pd.Timestamp
    dv: DataView
    holdings: dict[str, int]  # symbol -> qty (>0)
    entry_ts: dict[str, datetime]  # symbol -> lot entry timestamp
    equity: float  # net equity marked at this close


@dataclass
class OverlayDecision:
    """What an overlay wants the engine to do this bar."""

    exits: dict[str, str] = field(default_factory=dict)  # symbol -> exit reason
    liquidate_all: bool = False
    halt_entries: bool = False
    warnings: list[str] = field(default_factory=list)


class Overlay(Protocol):
    def evaluate(self, ctx: OverlayContext) -> OverlayDecision:
        ...


# ---------------------------------------------------------------------------
# registry
# ---------------------------------------------------------------------------

_OVERLAYS: dict[str, type[Overlay]] = {}


def register_overlay(name: str) -> Callable[[type[Overlay]], type[Overlay]]:
    def deco(cls: type[Overlay]) -> type[Overlay]:
        _OVERLAYS[name.lower()] = cls
        return cls

    return deco


def make_overlay(spec: OverlaySpec) -> Overlay:
    """Instantiate the overlay named by ``spec`` with its params."""
    key = spec.name.lower()
    if key not in _OVERLAYS:
        raise ConfigError(f"unknown overlay {spec.name!r}. Registered: {sorted(_OVERLAYS)}")
    return _OVERLAYS[key](**spec.params)


# ---------------------------------------------------------------------------
# local causal ATR
# ---------------------------------------------------------------------------


def _atr(df: pd.DataFrame, window: int) -> float | None:
    """Latest ATR value from a visible OHLCV frame, or ``None`` if not warmed up.

    True range TR_t = max(high-low, |high - close_{t-1}|, |low - close_{t-1}|);
    ATR is the simple rolling mean of TR over ``window`` bars. Row t uses only
    rows <= t (the shift of the previous close is causal), so this is safe to
    call on a DataView-sliced frame.
    """
    if len(df) < window + 1:
        return None
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    atr = tr.rolling(window=window, min_periods=window).mean()
    val = atr.iloc[-1]
    if pd.isna(val):
        return None
    return float(val)


# ---------------------------------------------------------------------------
# trailing stops
# ---------------------------------------------------------------------------


@dataclass
class _StopState:
    entry_ts: datetime
    stop: float


@register_overlay("trailing_stop_atr")
class TrailingStopATR:
    """Chandelier-style trailing stop: ``stop_t = max(stop_{t-1}, close_t -
    multiple * ATR_t)`` since entry, evaluated on a closing basis. Exit reason
    ``"trailing_stop"``."""

    def __init__(self, atr_window: int = 14, multiple: float = 3.0) -> None:
        self.atr_window = int(atr_window)
        self.multiple = float(multiple)
        self._state: dict[str, _StopState] = {}

    def evaluate(self, ctx: OverlayContext) -> OverlayDecision:
        exits: dict[str, str] = {}
        for sym in sorted(ctx.holdings):
            df = ctx.dv.history(sym)
            if df.empty:
                continue
            close_t = float(df["close"].iloc[-1])
            entry_ts = ctx.entry_ts.get(sym)
            st = self._state.get(sym)
            if st is None or (entry_ts is not None and st.entry_ts != entry_ts):
                st = _StopState(entry_ts=entry_ts or ctx.now.to_pydatetime(), stop=float("-inf"))
                self._state[sym] = st
            atr = _atr(df, self.atr_window)
            if atr is not None:
                st.stop = max(st.stop, close_t - self.multiple * atr)
            if st.stop != float("-inf") and close_t < st.stop:
                exits[sym] = "trailing_stop"
        self._prune(ctx.holdings)
        return OverlayDecision(exits=exits)

    def _prune(self, holdings: dict[str, int]) -> None:
        for sym in [s for s in self._state if s not in holdings]:
            del self._state[sym]


@register_overlay("trailing_stop_pct")
class TrailingStopPct:
    """Percentage trailing stop: ``stop = peak_close_since_entry * (1 - pct)``.
    Exit reason ``"trailing_stop"``."""

    def __init__(self, pct: float = 0.15) -> None:
        self.pct = float(pct)
        self._peak: dict[str, _StopState] = {}

    def evaluate(self, ctx: OverlayContext) -> OverlayDecision:
        exits: dict[str, str] = {}
        for sym in sorted(ctx.holdings):
            df = ctx.dv.history(sym)
            if df.empty:
                continue
            close_t = float(df["close"].iloc[-1])
            entry_ts = ctx.entry_ts.get(sym)
            st = self._peak.get(sym)
            if st is None or (entry_ts is not None and st.entry_ts != entry_ts):
                st = _StopState(entry_ts=entry_ts or ctx.now.to_pydatetime(), stop=close_t)
                self._peak[sym] = st
            st.stop = max(st.stop, close_t)  # ``stop`` field holds the running peak
            stop_level = st.stop * (1.0 - self.pct)
            if close_t < stop_level:
                exits[sym] = "trailing_stop"
        for sym in [s for s in self._peak if s not in ctx.holdings]:
            del self._peak[sym]
        return OverlayDecision(exits=exits)


@register_overlay("portfolio_drawdown_stop")
class PortfolioDrawdownStop:
    """Kill switch: once equity drawdown from the run peak reaches ``max_dd``,
    liquidate everything at the next open and halt all new entries for the rest
    of the run. Fires its liquidation exactly once."""

    def __init__(self, max_dd: float = 0.25) -> None:
        self.max_dd = float(max_dd)
        self._peak: float = float("-inf")
        self._fired = False

    def evaluate(self, ctx: OverlayContext) -> OverlayDecision:
        self._peak = max(self._peak, ctx.equity)
        if self._peak > 0 and (self._peak - ctx.equity) / self._peak >= self.max_dd:
            if not self._fired:
                self._fired = True
                dd = (self._peak - ctx.equity) / self._peak
                msg = (
                    f"KILL SWITCH: portfolio drawdown {dd:.1%} >= {self.max_dd:.1%} at "
                    f"{ctx.now.date()}; liquidating all positions and halting new entries."
                )
                logger.warning(msg)
                return OverlayDecision(liquidate_all=True, halt_entries=True, warnings=[msg])
            return OverlayDecision(halt_entries=True)
        return OverlayDecision()


__all__ = [
    "Overlay",
    "OverlayContext",
    "OverlayDecision",
    "make_overlay",
    "register_overlay",
]

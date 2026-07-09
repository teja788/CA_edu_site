"""Backtest engines. The event-driven engine is the realistic-fills reference;
the vectorized engine (separate module) trades accuracy for speed.

``VectorizedEngine`` is re-exported for symmetry, but importing it here does NOT
import vectorbt — the heavy numba import stays lazy inside ``run``.
"""

from __future__ import annotations

from tradingos.engine.event.engine import EventEngine
from tradingos.engine.vectorized.engine import VectorizedEngine

__all__ = ["EventEngine", "VectorizedEngine"]

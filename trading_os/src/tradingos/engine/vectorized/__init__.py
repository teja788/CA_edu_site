"""Vectorized (fast / screening) backtest engine, built on vectorbt.

The heavy ``vectorbt`` import (numba, ~30s cold) is deferred to
:meth:`VectorizedEngine.run`, so importing this package stays cheap.
"""

from __future__ import annotations

from tradingos.engine.vectorized.engine import VectorizedEngine

__all__ = ["VectorizedEngine"]

"""Engine-facing protocols. Engines depend on these, never on concrete
data-layer or broker classes (no circular imports).
"""

from __future__ import annotations

from datetime import date
from typing import Protocol, runtime_checkable

from tradingos.config.schemas import StrategyConfig, UniverseSpec
from tradingos.engine.dataview import MarketData
from tradingos.engine.result import BacktestResult


@runtime_checkable
class UniverseResolver(Protocol):
    """Resolves candidate symbols as of a date — point-in-time when backed by
    the membership table. Implementations must append a loud warning string to
    `warnings` (and log it) when PIT data is unavailable for the period."""

    def resolve(self, spec: UniverseSpec, on: date, data: MarketData) -> list[str]:
        ...

    @property
    def warnings(self) -> list[str]:
        ...


class StaticUniverseResolver:
    """Uses spec.symbols (or all symbols in data). For tests and ad-hoc runs.
    NOT point-in-time — emits the survivorship-bias warning when the spec asked
    for point_in_time universes."""

    def __init__(self) -> None:
        self._warnings: list[str] = []

    @property
    def warnings(self) -> list[str]:
        return self._warnings

    def resolve(self, spec: UniverseSpec, on: date, data: MarketData) -> list[str]:
        if spec.point_in_time and spec.symbols is None:
            msg = (
                f"SURVIVORSHIP BIAS: no point-in-time membership data for index "
                f"{spec.index!r}; using all available symbols as of today. "
                "Results overstate performance."
            )
            if msg not in self._warnings:
                self._warnings.append(msg)
        return spec.symbols if spec.symbols is not None else data.symbols


@runtime_checkable
class Engine(Protocol):
    def run(
        self,
        config: StrategyConfig,
        data: MarketData,
        universe: UniverseResolver,
    ) -> BacktestResult:
        ...

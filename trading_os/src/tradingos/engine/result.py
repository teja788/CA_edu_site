"""BacktestResult: the common output contract of both engines, consumed by
analytics, experiments and reports. Serializable to an artifacts directory so
every run is reproducible and comparable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from tradingos.config.schemas import EngineMode, StrategyConfig
from tradingos.core.models import Trade


@dataclass
class BacktestResult:
    config: StrategyConfig
    engine: EngineMode
    start: date
    end: date
    capital: float
    equity: pd.Series  # net-of-costs equity curve, indexed by bar ts
    gross_equity: pd.Series  # before transaction costs
    trades: list[Trade] = field(default_factory=list)
    total_costs: float = 0.0
    warnings: list[str] = field(default_factory=list)  # e.g. survivorship-bias warning
    meta: dict[str, Any] = field(default_factory=dict)  # data snapshot id, git hash, ...

    @property
    def returns(self) -> pd.Series:
        """Daily (bar-to-bar) net returns."""
        return self.equity.pct_change().fillna(0.0)

    @property
    def costs_pct_of_capital(self) -> float:
        return self.total_costs / self.capital if self.capital else 0.0

    def save(self, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        eq = pd.DataFrame({"equity": self.equity, "gross_equity": self.gross_equity})
        eq.index.name = "ts"
        eq.reset_index().to_parquet(out_dir / "equity.parquet", index=False)
        (out_dir / "trades.json").write_text(
            json.dumps([t.model_dump(mode="json") for t in self.trades], indent=1)
        )
        meta = {
            "config": self.config.model_dump(mode="json"),
            "config_hash": self.config.config_hash(),
            "engine": self.engine.value,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "capital": self.capital,
            "total_costs": self.total_costs,
            "warnings": self.warnings,
            "meta": self.meta,
        }
        (out_dir / "meta.json").write_text(json.dumps(meta, indent=1, default=str))
        return out_dir

    @classmethod
    def load(cls, out_dir: Path) -> BacktestResult:
        meta = json.loads((out_dir / "meta.json").read_text())
        eq = pd.read_parquet(out_dir / "equity.parquet").set_index("ts")
        eq.index = pd.to_datetime(eq.index)
        trades = [Trade.model_validate(t) for t in json.loads((out_dir / "trades.json").read_text())]
        return cls(
            config=StrategyConfig.model_validate(meta["config"]),
            engine=EngineMode(meta["engine"]),
            start=date.fromisoformat(meta["start"]),
            end=date.fromisoformat(meta["end"]),
            capital=meta["capital"],
            equity=eq["equity"],
            gross_equity=eq["gross_equity"],
            trades=trades,
            total_costs=meta["total_costs"],
            warnings=meta["warnings"],
            meta=meta["meta"],
        )


def _ensure_datetime(ts: Any) -> datetime:
    return pd.Timestamp(ts).to_pydatetime()

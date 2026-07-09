"""Indian transaction cost model — config-driven and versioned.

Charge schedules live in costs/schedules/<name>.yaml (dated, immutable).
This module is the ONLY place order charges are computed; engines, paper and
live brokers all call CostModel. Computation uses Decimal with ROUND_HALF_UP
per component (paisa precision), matching how Zerodha's brokerage calculator
displays numbers; per-contract-note whole-rupee rounding of STT/stamp is not
modeled (see docs/assumptions.md).
"""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from tradingos.core.errors import ConfigError
from tradingos.core.models import Product, Side

_SCHEDULES_DIR = Path(__file__).parent / "schedules"
_PAISA = Decimal("0.01")


def _rupees(x: Decimal) -> float:
    return float(x.quantize(_PAISA, rounding=ROUND_HALF_UP))


class ProductCharges(BaseModel):
    """One product's (CNC/MIS) charge rates. Rates are fractions of turnover."""

    brokerage_rate: float = 0.0
    brokerage_flat_cap: float = 0.0  # 0 -> no cap (i.e. pure rate); >0 -> min(rate*v, cap)
    stt_buy_rate: float = 0.0
    stt_sell_rate: float = 0.0
    exchange_txn_rate: float = 0.0
    sebi_rate: float = 0.0
    stamp_buy_rate: float = 0.0
    gst_rate: float = 0.18
    dp_charge_per_sell_day: float = 0.0


class SlippageDefaults(BaseModel):
    large_cap_bps: float = 10.0
    other_bps: float = 25.0


class CostSchedule(BaseModel):
    name: str
    effective_date: date
    exchange: str = "NSE"
    delivery: ProductCharges
    intraday: ProductCharges
    slippage: SlippageDefaults = Field(default_factory=SlippageDefaults)


class CostBreakdown(BaseModel):
    """All-in charges for one executed order (one side), in rupees."""

    brokerage: float = 0.0
    stt: float = 0.0
    exchange_txn: float = 0.0
    sebi: float = 0.0
    stamp: float = 0.0
    gst: float = 0.0
    dp: float = 0.0

    @property
    def total(self) -> float:
        return round(
            self.brokerage + self.stt + self.exchange_txn + self.sebi + self.stamp
            + self.gst + self.dp,
            2,
        )


@lru_cache(maxsize=8)
def load_schedule(name: str) -> CostSchedule:
    path = _SCHEDULES_DIR / f"{name}.yaml"
    if not path.exists():
        available = sorted(p.stem for p in _SCHEDULES_DIR.glob("*.yaml"))
        raise ConfigError(f"unknown cost schedule {name!r}; available: {available}")
    with open(path) as f:
        return CostSchedule.model_validate(yaml.safe_load(f))


class CostModel:
    def __init__(self, schedule: CostSchedule | str = "zerodha_2026") -> None:
        self.schedule = load_schedule(schedule) if isinstance(schedule, str) else schedule

    def _rates(self, product: Product) -> ProductCharges:
        return self.schedule.delivery if product == Product.CNC else self.schedule.intraday

    def order_charges(
        self,
        side: Side,
        product: Product,
        value: float,
        first_sell_of_scrip_today: bool = True,
    ) -> CostBreakdown:
        """Charges for one executed order of total traded `value` rupees.

        `first_sell_of_scrip_today`: the DP charge applies once per scrip per
        day on the sell side (delivery); callers that sell the same scrip
        multiple times a day must pass False after the first sell.
        """
        if value < 0:
            raise ValueError(f"order value must be >= 0, got {value}")
        r = self._rates(product)
        v = Decimal(str(value))

        brokerage = v * Decimal(str(r.brokerage_rate))
        if r.brokerage_flat_cap > 0:
            brokerage = min(brokerage, Decimal(str(r.brokerage_flat_cap)))

        if side == Side.BUY:
            stt = v * Decimal(str(r.stt_buy_rate))
            stamp = v * Decimal(str(r.stamp_buy_rate))
        else:
            stt = v * Decimal(str(r.stt_sell_rate))
            stamp = Decimal("0")

        exchange_txn = v * Decimal(str(r.exchange_txn_rate))
        sebi = v * Decimal(str(r.sebi_rate))
        # GST applies to brokerage + exchange transaction charges + SEBI charges
        gst = (brokerage + exchange_txn + sebi) * Decimal(str(r.gst_rate))

        dp = Decimal("0")
        if side == Side.SELL and first_sell_of_scrip_today:
            dp = Decimal(str(r.dp_charge_per_sell_day))

        return CostBreakdown(
            brokerage=_rupees(brokerage),
            stt=_rupees(stt),
            exchange_txn=_rupees(exchange_txn),
            sebi=_rupees(sebi),
            stamp=_rupees(stamp),
            gst=_rupees(gst),
            dp=_rupees(dp),
        )

    def round_trip_cost(self, product: Product, buy_value: float, sell_value: float) -> float:
        """Convenience: total charges for one buy + one sell."""
        buy = self.order_charges(Side.BUY, product, buy_value)
        sell = self.order_charges(Side.SELL, product, sell_value)
        return round(buy.total + sell.total, 2)

    def slippage_bps(self, is_large_cap: bool) -> float:
        s = self.schedule.slippage
        return s.large_cap_bps if is_large_cap else s.other_bps

"""Indian transaction cost model — config-driven and versioned.

Charge schedules live in costs/schedules/<name>.yaml (dated, immutable —
enforced: the pydantic models are frozen). This module is the ONLY place order
charges are computed; engines, paper and live brokers all call CostModel.
Callers that know the trade date pass ``trade_date=`` so the order is priced at
the schedule that was in force on that date (see CostModel.schedule_for), not
at today's rates. Computation uses Decimal with ROUND_HALF_UP
per component (paisa precision), matching how Zerodha's brokerage calculator
displays numbers; per-contract-note whole-rupee rounding of STT/stamp is not
modeled (see docs/assumptions.md).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from tradingos.core.errors import ConfigError
from tradingos.core.logging import get_logger
from tradingos.core.models import Product, Side

logger = get_logger(__name__)

_SCHEDULES_DIR = Path(__file__).parent / "schedules"
_PAISA = Decimal("0.01")

# Schedule files are named <family>_<version> where the version suffix is date-ish
# digits: zerodha_2026, zerodha_2024_10, ... The family groups the versions a
# CostModel may select between by trade date.
_VERSION_SUFFIX = re.compile(r"_\d{4}(?:_\d{2}){0,2}$")


def _family_of(name: str) -> str:
    """Family key of a schedule name: the name minus its date/version suffix."""
    return _VERSION_SUFFIX.sub("", name)


def _rupees(x: Decimal) -> float:
    return float(x.quantize(_PAISA, rounding=ROUND_HALF_UP))


class ProductCharges(BaseModel):
    """One product's (CNC/MIS) charge rates. Rates are fractions of turnover.

    Frozen: schedules are versioned and immutable once dated — a rate change is
    a NEW dated schedule file, never a mutation of a loaded one.
    """

    model_config = ConfigDict(frozen=True)

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
    model_config = ConfigDict(frozen=True)

    large_cap_bps: float = 10.0
    other_bps: float = 25.0


class CostSchedule(BaseModel):
    """A dated charge schedule. Immutable once loaded (frozen, like its parts):
    ``load_schedule`` caches and shares instances, so mutation would silently
    reprice every consumer — any change must be a new dated YAML file."""

    model_config = ConfigDict(frozen=True)

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


@lru_cache(maxsize=8)
def load_schedule_family(family: str) -> tuple[CostSchedule, ...]:
    """All on-disk schedules of ``family``, sorted by ascending effective_date."""
    members = [
        load_schedule(p.stem)
        for p in _SCHEDULES_DIR.glob("*.yaml")
        if _family_of(p.stem) == family
    ]
    return tuple(sorted(members, key=lambda s: s.effective_date))


class CostModel:
    """Date-aware charge computation against a family of dated schedules.

    ``schedule`` (a name or a loaded :class:`CostSchedule`) is the PINNED
    schedule: it is what undated calls (``trade_date=None``) price against, and
    it caps history — auto-discovered family members with a NEWER
    ``effective_date`` than the pin are ignored, so adding a future schedule
    file can never silently reprice an existing pinned run.

    Dated calls select the family schedule in force on the trade date (the
    latest ``effective_date <= trade_date``). A trade date EARLIER than the
    whole history is priced at the earliest schedule, with one warning per
    CostModel instance (one per run — engines build one model per run), because
    those historical costs are approximations.

    ``history`` overrides discovery (mainly for tests): the explicit schedule
    versions to select between, in any order.
    """

    def __init__(
        self,
        schedule: CostSchedule | str = "zerodha_2026",
        *,
        history: Sequence[CostSchedule] | None = None,
    ) -> None:
        self.schedule = load_schedule(schedule) if isinstance(schedule, str) else schedule
        if history is not None:
            members = list(history)
        else:
            members = [
                s
                for s in load_schedule_family(_family_of(self.schedule.name))
                if s.effective_date <= self.schedule.effective_date
            ] or [self.schedule]
        self._history: tuple[CostSchedule, ...] = tuple(
            sorted(members, key=lambda s: s.effective_date)
        )
        self._warned_predates_history = False

    def schedule_for(self, trade_date: date | None) -> CostSchedule:
        """The charge schedule in force on ``trade_date``.

        ``None`` means "no date known" and returns the pinned schedule
        unchanged (paper/live trade *now*, which is what the pin represents).
        """
        if trade_date is None:
            return self.schedule
        chosen: CostSchedule | None = None
        for s in self._history:  # ascending effective_date
            if s.effective_date <= trade_date:
                chosen = s
            else:
                break
        if chosen is not None:
            return chosen
        earliest = self._history[0]
        if not self._warned_predates_history:
            self._warned_predates_history = True
            logger.warning(
                "trade date %s predates the earliest known charge schedule %r "
                "(effective %s); applying it anyway — costs before %s are "
                "approximate. (warned once per run)",
                trade_date,
                earliest.name,
                earliest.effective_date,
                earliest.effective_date,
            )
        return earliest

    def _rates(self, product: Product, trade_date: date | None = None) -> ProductCharges:
        schedule = self.schedule_for(trade_date)
        return schedule.delivery if product == Product.CNC else schedule.intraday

    def order_charges(
        self,
        side: Side,
        product: Product,
        value: float,
        first_sell_of_scrip_today: bool = True,
        *,
        trade_date: date | None = None,
    ) -> CostBreakdown:
        """Charges for one executed order of total traded `value` rupees.

        `first_sell_of_scrip_today`: the DP charge applies once per scrip per
        day on the sell side (delivery); callers that sell the same scrip
        multiple times a day must pass False after the first sell.

        `trade_date`: prices the order at the schedule in force on that date
        (see :meth:`schedule_for`); None uses the pinned schedule.
        """
        if value < 0:
            raise ValueError(f"order value must be >= 0, got {value}")
        r = self._rates(product, trade_date)
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

    def round_trip_cost(
        self,
        product: Product,
        buy_value: float,
        sell_value: float,
        *,
        trade_date: date | None = None,
    ) -> float:
        """Convenience: total charges for one buy + one sell."""
        buy = self.order_charges(Side.BUY, product, buy_value, trade_date=trade_date)
        sell = self.order_charges(Side.SELL, product, sell_value, trade_date=trade_date)
        return round(buy.total + sell.total, 2)

    def slippage_bps(self, is_large_cap: bool) -> float:
        s = self.schedule.slippage
        return s.large_cap_bps if is_large_cap else s.other_bps

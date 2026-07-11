"""Known-answer tests for the Zerodha cost model.

Every expected number below is computed BY HAND from the zerodha_2026 schedule
(rates from https://zerodha.com/charges/), with per-component paisa rounding
(ROUND_HALF_UP). Worked arithmetic is in the comments — if a test here fails,
either the schedule YAML changed or the math is broken; investigate before
touching the expected values.
"""

from __future__ import annotations

import logging
from datetime import date

import pytest
from pydantic import ValidationError

from tradingos.core.models import Product, Side
from tradingos.costs.model import (
    CostModel,
    CostSchedule,
    ProductCharges,
    load_schedule,
)


@pytest.fixture(scope="module")
def model() -> CostModel:
    return CostModel("zerodha_2026")


class TestDeliveryCNC:
    def test_buy_1_lakh(self, model: CostModel) -> None:
        # value = 100,000
        # brokerage: 0
        # STT buy: 0.1% x 100000                 = 100.00
        # exchange: 0.00297% x 100000            = 2.97
        # SEBI: 10/crore -> 0.0001% x 100000     = 0.10
        # stamp buy: 0.015% x 100000             = 15.00
        # GST: 18% x (0 + 2.97 + 0.10) = 0.5526  -> 0.55
        # total                                  = 118.62
        c = model.order_charges(Side.BUY, Product.CNC, 100_000)
        assert c.brokerage == 0.0
        assert c.stt == 100.00
        assert c.exchange_txn == 2.97
        assert c.sebi == 0.10
        assert c.stamp == 15.00
        assert c.gst == 0.55
        assert c.dp == 0.0
        assert c.total == 118.62

    def test_sell_1_lakh(self, model: CostModel) -> None:
        # STT sell 100.00; exchange 2.97; SEBI 0.10; stamp 0 (sell);
        # GST 0.55; DP charge 15.93 (first sell of scrip today)
        # total = 100 + 2.97 + 0.10 + 0 + 0.55 + 15.93 = 119.55
        c = model.order_charges(Side.SELL, Product.CNC, 100_000)
        assert c.stamp == 0.0
        assert c.dp == 15.93
        assert c.total == 119.55

    def test_sell_second_time_same_day_no_dp(self, model: CostModel) -> None:
        c = model.order_charges(Side.SELL, Product.CNC, 100_000, first_sell_of_scrip_today=False)
        assert c.dp == 0.0
        assert c.total == pytest.approx(119.55 - 15.93)

    def test_round_trip_1_lakh(self, model: CostModel) -> None:
        assert model.round_trip_cost(Product.CNC, 100_000, 100_000) == pytest.approx(238.17)


class TestIntradayMIS:
    def test_buy_50k(self, model: CostModel) -> None:
        # value = 50,000
        # brokerage: min(0.03% x 50000, 20) = min(15, 20)    = 15.00
        # STT buy (MIS): 0                                    = 0.00
        # exchange: 0.00297% x 50000 = 1.485                  -> 1.49 (HALF_UP)
        # SEBI: 0.0001% x 50000                               = 0.05
        # stamp buy: 0.003% x 50000                           = 1.50
        # GST: 18% x (15 + 1.485 + 0.05) = 18% x 16.535 = 2.9763 -> 2.98
        # total = 15 + 0 + 1.49 + 0.05 + 1.50 + 2.98          = 21.02
        c = model.order_charges(Side.BUY, Product.MIS, 50_000)
        assert c.brokerage == 15.00
        assert c.stt == 0.0
        assert c.exchange_txn == 1.49
        assert c.sebi == 0.05
        assert c.stamp == 1.50
        assert c.gst == 2.98
        assert c.total == 21.02

    def test_sell_1_lakh_brokerage_capped(self, model: CostModel) -> None:
        # brokerage: min(0.03% x 100000 = 30, 20)             = 20.00
        # STT sell: 0.025% x 100000                           = 25.00
        # exchange 2.97; SEBI 0.10; stamp 0 (sell)
        # GST: 18% x (20 + 2.97 + 0.10) = 18% x 23.07 = 4.1526 -> 4.15
        # no DP for intraday
        # total = 20 + 25 + 2.97 + 0.10 + 0 + 4.15            = 52.22
        c = model.order_charges(Side.SELL, Product.MIS, 100_000)
        assert c.brokerage == 20.00
        assert c.stt == 25.00
        assert c.gst == 4.15
        assert c.dp == 0.0
        assert c.total == 52.22


class TestScheduleLoading:
    def test_unknown_schedule_raises(self) -> None:
        from tradingos.core.errors import ConfigError

        with pytest.raises(ConfigError, match="unknown cost schedule"):
            load_schedule("no_such_broker_1999")

    def test_zero_value_order(self, model: CostModel) -> None:
        c = model.order_charges(Side.BUY, Product.CNC, 0.0)
        assert c.total == 0.0

    def test_negative_value_rejected(self, model: CostModel) -> None:
        with pytest.raises(ValueError):
            model.order_charges(Side.BUY, Product.CNC, -1.0)

    def test_slippage_tiers(self, model: CostModel) -> None:
        assert model.slippage_bps(is_large_cap=True) == 10.0
        assert model.slippage_bps(is_large_cap=False) == 25.0


# --------------------------------------------------------------------------- #
# Date-aware schedule selection (historical trades must use historical rates)  #
# --------------------------------------------------------------------------- #
def _mk_schedule(name: str, effective: date, exchange_txn_rate: float) -> CostSchedule:
    """A CNC-only test schedule; only exchange_txn_rate differs between versions."""
    delivery = ProductCharges(
        brokerage_rate=0.0,
        stt_buy_rate=0.001,
        stt_sell_rate=0.001,
        exchange_txn_rate=exchange_txn_rate,
        sebi_rate=0.000001,
        stamp_buy_rate=0.00015,
        gst_rate=0.18,
        dp_charge_per_sell_day=15.93,
    )
    return CostSchedule(
        name=name,
        effective_date=effective,
        delivery=delivery,
        intraday=ProductCharges(),
    )


# Two dated versions of one family. Known-answer arithmetic for a 1,00,000 CNC
# BUY (per-component paisa rounding, ROUND_HALF_UP):
#   old (exchange 0.00345%): STT 100.00; exch 3.45; SEBI 0.10; stamp 15.00;
#       GST 18% x (0 + 3.45 + 0.10) = 0.639 -> 0.64;    total = 119.19
#   new (exchange 0.00297%): STT 100.00; exch 2.97; SEBI 0.10; stamp 15.00;
#       GST 18% x (0 + 2.97 + 0.10) = 0.5526 -> 0.55;   total = 118.62
OLD = _mk_schedule("kite_test_2024", date(2024, 10, 1), 0.0000345)
NEW = _mk_schedule("kite_test_2026", date(2026, 1, 1), 0.0000297)
OLD_TOTAL = 119.19
NEW_TOTAL = 118.62


class TestDateAwareScheduleSelection:
    @pytest.fixture()
    def two_version_model(self) -> CostModel:
        return CostModel(NEW, history=[NEW, OLD])  # deliberately unsorted

    def test_trade_before_boundary_uses_old_schedule(self, two_version_model: CostModel) -> None:
        c = two_version_model.order_charges(
            Side.BUY, Product.CNC, 100_000, trade_date=date(2025, 12, 31)
        )
        assert c.exchange_txn == 3.45
        assert c.gst == 0.64
        assert c.total == OLD_TOTAL

    def test_trade_on_boundary_uses_new_schedule(self, two_version_model: CostModel) -> None:
        c = two_version_model.order_charges(
            Side.BUY, Product.CNC, 100_000, trade_date=date(2026, 1, 1)
        )
        assert c.exchange_txn == 2.97
        assert c.gst == 0.55
        assert c.total == NEW_TOTAL

    def test_trade_on_old_effective_date_uses_old_schedule(
        self, two_version_model: CostModel
    ) -> None:
        c = two_version_model.order_charges(
            Side.BUY, Product.CNC, 100_000, trade_date=date(2024, 10, 1)
        )
        assert c.total == OLD_TOTAL

    def test_undated_call_uses_pinned_schedule(self, two_version_model: CostModel) -> None:
        assert two_version_model.order_charges(Side.BUY, Product.CNC, 100_000).total == NEW_TOTAL
        assert two_version_model.schedule_for(None) is NEW

    def test_round_trip_cost_respects_trade_date(self, two_version_model: CostModel) -> None:
        # old sell: STT 100.00; exch 3.45; SEBI 0.10; GST 0.64; DP 15.93 = 120.12
        # old round trip = 119.19 + 120.12 = 239.31
        assert two_version_model.round_trip_cost(
            Product.CNC, 100_000, 100_000, trade_date=date(2025, 6, 1)
        ) == pytest.approx(239.31)

    def test_trade_predating_history_uses_earliest_and_warns_once(
        self, two_version_model: CostModel, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING, logger="tradingos.costs.model"):
            c1 = two_version_model.order_charges(
                Side.BUY, Product.CNC, 100_000, trade_date=date(2023, 3, 15)
            )
            c2 = two_version_model.order_charges(
                Side.BUY, Product.CNC, 100_000, trade_date=date(2022, 1, 5)
            )
        assert c1.total == OLD_TOTAL  # earliest schedule applied, not the pin
        assert c2.total == OLD_TOTAL
        warnings = [r for r in caplog.records if "predates the earliest" in r.message]
        assert len(warnings) == 1  # once per run, not per trade
        assert "kite_test_2024" in warnings[0].getMessage()

    def test_default_zerodha_model_accepts_trade_dates(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        # Only zerodha_2026 exists on disk: a 2024 backtest trade predates the
        # whole history -> priced at zerodha_2026 rates, with a loud warning
        # instead of the old silent repricing.
        model = CostModel("zerodha_2026")
        with caplog.at_level(logging.WARNING, logger="tradingos.costs.model"):
            c = model.order_charges(
                Side.BUY, Product.CNC, 100_000, trade_date=date(2024, 6, 3)
            )
        assert c.total == 118.62
        assert any("predates the earliest" in r.message for r in caplog.records)

    def test_discovered_history_is_capped_at_the_pinned_schedule(self) -> None:
        # Pinning a schedule means dated selection never reaches past the pin:
        # with the pin as the only (earliest) known version, an earlier trade
        # date falls back to it rather than to some newer on-disk file.
        model = CostModel(OLD, history=[OLD, NEW])
        pinned_only = CostModel(OLD, history=[OLD])
        d = date(2026, 5, 1)
        assert model.schedule_for(d) is NEW  # explicit history: caller opted in
        assert pinned_only.schedule_for(d) is OLD


# --------------------------------------------------------------------------- #
# Immutability: a loaded schedule can never be repriced in place               #
# --------------------------------------------------------------------------- #
class TestScheduleImmutability:
    def test_schedule_fields_are_frozen(self) -> None:
        schedule = load_schedule("zerodha_2026")
        with pytest.raises(ValidationError):
            schedule.name = "hacked"  # type: ignore[misc]
        with pytest.raises(ValidationError):
            schedule.effective_date = date(1999, 1, 1)  # type: ignore[misc]

    def test_nested_rates_are_frozen(self) -> None:
        schedule = load_schedule("zerodha_2026")
        with pytest.raises(ValidationError):
            schedule.delivery.stt_buy_rate = 0.0  # type: ignore[misc]
        with pytest.raises(ValidationError):
            schedule.slippage.large_cap_bps = 0.0  # type: ignore[misc]

    def test_cached_instance_stays_pristine(self) -> None:
        # load_schedule caches and shares one instance; freezing is what makes
        # that sharing safe. Same object, same known-answer totals.
        a = load_schedule("zerodha_2026")
        b = load_schedule("zerodha_2026")
        assert a is b
        assert CostModel(a).order_charges(Side.BUY, Product.CNC, 100_000).total == 118.62

"""Known-answer tests for the Zerodha cost model.

Every expected number below is computed BY HAND from the zerodha_2026 schedule
(rates from https://zerodha.com/charges/), with per-component paisa rounding
(ROUND_HALF_UP). Worked arithmetic is in the comments — if a test here fails,
either the schedule YAML changed or the math is broken; investigate before
touching the expected values.
"""

from __future__ import annotations

import pytest

from tradingos.core.models import Product, Side
from tradingos.costs.model import CostModel, load_schedule


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

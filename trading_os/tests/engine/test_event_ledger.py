"""Money math for the event-driven Ledger, with hand-computed expectations.

Every rupee figure below is stated as an explicit literal AND cross-checked
against :class:`~tradingos.costs.model.CostModel` so a schedule change surfaces
loudly. Charges for zerodha_2026 CNC (delivery):

    BUY value 1000.00:  stt 1000*0.001 = 1.00; exch 1000*0.0000297 = 0.03;
                        sebi ~0.00; stamp 1000*0.00015 = 0.15;
                        gst (0.0297+0.001)*0.18 -> 0.01; dp 0  => TOTAL 1.19
    SELL value 1100.00: stt 1100*0.001 = 1.10; exch 0.03; gst 0.01;
                        dp 15.93 (first sell of scrip that day)  => TOTAL 17.07
    SELL value 1100.00 (second sell same scrip same day): no dp  => TOTAL 1.14
"""

from __future__ import annotations

from datetime import datetime

from tradingos.core.models import Fill, Product, Side
from tradingos.costs.model import CostModel
from tradingos.engine.event.execution import ChargeCalculator
from tradingos.engine.event.portfolio import Ledger

_BUY_TS = datetime(2021, 1, 4, 9, 15)
_SELL_TS = datetime(2021, 2, 1, 9, 15)


def _charges() -> ChargeCalculator:
    return ChargeCalculator(CostModel("zerodha_2026"), Product.CNC)


def test_buy_then_sell_cash_to_the_paisa_and_trade_round_trip() -> None:
    cc = _charges()
    ledger = Ledger(capital=100_000.0, strategy_id="ledger_test")

    # --- BUY 10 @ 100.00 -> value 1000.00, charges 1.19 -------------------
    buy_charges = cc.charges(Side.BUY, "X", 1000.00, _BUY_TS)
    assert buy_charges == 1.19  # hand-computed literal
    ledger.apply_fill(
        Fill(client_order_id="b1", symbol="X", side=Side.BUY, qty=10, price=100.00,
             ts=_BUY_TS, charges=buy_charges)
    )
    # cash = 100000 - (1000.00 + 1.19) = 98998.81
    assert ledger.cash == 98998.81
    assert ledger.positions["X"].qty == 10
    assert ledger.positions["X"].avg_price == 100.00  # VWAP excludes charges

    # --- SELL 10 @ 110.00 -> value 1100.00, charges 17.07 -----------------
    sell_charges = cc.charges(Side.SELL, "X", 1100.00, _SELL_TS)
    assert sell_charges == 17.07  # includes the 15.93 DP charge (first sell)
    trade = ledger.apply_fill(
        Fill(client_order_id="s1", symbol="X", side=Side.SELL, qty=10, price=110.00,
             ts=_SELL_TS, charges=sell_charges),
        reason="rebalance",
    )
    # cash = 98998.81 + (1100.00 - 17.07) = 100081.74
    assert ledger.cash == 100081.74
    assert "X" not in ledger.positions  # flat -> lot removed

    # --- Trade round trip -------------------------------------------------
    assert trade is not None
    assert trade.symbol == "X"
    assert trade.qty == 10
    assert trade.entry_price == 100.00
    assert trade.exit_price == 110.00
    assert trade.entry_costs == 1.19  # full lot's buy costs
    assert trade.exit_costs == 17.07
    assert trade.exit_reason == "rebalance"
    assert trade.entry_ts == _BUY_TS
    assert trade.exit_ts == _SELL_TS
    # gross 100.00, net = 100 - 18.26 = 81.74, matching the realised cash gain
    assert trade.gross_pnl == 100.00
    assert round(trade.net_pnl, 2) == 81.74


def test_total_costs_and_gross_minus_net_equity_equals_cumulative_costs() -> None:
    cc = _charges()
    ledger = Ledger(capital=100_000.0)
    ledger.apply_fill(
        Fill(client_order_id="b", symbol="X", side=Side.BUY, qty=10, price=100.00,
             ts=_BUY_TS, charges=cc.charges(Side.BUY, "X", 1000.00, _BUY_TS))
    )
    ledger.apply_fill(
        Fill(client_order_id="s", symbol="X", side=Side.SELL, qty=10, price=110.00,
             ts=_SELL_TS, charges=cc.charges(Side.SELL, "X", 1100.00, _SELL_TS)),
        reason="rebalance",
    )
    # total costs 1.19 + 17.07 = 18.26
    assert ledger.total_costs == 18.26
    net_equity = ledger.equity()  # flat -> just cash
    gross_equity = round(net_equity + ledger.total_costs, 2)
    # gross - net == cumulative costs, exactly
    assert round(gross_equity - net_equity, 2) == ledger.total_costs
    # and gross == capital + gross pnl (100)
    assert gross_equity == 100_100.00


def test_dp_charge_applies_once_per_scrip_per_day() -> None:
    cc = _charges()
    day1_first = datetime(2021, 1, 4, 9, 15)
    day1_second = datetime(2021, 1, 4, 15, 30)  # same day, later
    day2 = datetime(2021, 1, 5, 9, 15)

    # first sell of the scrip today -> DP included (total 17.07)
    assert cc.charges(Side.SELL, "Y", 1100.00, day1_first) == 17.07
    # second sell of the SAME scrip the SAME day -> no DP (total 1.14)
    assert cc.charges(Side.SELL, "Y", 1100.00, day1_second) == 1.14
    # a different scrip the same day -> DP again (its own first sell)
    assert cc.charges(Side.SELL, "Z", 1100.00, day1_second) == 17.07
    # next day the per-day tracking resets -> DP again for Y
    assert cc.charges(Side.SELL, "Y", 1100.00, day2) == 17.07


def test_oversell_clip_charges_only_the_clipped_quantity_and_warns() -> None:
    """Regression: a clipped SELL (oversell protection) used to debit the
    charges computed on the UNCLIPPED quantity. The ledger must charge the
    quantity that actually traded (pro-rata) and record a warning."""
    ledger = Ledger(capital=100_000.0)
    ledger.apply_fill(
        Fill(client_order_id="b", symbol="X", side=Side.BUY, qty=5, price=100.00,
             ts=_BUY_TS, charges=1.19)
    )
    cash_before = ledger.cash
    costs_before = ledger.total_costs

    # SELL 10 with only 5 held; 10.00 of charges were computed on the full 10.
    trade = ledger.apply_fill(
        Fill(client_order_id="s", symbol="X", side=Side.SELL, qty=10, price=110.00,
             ts=_SELL_TS, charges=10.00),
        reason="rebalance",
    )
    assert trade is not None
    assert trade.qty == 5
    # charges prorated to the clipped half: 10.00 * 5/10 = 5.00
    assert trade.exit_costs == 5.00
    assert ledger.cash == round(cash_before + 5 * 110.00 - 5.00, 2)
    assert ledger.total_costs == round(costs_before + 5.00, 2)
    assert any("clipped" in w for w in ledger.warnings)


def test_ignored_sell_with_no_open_long_records_warning() -> None:
    ledger = Ledger(capital=1_000.0)
    out = ledger.apply_fill(
        Fill(client_order_id="s", symbol="Y", side=Side.SELL, qty=1, price=10.00,
             ts=_SELL_TS, charges=0.50)
    )
    assert out is None
    assert ledger.cash == 1_000.0  # fill dropped entirely — no cash or costs
    assert ledger.total_costs == 0.0
    assert any("no open long" in w for w in ledger.warnings)


def test_partial_sell_prorates_entry_costs_across_two_trades() -> None:
    cc = _charges()
    ledger = Ledger(capital=1_000_000.0)
    # buy 100 @ 100.00 -> value 10000.00
    buy_charges = cc.charges(Side.BUY, "X", 10_000.00, _BUY_TS)
    ledger.apply_fill(
        Fill(client_order_id="b", symbol="X", side=Side.BUY, qty=100, price=100.00,
             ts=_BUY_TS, charges=buy_charges)
    )
    # sell 40 first, then 60 -> entry costs split 40/100 and 60/100
    t1 = ledger.apply_fill(
        Fill(client_order_id="s1", symbol="X", side=Side.SELL, qty=40, price=110.00,
             ts=_SELL_TS, charges=cc.charges(Side.SELL, "X", 4400.00, _SELL_TS)),
        reason="rebalance",
    )
    t2 = ledger.apply_fill(
        Fill(client_order_id="s2", symbol="X", side=Side.SELL, qty=60, price=120.00,
             ts=_SELL_TS, charges=cc.charges(Side.SELL, "X", 7200.00, _SELL_TS)),
        reason="rebalance",
    )
    assert t1 is not None and t2 is not None
    # entry costs are apportioned by quantity and, summed, recover the buy cost
    assert round(t1.entry_costs + t2.entry_costs, 2) == round(buy_charges, 2)
    assert t1.entry_costs == round(buy_charges * 0.40, 2)
    assert "X" not in ledger.positions

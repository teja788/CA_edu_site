from __future__ import annotations

from datetime import date, datetime

import pytest

from tradingos.core.errors import OrderStateError
from tradingos.core.models import (
    Order,
    OrderStatus,
    Side,
    Trade,
    validate_transition,
)
from tradingos.core.timeutils import date_chunks, is_market_hours, to_naive_ist


class TestOrderStateMachine:
    def test_happy_path(self) -> None:
        o = Order(symbol="INFY", side=Side.BUY, qty=10)
        assert o.status == OrderStatus.PENDING
        o.transition(OrderStatus.OPEN)
        o.transition(OrderStatus.PARTIAL)
        o.transition(OrderStatus.COMPLETE)
        assert o.status.is_terminal

    def test_pending_cannot_jump_to_complete(self) -> None:
        with pytest.raises(OrderStateError):
            validate_transition(OrderStatus.PENDING, OrderStatus.COMPLETE)

    def test_terminal_states_frozen(self) -> None:
        for terminal in (OrderStatus.COMPLETE, OrderStatus.CANCELLED, OrderStatus.REJECTED):
            for target in OrderStatus:
                with pytest.raises(OrderStateError):
                    validate_transition(terminal, target)

    def test_partial_can_repeat(self) -> None:
        validate_transition(OrderStatus.PARTIAL, OrderStatus.PARTIAL)

    def test_remaining_qty(self) -> None:
        o = Order(symbol="INFY", side=Side.BUY, qty=10, filled_qty=4)
        assert o.remaining_qty == 6


class TestTrade:
    def test_pnl_known_answer(self) -> None:
        # buy 100 @ 500, sell 100 @ 550: gross 5000; costs 118.62 + 119.55
        t = Trade(
            symbol="X",
            qty=100,
            entry_ts=datetime(2024, 1, 1, 9, 15),
            exit_ts=datetime(2024, 2, 1, 9, 15),
            entry_price=500.0,
            exit_price=550.0,
            entry_costs=118.62,
            exit_costs=119.55,
        )
        assert t.gross_pnl == pytest.approx(5000.0)
        assert t.net_pnl == pytest.approx(5000.0 - 238.17)
        assert t.holding_days == pytest.approx(31.0)


class TestTimeUtils:
    def test_date_chunks_respects_max(self) -> None:
        chunks = date_chunks(date(2020, 1, 1), date(2020, 3, 1), max_days=30)
        assert chunks[0] == (date(2020, 1, 1), date(2020, 1, 30))
        assert chunks[-1][1] == date(2020, 3, 1)
        # contiguous, non-overlapping
        for (_, e1), (s2, _) in zip(chunks, chunks[1:], strict=False):
            assert (s2 - e1).days == 1
        assert all((e - s).days < 30 for s, e in chunks)

    def test_date_chunks_single_day(self) -> None:
        assert date_chunks(date(2020, 1, 1), date(2020, 1, 1), 60) == [
            (date(2020, 1, 1), date(2020, 1, 1))
        ]

    def test_date_chunks_rejects_reversed(self) -> None:
        with pytest.raises(ValueError):
            date_chunks(date(2020, 2, 1), date(2020, 1, 1), 60)

    def test_market_hours(self) -> None:
        assert is_market_hours(datetime(2024, 1, 15, 10, 0))  # Monday
        assert not is_market_hours(datetime(2024, 1, 15, 8, 0))
        assert not is_market_hours(datetime(2024, 1, 13, 10, 0))  # Saturday

    def test_to_naive_ist(self) -> None:
        from zoneinfo import ZoneInfo

        utc = datetime(2024, 1, 15, 10, 0, tzinfo=ZoneInfo("UTC"))
        assert to_naive_ist(utc) == datetime(2024, 1, 15, 15, 30)

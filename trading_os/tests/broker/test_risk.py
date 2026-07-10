from __future__ import annotations

from datetime import date, datetime, time

import pytest

from tradingos.broker.risk import PreTradeRiskChecker, RiskLimits
from tradingos.config.settings import Settings
from tradingos.core.errors import RiskViolation
from tradingos.core.models import Order, Side
from tradingos.data.calendar import NSECalendar

# Known 2024 dates (see tests/data/test_calendar.py):
TRADING_DAY = date(2024, 1, 25)  # ordinary Thursday
HOLIDAY = date(2024, 1, 26)  # Republic Day, a Friday
WEEKEND = date(2024, 1, 27)  # Saturday

NOON = datetime.combine(TRADING_DAY, time(12, 0))


def make_limits(**overrides: object) -> RiskLimits:
    kwargs: dict[str, object] = dict(
        max_order_value=1_000_000.0,
        max_position_pct=0.5,
        max_daily_loss=50_000.0,
        max_orders_per_day=100,
        restricted_symbols=frozenset(),
        market_hours_only=True,
    )
    kwargs.update(overrides)
    return RiskLimits(**kwargs)  # type: ignore[arg-type]


def make_checker(**overrides: object) -> PreTradeRiskChecker:
    return PreTradeRiskChecker(make_limits(**overrides), calendar=NSECalendar())


def make_order(side: Side = Side.BUY, qty: int = 10, symbol: str = "INFY") -> Order:
    return Order(symbol=symbol, side=side, qty=qty)


DEFAULT_KWARGS = dict(
    price=100.0,
    equity=100_000.0,
    positions={},
    orders_today=0,
    day_start_equity=100_000.0,
    now=NOON,
)


def check(checker: PreTradeRiskChecker, order: Order, **overrides: object) -> None:
    kwargs = dict(DEFAULT_KWARGS)
    kwargs.update(overrides)
    checker.check(order, **kwargs)  # type: ignore[arg-type]


class TestRiskLimitsFromSettings:
    def test_pulls_values_from_settings(self, settings: Settings) -> None:
        limits = RiskLimits.from_settings(settings)
        assert limits.max_order_value == settings.max_order_value
        assert limits.max_position_pct == settings.max_position_pct
        assert limits.max_daily_loss == settings.max_daily_loss
        assert limits.max_orders_per_day == settings.max_orders_per_day
        assert limits.restricted_symbols == frozenset()
        assert limits.market_hours_only is True

    def test_accepts_restricted_symbols_and_market_hours_override(
        self, settings: Settings
    ) -> None:
        limits = RiskLimits.from_settings(
            settings, restricted_symbols=["XYZ", "ABC"], market_hours_only=False
        )
        assert limits.restricted_symbols == frozenset({"XYZ", "ABC"})
        assert limits.market_hours_only is False


class TestRestrictedSymbol:
    def test_non_restricted_symbol_passes(self) -> None:
        checker = make_checker(restricted_symbols=frozenset({"BANNED"}))
        check(checker, make_order(symbol="INFY"))  # must not raise

    def test_restricted_symbol_fails(self) -> None:
        checker = make_checker(restricted_symbols=frozenset({"BANNED"}))
        with pytest.raises(RiskViolation, match="restricted"):
            check(checker, make_order(symbol="BANNED"))

    def test_restricted_symbol_takes_priority_over_market_hours(self) -> None:
        checker = make_checker(restricted_symbols=frozenset({"BANNED"}))
        bad_time = datetime.combine(HOLIDAY, time(12, 0))
        with pytest.raises(RiskViolation, match="restricted"):
            check(checker, make_order(symbol="BANNED"), now=bad_time)


class TestMarketHours:
    def test_trading_day_within_hours_passes(self) -> None:
        checker = make_checker()
        check(checker, make_order(), now=NOON)

    def test_exactly_market_open_passes(self) -> None:
        checker = make_checker()
        check(checker, make_order(), now=datetime.combine(TRADING_DAY, time(9, 15)))

    def test_exactly_market_close_passes(self) -> None:
        checker = make_checker()
        check(checker, make_order(), now=datetime.combine(TRADING_DAY, time(15, 30)))

    def test_before_market_open_fails(self) -> None:
        checker = make_checker()
        before_open = datetime.combine(TRADING_DAY, time(9, 14, 59))
        with pytest.raises(RiskViolation, match="market hours"):
            check(checker, make_order(), now=before_open)

    def test_after_market_close_fails(self) -> None:
        checker = make_checker()
        after_close = datetime.combine(TRADING_DAY, time(15, 30, 1))
        with pytest.raises(RiskViolation, match="market hours"):
            check(checker, make_order(), now=after_close)

    def test_holiday_fails(self) -> None:
        checker = make_checker()
        on_holiday = datetime.combine(HOLIDAY, time(12, 0))
        with pytest.raises(RiskViolation, match="market hours"):
            check(checker, make_order(), now=on_holiday)

    def test_weekend_fails(self) -> None:
        checker = make_checker()
        on_weekend = datetime.combine(WEEKEND, time(12, 0))
        with pytest.raises(RiskViolation, match="market hours"):
            check(checker, make_order(), now=on_weekend)

    def test_market_hours_only_false_bypasses_all_of_the_above(self) -> None:
        checker = make_checker(market_hours_only=False)
        on_weekend = datetime.combine(WEEKEND, time(3, 0))
        check(checker, make_order(), now=on_weekend)  # must not raise


class TestOrdersPerDay:
    def test_just_below_limit_passes(self) -> None:
        checker = make_checker(max_orders_per_day=5)
        check(checker, make_order(), orders_today=4)

    def test_at_limit_fails(self) -> None:
        checker = make_checker(max_orders_per_day=5)
        with pytest.raises(RiskViolation, match="orders per day"):
            check(checker, make_order(), orders_today=5)

    def test_over_limit_fails(self) -> None:
        checker = make_checker(max_orders_per_day=5)
        with pytest.raises(RiskViolation, match="orders per day"):
            check(checker, make_order(), orders_today=6)


class TestOrderValue:
    def test_exactly_at_limit_passes(self) -> None:
        checker = make_checker(max_order_value=1_000.0)
        check(checker, make_order(qty=10), price=100.0)  # 10*100 == 1000

    def test_strictly_over_limit_fails(self) -> None:
        checker = make_checker(max_order_value=1_000.0)
        with pytest.raises(RiskViolation, match="order value"):
            check(checker, make_order(qty=10), price=100.01)  # 1000.1 > 1000

    def test_applies_to_sell_orders_too(self) -> None:
        checker = make_checker(max_order_value=1_000.0)
        with pytest.raises(RiskViolation, match="order value"):
            check(
                checker,
                make_order(side=Side.SELL, qty=10),
                price=100.01,
                positions={"INFY": 100},
            )

    def test_order_value_checked_before_daily_loss(self) -> None:
        checker = make_checker(max_order_value=1_000.0, max_daily_loss=100.0)
        with pytest.raises(RiskViolation, match="order value"):
            check(
                checker,
                make_order(qty=10),
                price=100.01,  # over order-value limit
                equity=0.0,
                day_start_equity=100_000.0,  # also way over daily-loss limit
            )


class TestDailyLoss:
    def test_exactly_at_limit_passes_for_buy(self) -> None:
        checker = make_checker(max_daily_loss=1_000.0)
        check(checker, make_order(side=Side.BUY), day_start_equity=100_000.0, equity=99_000.0)

    def test_strictly_over_limit_fails_for_buy(self) -> None:
        checker = make_checker(max_daily_loss=1_000.0)
        with pytest.raises(RiskViolation, match="daily loss"):
            check(
                checker,
                make_order(side=Side.BUY),
                day_start_equity=100_000.0,
                equity=98_999.99,
            )

    def test_sell_bypasses_daily_loss_even_when_breached(self) -> None:
        checker = make_checker(max_daily_loss=1_000.0)
        check(
            checker,
            make_order(side=Side.SELL, qty=5),
            day_start_equity=100_000.0,
            equity=10_000.0,  # loss of 90,000 >> limit
            positions={"INFY": 100},
        )  # must not raise

    def test_daily_loss_checked_before_position_pct(self) -> None:
        checker = make_checker(max_daily_loss=100.0, max_position_pct=0.01)
        with pytest.raises(RiskViolation, match="daily loss"):
            check(
                checker,
                make_order(side=Side.BUY, qty=1),
                price=10.0,
                equity=50_000.0,
                day_start_equity=100_000.0,  # loss 50,000 >> 100 limit
                positions={},
            )


class TestPositionPct:
    def test_exactly_at_limit_passes_for_buy(self) -> None:
        # (existing_qty + order.qty) * price / equity == max_position_pct
        checker = make_checker(max_position_pct=0.1)
        check(
            checker,
            make_order(side=Side.BUY, qty=10),
            price=100.0,  # 10 * 100 = 1000
            equity=10_000.0,  # 1000 / 10000 = 0.1 == limit
            day_start_equity=10_000.0,  # no daily loss, isolates the position-pct rule
            positions={},
        )

    def test_strictly_over_limit_fails_for_buy(self) -> None:
        checker = make_checker(max_position_pct=0.1)
        with pytest.raises(RiskViolation, match="position pct"):
            check(
                checker,
                make_order(side=Side.BUY, qty=11),
                price=100.0,  # 11 * 100 = 1100
                equity=10_000.0,  # 1100 / 10000 = 0.11 > 0.1
                day_start_equity=10_000.0,
                positions={},
            )

    def test_includes_existing_position_in_projection(self) -> None:
        checker = make_checker(max_position_pct=0.1)
        with pytest.raises(RiskViolation, match="position pct"):
            check(
                checker,
                make_order(side=Side.BUY, qty=5),
                price=100.0,  # (50 + 5) * 100 = 5500
                equity=10_000.0,  # 5500 / 10000 = 0.55 > 0.1
                day_start_equity=10_000.0,
                positions={"INFY": 50},
            )

    def test_does_not_apply_to_sell_orders(self) -> None:
        checker = make_checker(max_position_pct=0.01)
        check(
            checker,
            make_order(side=Side.SELL, qty=100),
            price=100.0,
            equity=10_000.0,  # would massively breach if position% applied
            positions={"INFY": 200},
        )  # must not raise

    def test_zero_equity_fails_for_buy(self) -> None:
        checker = make_checker()
        with pytest.raises(RiskViolation, match="position pct"):
            check(checker, make_order(side=Side.BUY, qty=1), equity=0.0, day_start_equity=0.0)

    def test_negative_equity_fails_for_buy(self) -> None:
        checker = make_checker()
        with pytest.raises(RiskViolation, match="position pct"):
            check(checker, make_order(side=Side.BUY, qty=1), equity=-500.0, day_start_equity=0.0)

    def test_non_positive_equity_does_not_affect_sell_orders(self) -> None:
        checker = make_checker()
        check(
            checker,
            make_order(side=Side.SELL, qty=1),
            equity=0.0,
            day_start_equity=0.0,
            positions={"INFY": 10},
        )  # must not raise: position pct (and daily loss) are BUY-only rules


class TestFullCheckPasses:
    def test_a_wholly_compliant_order_raises_nothing(self) -> None:
        checker = make_checker()
        check(checker, make_order())

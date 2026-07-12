from datetime import UTC, datetime

import pytest

from tradingos.core.models import OrderStatus
from tradingos.live.order_mapping import map_status, optional_float, parse_timestamp, tag_for


@pytest.mark.parametrize(
    ("raw", "filled", "expected"),
    [
        ("COMPLETE", 10, OrderStatus.COMPLETE),
        ("REJECTED", 0, OrderStatus.REJECTED),
        ("CANCELED", 0, OrderStatus.CANCELLED),
        ("trigger pending", 0, OrderStatus.OPEN),
        ("unknown future status", 2, OrderStatus.PARTIAL),
    ],
)
def test_map_status_is_conservative(raw: object, filled: int, expected: OrderStatus) -> None:
    assert map_status(raw, filled) == expected


def test_tag_is_stable_and_kite_compatible() -> None:
    assert tag_for("client-1") == tag_for("client-1")
    assert len(tag_for("client-1")) == 18
    assert tag_for("client-1").isalnum()


@pytest.mark.parametrize(("raw", "expected"), [(None, None), (0, None), ("12.5", 12.5), ("x", None)])
def test_optional_float(raw: object, expected: float | None) -> None:
    assert optional_float(raw) == expected


def test_parse_timestamp_normalizes_supported_inputs() -> None:
    expected = datetime(2026, 1, 2, 9, 30)
    assert parse_timestamp("2026-01-02 09:30:00") == expected
    assert parse_timestamp(datetime(2026, 1, 2, 4, 0, tzinfo=UTC)) == expected
    assert parse_timestamp("not-a-time") is None

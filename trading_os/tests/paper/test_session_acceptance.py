"""Phase 5 acceptance: a strategy paper-trades a full (two-day, synthetic,
tickless-morning) session end to end and produces the EOD divergence report.

Deliberately runs the REAL scheduler ordering for the morning: the session-open
job fires before any tick exists (broker has no quotes -> planned MARKET orders
stay PENDING, fault-tolerant), then the day's first quote arrives (primed from
the bar OPEN) and a retry places and fills everything at open+slippage -- the
paper analogue of the backtest's fill-at-T+1-open convention.

Strategy is the same hand-computable shape as tests/paper/test_runner.py:
single "close" signal, top-2-of-3, equal weight. All quantities and fill
prices below are hand-computed literals:

  D1 closes: AAA 100, BBB 200, CCC 50 -> top-2 = BBB, AAA; weight 0.5 each of
  equity 100,000 -> targets AAA 500 = floor(50,000/100), BBB 250 = floor(50,000/200).
  D2 opens gap DOWN (so both buys fit inside capital): AAA 99 -> fill
  round(99 * 1.001, 2) = 99.10 with slippage_bps=10; BBB 197 -> 197.20.
  D2 closes: AAA 101, BBB 199 -> final equity = cash + 500*101 + 250*199.
"""

from __future__ import annotations

from datetime import date, datetime, time

import pandas as pd
import polars as pl
import pytest

from tradingos.broker.risk import RiskLimits
from tradingos.config.schemas import (
    ScoreSpec,
    SelectionSpec,
    SignalSpec,
    SizingSpec,
    StrategyConfig,
    UniverseSpec,
)
from tradingos.config.settings import Settings
from tradingos.core.models import OrderStatus, Tick, Timeframe
from tradingos.data.calendar import NSECalendar
from tradingos.data.store import BarStore
from tradingos.paper.broker import PaperBroker
from tradingos.paper.ledgerdb import PaperStore
from tradingos.paper.runner import PaperSessionRunner
from tradingos.strategies.registry import register_signal

D1 = date(2024, 2, 7)  # Wednesday, ordinary NSE trading day
D2 = date(2024, 2, 8)  # Thursday, ordinary NSE trading day


@register_signal("acceptance_close")
def _close_signal(df: pd.DataFrame, **params: object) -> pd.Series:
    return df["close"]


class _Clock:
    """Mutable injected clock: one broker lives across both days."""

    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


# The strategy sizes 50% positions; the Settings-default limits (10% per
# symbol) would veto them — which is the guardrail working, not a bug. Real
# deployments raise the env limits to match the strategy's sizing.
_LIMITS = RiskLimits(
    max_order_value=10_000_000.0,
    max_position_pct=1.0,
    max_daily_loss=10_000_000.0,
    max_orders_per_day=100,
    market_hours_only=False,
)


def _config() -> StrategyConfig:
    return StrategyConfig(
        name="acceptance",
        capital=100_000.0,
        universe=UniverseSpec(symbols=["AAA", "BBB", "CCC"], point_in_time=False),
        signals=[SignalSpec(id="px", name="acceptance_close")],
        score=ScoreSpec(type="single"),
        selection=SelectionSpec(method="top_n", n=2, exit_rank=2),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.6),
    )


def _seed(bar_store: BarStore, symbol: str, days: list[tuple[date, float, float]]) -> None:
    """days: (day, open, close) rows written in one frame."""
    df = pl.DataFrame(
        {
            "ts": [datetime.combine(d, time(0, 0)) for d, _, _ in days],
            "open": [o for _, o, _ in days],
            "high": [max(o, c) for _, o, c in days],
            "low": [min(o, c) for _, o, c in days],
            "close": [c for _, _, c in days],
            "volume": [100_000] * len(days),
        }
    )
    bar_store.write_raw(symbol, Timeframe.DAY, df)


def test_full_two_day_paper_session_produces_fills_and_eod_report(
    settings: Settings,
) -> None:
    config = _config()
    store = PaperStore(settings.paper_db_path, config.name)
    store.ensure_run(config.capital)
    calendar = NSECalendar(settings)
    clock = _Clock(datetime.combine(D1, time(15, 35)))
    broker = PaperBroker(
        settings,
        strategy_id=config.name,
        capital=config.capital,
        slippage_bps=10.0,
        risk_limits=_LIMITS,
        calendar=calendar,
        store=store,
        enforce_market_hours=False,
        now_fn=clock,
    )
    runner = PaperSessionRunner(settings, config, broker, calendar=calendar, store=store)
    bar_store = BarStore(settings)

    # ---- D1: bars through D1, close routine queues the D2 rebalance -------
    _seed(bar_store, "AAA", [(D1, 100.0, 100.0)])
    _seed(bar_store, "BBB", [(D1, 200.0, 200.0)])
    _seed(bar_store, "CCC", [(D1, 50.0, 50.0)])

    report_d1 = runner.on_session_close(D1)
    assert report_d1.exists()

    planned = store.planned_orders(D2)
    assert [(o.client_order_id, o.qty) for o in planned] == [
        (f"acceptance-{D2.isoformat()}-AAA-BUY", 500),
        (f"acceptance-{D2.isoformat()}-BBB-BUY", 250),
    ]

    # ---- D2 morning, real scheduler ordering: open job BEFORE any tick ----
    _seed(bar_store, "AAA", [(D2, 99.0, 101.0)])
    _seed(bar_store, "BBB", [(D2, 197.0, 199.0)])
    _seed(bar_store, "CCC", [(D2, 50.0, 50.0)])
    clock.now = datetime.combine(D2, time(9, 15))

    # No quote exists yet: both planned MARKET orders must survive as PENDING
    # (fault-tolerant open), not abort or half-place.
    assert runner.on_session_open(D2) == []
    assert all(o.status == OrderStatus.PENDING for o in store.planned_orders(D2))

    # The day's first quotes arrive (bar OPEN as the first tick), the retry
    # places both orders, and they fill at open +/- slippage.
    assert runner.prime_open_quotes(D2) == 2
    clock.now = datetime.combine(D2, time(9, 16))
    placed = runner.on_session_open(D2)
    assert [o.status for o in placed] == [OrderStatus.COMPLETE, OrderStatus.COMPLETE]

    fills = store.all_fills()
    assert [(f.symbol, f.qty, f.price) for f in fills] == [
        ("AAA", 500, pytest.approx(99.10)),  # round(99 * 1.001, 2)
        ("BBB", 250, pytest.approx(197.20)),  # round(197 * 1.001, 2)
    ]
    holdings = {p.symbol: p.qty for p in broker.get_holdings()}
    assert holdings == {"AAA": 500, "BBB": 250}

    # ---- D2 intraday: a live tick marks the book (no working orders) ------
    broker.on_tick(
        Tick(
            symbol="AAA",
            instrument_token=1,
            ts=datetime.combine(D2, time(12, 0)),
            last_price=100.5,
            bid=100.4,
            ask=100.6,
            volume=10_000,
        )
    )

    # ---- D2 close: mark to official closes, snapshot, report --------------
    clock.now = datetime.combine(D2, time(15, 35))
    report_d2 = runner.on_session_close(D2)
    assert report_d2.exists()

    cash = broker.get_margins().cash_available
    assert broker.equity() == pytest.approx(cash + 500 * 101.0 + 250 * 199.0)

    curve = store.equity_curve()
    assert list(curve.index) == [
        datetime.combine(D1, time(15, 30)),  # D1 close snapshot
        datetime.combine(D2, time(9, 15)),  # D2 day-start (max_daily_loss basis)
        datetime.combine(D2, time(15, 30)),  # D2 close snapshot
    ]
    assert curve.iloc[0] == pytest.approx(100_000.0)  # nothing traded on D1
    assert curve.iloc[1] == pytest.approx(100_000.0)  # day start: still all cash
    assert curve.iloc[2] == pytest.approx(broker.equity())

    # ---- restart: a fresh broker over the same store agrees ---------------
    broker2 = PaperBroker(
        settings,
        strategy_id=config.name,
        capital=config.capital,
        slippage_bps=10.0,
        risk_limits=_LIMITS,
        calendar=calendar,
        store=store,
        enforce_market_hours=False,
        now_fn=clock,
    )
    assert broker2.get_margins().cash_available == pytest.approx(cash)
    assert {p.symbol: p.qty for p in broker2.get_holdings()} == holdings

"""End-to-end event-engine behaviour on hand-built and synthetic frames.

Deterministic, no live APIs. Covers: a monthly top-1 momentum run (monotonic
time index, trades logged, bit-for-bit reproducible); symbol-routed regime
filter sending the whole book to cash; buffer-zone retention; mid-run delisting
force-exit at a haircut; the portfolio drawdown kill switch; and propagation of
the StaticUniverseResolver survivorship-bias warning.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest
from fixtures.synthetic import synthetic_daily, synthetic_universe

from tradingos.config.schemas import (
    ExecutionSpec,
    FilterSpec,
    OverlaySpec,
    RebalanceSpec,
    ScoreSpec,
    SelectionSpec,
    SignalSpec,
    SizingSpec,
    StrategyConfig,
    UniverseSpec,
)
from tradingos.core.models import Timeframe
from tradingos.engine.base import StaticUniverseResolver
from tradingos.engine.dataview import MarketData
from tradingos.engine.event.engine import EventEngine
from tradingos.strategies.registry import register_signal

_INDEX = "NIFTY 50"


@register_signal("test_engine_mom", tier="custom", window=63)
def _mom(df: pd.DataFrame, **params: object) -> pd.Series:
    """Trailing return over ``window`` bars (causal)."""
    window = int(params["window"])
    return df["close"].pct_change(window)


@register_signal("test_engine_close", tier="custom")
def _close(df: pd.DataFrame, **params: object) -> pd.Series:
    """Rank by the latest close (causal)."""
    return df["close"].astype("float64")


def _flat(dates: pd.DatetimeIndex, closes: list[float], opens: list[float] | None = None,
          volume: int = 10_000_000) -> pd.DataFrame:
    o = opens if opens is not None else list(closes)
    return pd.DataFrame(
        {
            "open": o,
            "high": [max(a, b) + 5 for a, b in zip(o, closes, strict=True)],
            "low": [min(a, b) - 5 for a, b in zip(o, closes, strict=True)],
            "close": closes,
            "volume": [volume] * len(dates),
        },
        index=dates,
    )


# ---------------------------------------------------------------------------
# momentum end-to-end: monotonic time, trades logged, deterministic
# ---------------------------------------------------------------------------


def test_momentum_run_is_monotonic_logged_and_deterministic() -> None:
    frames = synthetic_universe(["AAA", "BBB", "CCC"], start=date(2019, 1, 1), end=date(2021, 12, 31))
    # a strongly-rising index so the regime gate is mostly open and trades happen
    frames[_INDEX] = synthetic_daily(
        _INDEX, start=date(2019, 1, 1), end=date(2021, 12, 31), seed=99, drift=0.30, vol=0.10
    )
    data = MarketData(frames, timeframe=Timeframe.DAY, snapshot_id="mom")

    cfg = StrategyConfig(
        name="mom_top1",
        start=date(2019, 1, 1),
        end=date(2021, 12, 31),
        capital=1_000_000,
        universe=UniverseSpec(symbols=["AAA", "BBB", "CCC"], point_in_time=False),
        signals=[SignalSpec(id="mom", name="test_engine_mom", params={"window": 63})],
        score=ScoreSpec(type="single"),
        filters=[FilterSpec(name="index_above_ma", params={"window": 50, "symbol": _INDEX})],
        selection=SelectionSpec(method="top_n", n=1, exit_rank=2),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.9),
        rebalance=RebalanceSpec(frequency="monthly", trading_day=1),
    )
    r1 = EventEngine().run(cfg, data, StaticUniverseResolver())
    r2 = EventEngine().run(cfg, data, StaticUniverseResolver())

    assert r1.equity.index.is_monotonic_increasing
    assert (r1.gross_equity >= r1.equity - 1e-6).all()  # gross never below net
    assert r1.trades, "expected trades to be logged"
    assert r1.total_costs > 0
    # bit-for-bit reproducible
    assert r1.equity.equals(r2.equity)
    assert r1.gross_equity.equals(r2.gross_equity)
    assert [t.model_dump() for t in r1.trades] == [t.model_dump() for t in r2.trades]
    # gross - net == cumulative costs at the final bar
    assert round(r1.gross_equity.iloc[-1] - r1.equity.iloc[-1], 2) == r1.total_costs


# ---------------------------------------------------------------------------
# regime routing: index below its MA -> whole book to cash
# ---------------------------------------------------------------------------


def test_symbol_routed_regime_filter_sends_book_to_cash() -> None:
    dates = pd.date_range(date(2021, 1, 1), periods=10, freq="B")
    # a strongly trending tradable name so a held position would keep moving
    stock = _flat(dates, [100, 110, 120, 130, 140, 150, 160, 170, 180, 190])
    # index rises (above 3-day MA) then crashes below it from bar index 6 on
    idx = _flat(dates, [100, 101, 102, 103, 104, 105, 80, 79, 78, 77])
    data = MarketData({"AAA": stock, _INDEX: idx}, timeframe=Timeframe.DAY, snapshot_id="regime")

    base = dict(
        name="regime",
        start=date(2021, 1, 1),
        end=date(2021, 1, 31),
        capital=1_000_000,
        universe=UniverseSpec(symbols=["AAA"], point_in_time=False),
        signals=[SignalSpec(id="c", name="test_engine_close")],
        score=ScoreSpec(type="single"),
        selection=SelectionSpec(method="top_n", n=1, exit_rank=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.9),
        rebalance=RebalanceSpec(frequency="daily"),
        execution=ExecutionSpec(timing="same_close", max_participation=1.0),
    )
    with_regime = StrategyConfig(
        filters=[FilterSpec(name="index_above_ma", params={"window": 3, "symbol": _INDEX})], **base
    )
    without = StrategyConfig(**base)

    r_regime = EventEngine().run(with_regime, data, StaticUniverseResolver())
    r_hold = EventEngine().run(without, data, StaticUniverseResolver())

    # After the index crashes the regime run is 100% cash: the last two bars'
    # equity is flat even though the stock keeps ripping higher.
    assert r_regime.equity.iloc[-1] == pytest.approx(r_regime.equity.iloc[-2])
    # The control (no regime filter) is still fully invested and keeps moving.
    assert r_hold.equity.iloc[-1] != pytest.approx(r_hold.equity.iloc[-2])
    assert r_regime.equity.iloc[-1] < r_hold.equity.iloc[-1]


# ---------------------------------------------------------------------------
# buffer-zone retention
# ---------------------------------------------------------------------------


def test_buffer_zone_retains_holding_between_n_and_exit_rank() -> None:
    dates = pd.date_range(date(2021, 1, 1), periods=4, freq="B")
    # ranks by close: t1 A>B>C ; t2 B>A>C (A drifts to rank 2) ; t3 B>C>A (rank 3)
    aaa = _flat(dates, [100, 100, 100, 100])
    bbb = _flat(dates, [90, 110, 110, 110])
    ccc = _flat(dates, [80, 80, 105, 105])
    data = MarketData(
        {"AAA": aaa, "BBB": bbb, "CCC": ccc}, timeframe=Timeframe.DAY, snapshot_id="buffer"
    )

    base = dict(
        name="buffer",
        start=date(2021, 1, 1),
        end=date(2021, 1, 31),
        capital=1_000_000,
        universe=UniverseSpec(symbols=["AAA", "BBB", "CCC"], point_in_time=False),
        signals=[SignalSpec(id="c", name="test_engine_close")],
        score=ScoreSpec(type="single"),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.9),
        rebalance=RebalanceSpec(frequency="daily"),
        execution=ExecutionSpec(timing="same_close", max_participation=1.0),
    )
    buffered = StrategyConfig(selection=SelectionSpec(method="top_n", n=1, exit_rank=2), **base)
    unbuffered = StrategyConfig(selection=SelectionSpec(method="top_n", n=1, exit_rank=1), **base)

    r_buf = EventEngine().run(buffered, data, StaticUniverseResolver())
    r_unbuf = EventEngine().run(unbuffered, data, StaticUniverseResolver())

    def aaa_qty_sold_on(res: object, d: date) -> int:
        return sum(
            t.qty for t in res.trades if t.symbol == "AAA" and t.exit_ts.date() == d
        )

    t2, t3 = dates[1].date(), dates[2].date()
    # Buffered: AAA is RETAINED at t2 (rank 2 <= exit_rank 2) — at most a tiny
    # re-size trim sells — and the BULK of AAA is only unwound at t3 (rank 3).
    assert aaa_qty_sold_on(r_buf, t3) > aaa_qty_sold_on(r_buf, t2)
    # Unbuffered: AAA is dumped wholesale one bar earlier, at t2.
    assert aaa_qty_sold_on(r_unbuf, t2) > aaa_qty_sold_on(r_unbuf, t3)
    # The buffer's whole point: far less AAA is sold at t2 than without it.
    assert aaa_qty_sold_on(r_buf, t2) < aaa_qty_sold_on(r_unbuf, t2)


# ---------------------------------------------------------------------------
# delisting force-exit
# ---------------------------------------------------------------------------


def test_delisting_force_exits_at_haircut_with_warning() -> None:
    full_dates = pd.date_range(date(2021, 1, 1), periods=8, freq="B")
    short_dates = full_dates[:5]  # DDD's frame ends mid-run
    ddd = _flat(short_dates, [300, 300, 300, 300, 300])  # highest -> always picked
    eee = _flat(full_dates, [100, 100, 100, 100, 100, 100, 100, 100])
    fff = _flat(full_dates, [90, 90, 90, 90, 90, 90, 90, 90])
    data = MarketData(
        {"DDD": ddd, "EEE": eee, "FFF": fff}, timeframe=Timeframe.DAY, snapshot_id="delist"
    )

    cfg = StrategyConfig(
        name="delist",
        start=date(2021, 1, 1),
        end=date(2021, 1, 31),
        capital=1_000_000,
        universe=UniverseSpec(symbols=["DDD", "EEE", "FFF"], point_in_time=False),
        signals=[SignalSpec(id="c", name="test_engine_close")],
        score=ScoreSpec(type="single"),
        selection=SelectionSpec(method="top_n", n=1, exit_rank=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.9),
        rebalance=RebalanceSpec(frequency="daily"),
        execution=ExecutionSpec(timing="same_close", max_participation=1.0),
    )
    res = EventEngine().run(cfg, data, StaticUniverseResolver())

    delist_trades = [t for t in res.trades if t.exit_reason == "delisted"]
    assert len(delist_trades) == 1
    # forced exit at close(last DDD bar) * (1 - haircut 0.20) = 300 * 0.8 = 240.00
    assert delist_trades[0].symbol == "DDD"
    assert delist_trades[0].exit_price == pytest.approx(240.00)
    assert delist_trades[0].exit_ts.date() == short_dates[-1].date()
    assert any("DELISTING: DDD" in w for w in res.warnings)


# ---------------------------------------------------------------------------
# portfolio drawdown kill switch
# ---------------------------------------------------------------------------


def test_drawdown_kill_switch_liquidates_and_halts() -> None:
    dates = pd.date_range(date(2021, 1, 1), periods=8, freq="B")
    # rise to a peak, then a >10% crash, then recovery the kill switch must ignore
    x = _flat(dates, [100, 110, 120, 130, 100, 105, 140, 150])
    data = MarketData({"XXX": x}, timeframe=Timeframe.DAY, snapshot_id="kill")

    cfg = StrategyConfig(
        name="kill",
        start=date(2021, 1, 1),
        end=date(2021, 1, 31),
        capital=1_000_000,
        universe=UniverseSpec(symbols=["XXX"], point_in_time=False),
        selection=SelectionSpec(method="top_n", n=1, exit_rank=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.9),
        overlays=[OverlaySpec(name="portfolio_drawdown_stop", params={"max_dd": 0.10})],
        rebalance=RebalanceSpec(frequency="daily"),
        execution=ExecutionSpec(timing="next_open", max_participation=1.0),
    )
    res = EventEngine().run(cfg, data, StaticUniverseResolver())

    kill_trades = [t for t in res.trades if t.exit_reason == "kill_switch"]
    assert len(kill_trades) == 1
    assert any("KILL SWITCH" in w for w in res.warnings)
    # once halted, no re-entry: equity is flat (all cash) over the final bars
    # despite XXX rallying to 150.
    assert res.equity.iloc[-1] == pytest.approx(res.equity.iloc[-2])
    assert res.equity.iloc[-1] == pytest.approx(res.equity.iloc[-3])


# ---------------------------------------------------------------------------
# survivorship-bias warning propagation
# ---------------------------------------------------------------------------


def test_pit_survivorship_warning_propagates_into_result() -> None:
    frames = synthetic_universe(["AAA", "BBB"], start=date(2021, 1, 1), end=date(2021, 6, 30))
    data = MarketData(frames, timeframe=Timeframe.DAY, snapshot_id="pit")
    cfg = StrategyConfig(
        name="pit",
        start=date(2021, 1, 1),
        end=date(2021, 6, 30),
        capital=1_000_000,
        # point_in_time with no explicit symbol list -> resolver must warn
        universe=UniverseSpec(index="NIFTY500", point_in_time=True),
        selection=SelectionSpec(method="top_n", n=1, exit_rank=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.9),
        rebalance=RebalanceSpec(frequency="monthly", trading_day=1),
    )
    res = EventEngine().run(cfg, data, StaticUniverseResolver())
    assert any("SURVIVORSHIP BIAS" in w for w in res.warnings)


# ---------------------------------------------------------------------------
# calendar clipping at config.end
# ---------------------------------------------------------------------------


def test_run_never_extends_past_config_end() -> None:
    """Regression: `end` clipping must be exclusive of end+1. With daily bars
    stamped at midnight, a bar dated end+1 satisfies `<= end + 1 day` exactly,
    so an inclusive comparison silently simulated one extra day and reported
    the wrong result.end."""
    frames = {"AAA": synthetic_daily("AAA", start=date(2021, 1, 1), end=date(2021, 3, 31))}
    data = MarketData(frames, timeframe=Timeframe.DAY, snapshot_id="clip")
    # 2021-02-25 is a Thursday; 2021-02-26 (Friday) is a bar in the data, and
    # sits exactly at end + 1 day midnight — the old inclusive bound kept it.
    cfg = StrategyConfig(
        name="clip",
        start=date(2021, 1, 1),
        end=date(2021, 2, 25),
        capital=1_000_000,
        universe=UniverseSpec(symbols=["AAA"], point_in_time=False),
        selection=SelectionSpec(method="top_n", n=1, exit_rank=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.9),
        rebalance=RebalanceSpec(frequency="monthly", trading_day=1),
    )
    res = EventEngine().run(cfg, data, StaticUniverseResolver())
    assert res.equity.index.max() == pd.Timestamp("2021-02-25")
    assert res.end == date(2021, 2, 25)

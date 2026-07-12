"""Benchmark-frame routing for signals (Batch 3, item #11 — Part 1).

A SignalSpec may name a `benchmark`; when set, the engine joins that symbol's
close onto the traded frame as a causal `benchmark_close` column BEFORE the
signal fn runs — the second-frame analogue of the `symbol`-routed regime
filters. Covered here:

  * the joined column is present, aligned by exact timestamp, and NaN where the
    benchmark has no bar at that stamp;
  * causality: altering FUTURE benchmark bars never changes the value at t;
  * without `benchmark`, the frame the signal sees is unchanged (a
    benchmark-reading signal raises; a plain signal is byte-identical);
  * the cache keys benchmark into its identity (no cross-benchmark collision);
  * a benchmark symbol absent from the run's data fails loudly;
  * DataView.signal and strategy_runtime._score both forward `sig.benchmark`.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest
from fixtures.synthetic import synthetic_daily

from tradingos.config.schemas import (
    ScoreSpec,
    SignalSpec,
    StrategyConfig,
    UniverseSpec,
)
from tradingos.core.errors import DataError
from tradingos.core.models import Timeframe
from tradingos.engine.dataview import DataView, MarketData, SignalStore, _join_benchmark_close
from tradingos.engine.event.strategy_runtime import _score
from tradingos.strategies.registry import compute_signal, register_signal


@register_signal("test_bench_echo", tier="custom")
def _bench_echo(df: pd.DataFrame, **_params: object) -> pd.Series:
    """Echo the routed benchmark_close column; raise if it was not joined."""
    if "benchmark_close" not in df.columns:
        raise ValueError("benchmark_close absent — benchmark was not routed")
    return df["benchmark_close"].astype("float64")


def _stock() -> pd.DataFrame:
    return synthetic_daily("BENCH_STOCK", start=date(2022, 1, 1), end=date(2023, 12, 31), seed=1)


def _bench(seed: int = 2) -> pd.DataFrame:
    return synthetic_daily("BENCH_IDX", start=date(2022, 1, 1), end=date(2023, 12, 31), seed=seed)


# ---------------------------------------------------------------------------
# the join: presence, alignment, NaN where the benchmark has no bar
# ---------------------------------------------------------------------------


def test_join_aligns_benchmark_close_by_exact_timestamp_and_nans_gaps() -> None:
    stock = _stock()
    bench = _bench()
    # drop a handful of benchmark bars: the stock keeps those dates, so the
    # joined column must be NaN exactly there and equal to the benchmark close
    # everywhere the benchmark still has a bar.
    dropped = bench.index[[10, 25, 40]]
    bench_gapped = bench.drop(index=dropped)

    joined = _join_benchmark_close(stock, bench_gapped)

    assert "benchmark_close" in joined.columns
    assert (joined.index == stock.index).all()
    assert joined["benchmark_close"].loc[dropped].isna().all()
    present = stock.index.difference(dropped)
    pd.testing.assert_series_equal(
        joined["benchmark_close"].loc[present],
        bench_gapped["close"].loc[present],
        check_names=False,
    )
    # the source frames are never mutated
    assert "benchmark_close" not in stock.columns


def test_signalstore_routes_benchmark_and_matches_a_manual_join() -> None:
    stock, bench = _stock(), _bench()
    data = MarketData(
        {"STOCK": stock, "BENCH": bench}, timeframe=Timeframe.DAY, snapshot_id="route-manual"
    )
    routed = SignalStore(data).series("STOCK", "test_bench_echo", {}, benchmark="BENCH")

    manual = compute_signal("test_bench_echo", _join_benchmark_close(stock, bench), {})
    pd.testing.assert_series_equal(routed, manual, check_names=False)


# ---------------------------------------------------------------------------
# causality: future benchmark bars cannot change the value at t
# ---------------------------------------------------------------------------


def test_future_benchmark_bars_do_not_change_the_value_at_t() -> None:
    stock = _stock()
    bench_a = _bench()
    cut = stock.index[len(stock) // 2]

    # bench_b == bench_a up to and including `cut`; every bar AFTER cut is
    # perturbed. A causal join reads benchmark_close[t] = bench[t], so the
    # routed signal at rows <= cut must be identical between the two.
    bench_b = bench_a.copy()
    future = bench_b.index > cut
    bench_b.loc[future, "close"] = bench_b.loc[future, "close"] * 3.0 + 7.0

    # small windows so the signal is warmed up on BOTH sides of the cut (a
    # 2-year frame can't warm the 252/21/252 defaults).
    params = {"window": 40, "skip": 2, "beta_window": 40}

    def routed(bench: pd.DataFrame) -> pd.Series:
        data = MarketData(
            {"STOCK": stock, "BENCH": bench}, timeframe=Timeframe.DAY, snapshot_id="causal"
        )
        return SignalStore(data).series("STOCK", "residual_momentum", params, benchmark="BENCH")

    sig_a = routed(bench_a)
    sig_b = routed(bench_b)
    pd.testing.assert_series_equal(sig_a.loc[:cut], sig_b.loc[:cut], check_names=False)
    # sanity: the perturbation DID change something after the cut (otherwise the
    # test proves nothing) — later rows depend on the altered future bars.
    after = sig_a.index > cut
    assert not np.allclose(
        sig_a[after].to_numpy(), sig_b[after].to_numpy(), equal_nan=True
    )


# ---------------------------------------------------------------------------
# no-benchmark: the input frame is unchanged
# ---------------------------------------------------------------------------


def test_without_benchmark_a_benchmark_reading_signal_raises() -> None:
    stock, bench = _stock(), _bench()
    data = MarketData(
        {"STOCK": stock, "BENCH": bench}, timeframe=Timeframe.DAY, snapshot_id="no-bench"
    )
    with pytest.raises(ValueError, match="benchmark_close absent"):
        SignalStore(data).series("STOCK", "test_bench_echo", {})  # benchmark defaulted to None


def test_without_benchmark_a_plain_signal_is_unchanged() -> None:
    stock, bench = _stock(), _bench()
    data = MarketData(
        {"STOCK": stock, "BENCH": bench}, timeframe=Timeframe.DAY, snapshot_id="plain"
    )
    routed = SignalStore(data).series("STOCK", "return_over_window", {"window": 63, "skip": 5})
    direct = compute_signal("return_over_window", stock, {"window": 63, "skip": 5})
    pd.testing.assert_series_equal(routed, direct, check_names=False)


# ---------------------------------------------------------------------------
# cache identity + missing-benchmark error
# ---------------------------------------------------------------------------


def test_cache_does_not_collide_across_different_benchmarks() -> None:
    stock = _stock()
    bench_x = _bench(seed=2)
    bench_y = _bench(seed=3)
    data = MarketData(
        {"STOCK": stock, "BX": bench_x, "BY": bench_y},
        timeframe=Timeframe.DAY,
        snapshot_id="cache-id",
    )
    store = SignalStore(data)  # one store: the two reads must not alias
    sx = store.series("STOCK", "test_bench_echo", {}, benchmark="BX")
    sy = store.series("STOCK", "test_bench_echo", {}, benchmark="BY")
    assert not sx.equals(sy)
    pd.testing.assert_series_equal(sx, bench_x["close"].astype("float64"), check_names=False)
    pd.testing.assert_series_equal(sy, bench_y["close"].astype("float64"), check_names=False)


def test_missing_benchmark_symbol_fails_loudly() -> None:
    stock = _stock()
    data = MarketData({"STOCK": stock}, timeframe=Timeframe.DAY, snapshot_id="missing-bench")
    with pytest.raises(DataError):
        SignalStore(data).series("STOCK", "test_bench_echo", {}, benchmark="NOT_LOADED")


# ---------------------------------------------------------------------------
# DataView.signal and _score forward sig.benchmark
# ---------------------------------------------------------------------------


def test_dataview_signal_forwards_benchmark_through_the_visibility_guard() -> None:
    stock, bench = _stock(), _bench()
    data = MarketData(
        {"STOCK": stock, "BENCH": bench}, timeframe=Timeframe.DAY, snapshot_id="dv-forward"
    )
    now = stock.index[-1] + timedelta(hours=16)  # after close: last bar visible
    dv = DataView(data, SignalStore(data), now)

    params = {"window": 40, "skip": 2, "beta_window": 40}
    val = dv.signal("STOCK", "residual_momentum", params, benchmark="BENCH")
    assert val is not None and np.isfinite(val)

    # the visible series equals the routed full series sliced at the cutoff
    series = dv.signal_series("STOCK", "residual_momentum", params, benchmark="BENCH")
    assert series.index.max() == stock.index[-1]


def test_score_routes_each_signals_benchmark() -> None:
    stock, bench = _stock(), _bench()
    data = MarketData(
        {"STOCK": stock, "BENCH": bench}, timeframe=Timeframe.DAY, snapshot_id="score-route"
    )
    now = stock.index[-1] + timedelta(hours=16)
    dv = DataView(data, SignalStore(data), now)

    config = StrategyConfig(
        name="resid-mom-route-test",
        universe=UniverseSpec(symbols=["STOCK"]),
        signals=[
            SignalSpec(
                id="rm",
                name="residual_momentum",
                params={"window": 40, "skip": 2, "beta_window": 40},
                benchmark="BENCH",
            )
        ],
        score=ScoreSpec(type="single"),
    )

    scores = _score(config, dv, ["STOCK"])
    # STOCK is warmed up (2 years of bars vs ~82-bar warmup) -> a finite score,
    # which is only computable if _score routed BENCH onto STOCK's frame.
    assert "STOCK" in scores
    assert np.isfinite(scores["STOCK"])
    assert scores["STOCK"] == pytest.approx(
        dv.signal("STOCK", "residual_momentum", config.signals[0].params, benchmark="BENCH")
    )

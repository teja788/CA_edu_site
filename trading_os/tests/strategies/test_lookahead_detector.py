"""The framework guarantee: an automated look-ahead detector.

Two halves, per initial_prompt.md MODULE 2:

  (a) PIT certification — every signal in registry.list_signals() and every
      registered filter is computed on a synthetic frame, then re-computed
      on that frame truncated at several probe timestamps; the value at each
      probe point must be identical whether or not later rows existed. Any
      registered signal/filter that fails is a genuine look-ahead leak and
      the test fails loudly, naming it. Probe points span BOTH the early
      (warm-up) region and the tail of the frame: warm-up-only leaks (e.g. a
      bfill that copies a future value back over the warm-up window) are
      invisible to late probes. Signals/filters are certified with their
      DEFAULT params AND with every param set actually used by the shipped
      strategies in strategies/examples/*.yaml — a leak enabled purely
      through YAML params is caught too.

  (b) Framework blocking — a deliberately-leaky signal registered inside
      this test must be CAUGHT by (a)'s checker; the DataView-level API must
      never expose bars beyond its visibility cutoff and must raise
      LookAheadError for a future timestamp; and shifting all input data
      forward one day must change a simple signal's latest visible value.

Test-only signal names are prefixed `test_lookahead_` so they never collide
with real signal names.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest
from fixtures.synthetic import synthetic_daily

from tradingos.config.loader import load_strategy
from tradingos.core.errors import DataError, LookAheadError
from tradingos.core.models import Timeframe
from tradingos.engine.dataview import DataView, MarketData, SignalStore
from tradingos.strategies import registry
from tradingos.strategies.registry import register_signal

# Skip-list for genuinely-known, documented look-ahead exceptions. Must start
# EMPTY: any registered signal/filter added here needs a comment citing why
# it cannot be made point-in-time-safe (there should be none in a healthy
# registry — see the implementer's final report if this is ever non-empty).
_SKIP: frozenset[str] = frozenset()

_N_BARS = 400
_N_PROBES = 10

# The earliest probe position. Early probes sit INSIDE typical indicator
# warm-up windows, where backfill-style leaks live (a bfill'd warm-up copies a
# FUTURE value over rows before it — invisible to any probe past the warm-up).
# The floor cannot be arbitrarily low: several pandas_ta_classic indicators
# cannot compute AT ALL on very short frames (ta.trix raises below ~91 rows;
# supertrend/ichimoku return None below their window lengths, making a causal
# warm-up value on the full frame look like a mismatch). 100 bars is the
# smallest truncated length every registered indicator computes on, verified
# empirically against the whole registry.
_EARLY_PROBE_FLOOR = 100

_EXAMPLES_DIR = (
    Path(__file__).resolve().parents[2] / "src" / "tradingos" / "strategies" / "examples"
)


def _probe_frame() -> pd.DataFrame:
    """~400-bar synthetic daily OHLCV frame, deterministic."""
    df = synthetic_daily(
        "LOOKAHEAD_PROBE", start=date(2019, 1, 1), end=date(2021, 12, 31), seed=42
    )
    return df.iloc[:_N_BARS]


def _probe_times(df: pd.DataFrame) -> list[pd.Timestamp]:
    """K probe timestamps from the early warm-up region through the frame end."""
    n = len(df)
    positions = np.linspace(_EARLY_PROBE_FLOOR, n - 1, num=_N_PROBES, dtype=int)
    return [df.index[p] for p in sorted(set(positions))]


def _assert_values_match(full_val: object, trunc_val: object, where: str) -> None:
    full_na, trunc_na = pd.isna(full_val), pd.isna(trunc_val)
    if full_na or trunc_na:
        if full_na != trunc_na:
            raise AssertionError(
                f"{where}: NaN mismatch (full={full_val!r}, truncated={trunc_val!r}) "
                "— truncating the frame at t changed whether t's value is known, "
                "which means the full computation used rows after t"
            )
        return
    if isinstance(full_val, (bool, np.bool_)) or isinstance(trunc_val, (bool, np.bool_)):
        if bool(full_val) != bool(trunc_val):
            raise AssertionError(f"{where}: {full_val!r} != {trunc_val!r}")
        return
    if not np.isclose(float(full_val), float(trunc_val), rtol=1e-9, atol=1e-12):
        raise AssertionError(f"{where}: full={full_val!r} != truncated={trunc_val!r}")


def _certify_signal_causal(
    name: str,
    df: pd.DataFrame,
    probe_times: list[pd.Timestamp],
    params: dict[str, Any] | None = None,
) -> None:
    params = params or {}
    where = f"signal {name!r} (params={params})" if params else f"signal {name!r}"
    full = registry.compute_signal(name, df, params)
    for t in probe_times:
        truncated = df.loc[:t]
        trunc_series = registry.compute_signal(name, truncated, params)
        _assert_values_match(full.loc[t], trunc_series.loc[t], f"{where} at t={t}")


def _certify_filter_causal(
    name: str,
    df: pd.DataFrame,
    probe_times: list[pd.Timestamp],
    params: dict[str, Any] | None = None,
) -> None:
    params = params or {}
    where = f"filter {name!r} (params={params})" if params else f"filter {name!r}"
    filt = registry.get_filter(name)
    full = filt.fn(df, **params)
    for t in probe_times:
        truncated = df.loc[:t]
        trunc_series = filt.fn(truncated, **params)
        _assert_values_match(full.loc[t], trunc_series.loc[t], f"{where} at t={t}")


def _all_registered_filters() -> list[registry.FilterDef]:
    # registry.py exposes no public list_filters(); this task is not allowed
    # to add one (registry.py may only change to import filters.py), so the
    # certifier introspects the private registry directly for test purposes.
    registry.ensure_discovered()
    return sorted(registry._FILTERS.values(), key=lambda d: d.name)  # noqa: SLF001


# --- a small, genuinely causal signal reused by the DataView-level checks ---
@register_signal("test_lookahead_probe_sma", tier="custom", window=10)
def _probe_sma(df: pd.DataFrame, **params: object) -> pd.Series:
    window = params["window"]
    return df["close"].rolling(window=window, min_periods=window).mean()


# ---------------------------------------------------------------------------
# (a) PIT certification of every currently-registered signal and filter
# ---------------------------------------------------------------------------


def test_every_registered_signal_and_filter_is_pit_safe() -> None:
    registry.ensure_discovered()
    df = _probe_frame()
    probe_times = _probe_times(df)
    failures: list[str] = []

    for sig in registry.list_signals():
        if sig.name in _SKIP:
            continue
        try:
            _certify_signal_causal(sig.name, df, probe_times)
        except AssertionError as exc:
            failures.append(f"SIGNAL {sig.name!r} (tier={sig.tier}) LEAKS THE FUTURE: {exc}")
        except Exception as exc:  # noqa: BLE001 - a crash is also a certification failure
            failures.append(
                f"SIGNAL {sig.name!r} (tier={sig.tier}) raised {type(exc).__name__}: {exc}"
            )

    for filt in _all_registered_filters():
        if filt.name in _SKIP:
            continue
        try:
            _certify_filter_causal(filt.name, df, probe_times)
        except AssertionError as exc:
            failures.append(f"FILTER {filt.name!r} LEAKS THE FUTURE: {exc}")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"FILTER {filt.name!r} raised {type(exc).__name__}: {exc}")

    assert not failures, "look-ahead detector found leaking signal(s)/filter(s):\n" + "\n".join(
        failures
    )


# ---------------------------------------------------------------------------
# (b) framework blocking
# ---------------------------------------------------------------------------


def test_certifier_catches_a_shift_negative_leaky_signal() -> None:
    @register_signal("test_lookahead_leaky_future_shift", tier="custom")
    def _leaky_shift(df: pd.DataFrame, **params: object) -> pd.Series:
        return df["close"].shift(-1)  # reads TOMORROW's close: a genuine leak

    df = _probe_frame()
    probe_times = _probe_times(df)
    with pytest.raises(AssertionError):
        _certify_signal_causal("test_lookahead_leaky_future_shift", df, probe_times)


def test_certifier_catches_a_bfill_warmup_leak() -> None:
    """Negative control for the EARLY probes: a rolling mean whose warm-up NaNs
    are backfilled. Row t < window then holds the value computed at the first
    complete window — data strictly AFTER t. The leak exists ONLY inside the
    warm-up region, so it is invisible to second-half probes; the early probe
    positions (< window) must catch it."""
    window = _EARLY_PROBE_FLOOR + 150  # warm-up region safely spans the early probes

    @register_signal("test_lookahead_leaky_bfill_warmup", tier="custom")
    def _leaky_bfill(df: pd.DataFrame, **params: object) -> pd.Series:
        return df["close"].rolling(window=window, min_periods=window).mean().bfill()

    df = _probe_frame()
    probe_times = _probe_times(df)
    assert min(probe_times) < df.index[window], (
        "probe positions no longer reach the warm-up region; early probing regressed"
    )
    with pytest.raises(AssertionError):
        _certify_signal_causal("test_lookahead_leaky_bfill_warmup", df, probe_times)


def test_certifier_probes_the_actual_params_used_by_example_strategies() -> None:
    """Certify every signal and filter with the EXACT params the shipped
    strategies/examples/*.yaml pass — a leak that only manifests under
    non-default params (e.g. a future-shifting `offset`) must not hide behind
    a defaults-only certification."""
    example_paths = sorted(_EXAMPLES_DIR.glob("*.yaml"))
    assert example_paths, f"no example strategies found under {_EXAMPLES_DIR}"

    df = _probe_frame()
    probe_times = _probe_times(df)
    failures: list[str] = []

    for path in example_paths:
        cfg = load_strategy(path)
        for spec in cfg.signals:
            if spec.name in _SKIP:
                continue
            try:
                _certify_signal_causal(spec.name, df, probe_times, params=spec.params)
            except AssertionError as exc:
                failures.append(f"{path.name}: SIGNAL {spec.name!r} LEAKS THE FUTURE: {exc}")
            except Exception as exc:  # noqa: BLE001 - a crash is also a certification failure
                failures.append(
                    f"{path.name}: SIGNAL {spec.name!r} (params={spec.params}) raised "
                    f"{type(exc).__name__}: {exc}"
                )
        for fspec in cfg.filters:
            if fspec.name in _SKIP:
                continue
            # `symbol` is the engine's reserved routing key (which series the
            # filter is evaluated on), popped before the filter fn is called.
            params = {k: v for k, v in fspec.params.items() if k != "symbol"}
            try:
                _certify_filter_causal(fspec.name, df, probe_times, params=params)
            except AssertionError as exc:
                failures.append(f"{path.name}: FILTER {fspec.name!r} LEAKS THE FUTURE: {exc}")
            except Exception as exc:  # noqa: BLE001
                failures.append(
                    f"{path.name}: FILTER {fspec.name!r} (params={params}) raised "
                    f"{type(exc).__name__}: {exc}"
                )

    assert not failures, (
        "look-ahead detector found leaks under example-YAML params:\n" + "\n".join(failures)
    )


def test_certifier_catches_a_full_sample_statistic_leaky_signal() -> None:
    @register_signal("test_lookahead_leaky_full_sample_mean", tier="custom")
    def _leaky_mean(df: pd.DataFrame, **params: object) -> pd.Series:
        # a full-sample statistic broadcast to every row: row t "knows" the
        # mean of rows that come after it whenever t is not the last row
        m = df["close"].mean()
        return pd.Series(m, index=df.index)

    df = _probe_frame()
    probe_times = _probe_times(df)
    with pytest.raises(AssertionError):
        _certify_signal_causal("test_lookahead_leaky_full_sample_mean", df, probe_times)


def test_dataview_never_exposes_bars_beyond_visibility_cutoff() -> None:
    df = synthetic_daily("LOOKAHEAD_DV", start=date(2022, 1, 1), end=date(2023, 6, 30), seed=7)
    data = MarketData({"LOOKAHEAD_DV": df}, timeframe=Timeframe.DAY, snapshot_id="lookahead-dv")
    store = SignalStore(data)

    mid = len(df.index) // 2
    now = df.index[mid] + pd.Timedelta(hours=10)  # before 15:30 close -> today's bar not yet visible
    expected_cutoff = df.index[mid - 1]

    dv = DataView(data, store, now)

    history = dv.history("LOOKAHEAD_DV")
    assert history.index.max() == expected_cutoff
    assert (history.index <= expected_cutoff).all()

    series = dv.signal_series("LOOKAHEAD_DV", "test_lookahead_probe_sma")
    assert series.index.max() == expected_cutoff
    assert (series.index <= expected_cutoff).all()

    # a bar dated after the cutoff must be rejected
    with pytest.raises(LookAheadError):
        dv.assert_visible(df.index[mid])
    # the cutoff bar itself, and anything before it, must be accepted
    dv.assert_visible(expected_cutoff)


def test_shift_all_input_data_forward_one_day_changes_the_visible_result() -> None:
    """The spec's shift test: shifting every timestamp in the input data
    forward by one day must change what's visible at a fixed `now`, and
    therefore change a simple signal's latest visible value."""
    df = synthetic_daily("LOOKAHEAD_SHIFT", start=date(2022, 1, 1), end=date(2023, 6, 30), seed=11)
    shifted = df.copy()
    shifted.index = shifted.index + pd.Timedelta(days=1)

    mid = len(df.index) // 2
    now = df.index[mid] + pd.Timedelta(hours=16)  # after close on that date

    data_a = MarketData({"S": df}, timeframe=Timeframe.DAY, snapshot_id="shift-a")
    data_b = MarketData({"S": shifted}, timeframe=Timeframe.DAY, snapshot_id="shift-b")

    dv_a = DataView(data_a, SignalStore(data_a), now)
    dv_b = DataView(data_b, SignalStore(data_b), now)

    val_a = dv_a.signal("S", "test_lookahead_probe_sma")
    val_b = dv_b.signal("S", "test_lookahead_probe_sma")

    assert val_a is not None and val_b is not None
    assert val_a != pytest.approx(val_b), (
        "shifting all input timestamps forward one day must change which bars "
        "are visible at the same wall-clock `now`, and therefore the signal's "
        "latest visible value"
    )


def test_dataview_missing_timeframe_raises_dataerror() -> None:
    df = synthetic_daily("LOOKAHEAD_MISSING_TF", start=date(2022, 1, 1), end=date(2022, 6, 30))
    data = MarketData({"X": df}, timeframe=Timeframe.DAY, snapshot_id="missing-tf")
    dv = DataView(data, SignalStore(data), df.index[-1] + pd.Timedelta(hours=16))

    with pytest.raises(DataError):
        dv.history("X", timeframe=Timeframe.MINUTE)
    with pytest.raises(DataError):
        dv.signal_series("X", "test_lookahead_probe_sma", timeframe=Timeframe.MINUTE)

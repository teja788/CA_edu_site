"""Tests for strategies/registry.py: registration, lookup, validation,
caching, and auto-discovery.

Test-only signal names are prefixed `test_registry_` so they never collide
with real builtin/factor/custom signal names, and their bodies are all
trivially point-in-time safe (identity / rolling on `df`) so they don't trip
up the look-ahead certifier in test_lookahead_detector.py if that suite
happens to run in the same session.
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from fixtures.synthetic import synthetic_daily

from tradingos.core.errors import ConfigError
from tradingos.strategies import registry
from tradingos.strategies.registry import (
    compute_signal,
    ensure_discovered,
    get_filter,
    get_signal,
    list_signals,
    register_signal,
    signal_cache_key,
)


@pytest.fixture()
def df() -> pd.DataFrame:
    return synthetic_daily("REG_TEST", start=date(2021, 1, 1), end=date(2021, 12, 31))


def test_register_and_get_signal_roundtrip(df: pd.DataFrame) -> None:
    @register_signal("test_registry_roundtrip", tier="custom")
    def _identity(frame: pd.DataFrame, **params: object) -> pd.Series:
        return frame["close"]

    sig = get_signal("test_registry_roundtrip")
    assert sig.name == "test_registry_roundtrip"
    assert sig.tier == "custom"
    out = compute_signal("test_registry_roundtrip", df, {})
    assert (out.values == df["close"].values).all()


def test_register_signal_name_is_case_insensitive(df: pd.DataFrame) -> None:
    @register_signal("Test_Registry_CaseInsensitive", tier="custom")
    def _identity(frame: pd.DataFrame, **params: object) -> pd.Series:
        return frame["close"]

    assert get_signal("test_registry_caseinsensitive").name == "test_registry_caseinsensitive"
    assert get_signal("TEST_REGISTRY_CASEINSENSITIVE").name == "test_registry_caseinsensitive"


def test_re_registering_a_signal_name_logs_a_warning_and_overrides(
    caplog: pytest.LogCaptureFixture,
) -> None:
    @register_signal("test_registry_dup", tier="custom")
    def _first(frame: pd.DataFrame, **params: object) -> pd.Series:
        return frame["close"]

    with caplog.at_level(logging.WARNING, logger="tradingos.strategies.registry"):

        @register_signal("test_registry_dup", tier="custom")
        def _second(frame: pd.DataFrame, **params: object) -> pd.Series:
            return frame["close"] * 2.0

    assert any(
        "test_registry_dup" in rec.message and "re-registered" in rec.message
        for rec in caplog.records
    )
    # second registration wins
    assert get_signal("test_registry_dup").fn is _second


def test_unknown_signal_raises_configerror_listing_candidates() -> None:
    ensure_discovered()
    with pytest.raises(ConfigError) as excinfo:
        get_signal("definitely_not_a_real_signal_xyz")
    msg = str(excinfo.value)
    assert "unknown signal" in msg
    assert "definitely_not_a_real_signal_xyz" in msg
    assert "Registered:" in msg


def test_unknown_filter_raises_configerror() -> None:
    ensure_discovered()
    with pytest.raises(ConfigError, match="unknown filter"):
        get_filter("definitely_not_a_real_filter_xyz")


def test_compute_signal_rejects_non_series_return(df: pd.DataFrame) -> None:
    @register_signal("test_registry_bad_type", tier="custom")
    def _bad(frame: pd.DataFrame, **params: object) -> list:  # type: ignore[override]
        return list(frame["close"])

    with pytest.raises(ConfigError, match="expected pd.Series"):
        compute_signal("test_registry_bad_type", df, {})


def test_compute_signal_rejects_wrong_length(df: pd.DataFrame) -> None:
    @register_signal("test_registry_bad_length", tier="custom")
    def _bad_len(frame: pd.DataFrame, **params: object) -> pd.Series:
        return frame["close"].iloc[:-1]

    with pytest.raises(ConfigError, match="wrong length"):
        compute_signal("test_registry_bad_length", df, {})


def test_compute_signal_result_is_reindexed_and_float64(df: pd.DataFrame) -> None:
    @register_signal("test_registry_dtype", tier="custom")
    def _ints(frame: pd.DataFrame, **params: object) -> pd.Series:
        # deliberately return a plain-int-indexed series of the right length
        return pd.Series(range(len(frame)))

    out = compute_signal("test_registry_dtype", df, {})
    assert out.dtype == "float64"
    assert (out.index == df.index).all()


def test_defaults_merged_with_params_and_yaml_params_override(df: pd.DataFrame) -> None:
    captured: dict[str, object] = {}

    @register_signal("test_registry_defaults", tier="custom", window=10)
    def _probe(frame: pd.DataFrame, **params: object) -> pd.Series:
        captured["window"] = params["window"]
        return frame["close"]

    compute_signal("test_registry_defaults", df, {})
    assert captured["window"] == 10  # default used when YAML supplies nothing

    compute_signal("test_registry_defaults", df, {"window": 5})
    assert captured["window"] == 5  # YAML param overrides the registered default


def test_list_signals_sorted_by_tier_then_name_with_valid_tiers() -> None:
    ensure_discovered()
    defs = list_signals()
    assert defs == sorted(defs, key=lambda d: (d.tier, d.name))
    assert all(d.tier in {"builtin", "factor", "custom"} for d in defs)


def test_signal_cache_key_is_order_independent_and_symbol_snapshot_sensitive() -> None:
    k1 = signal_cache_key("INFY", "rsi", {"length": 14, "scalar": 100}, "snap1")
    k2 = signal_cache_key("INFY", "rsi", {"scalar": 100, "length": 14}, "snap1")
    assert k1 == k2, "param dict key order must not affect the cache key"

    k_diff_snapshot = signal_cache_key("INFY", "rsi", {"length": 14, "scalar": 100}, "snap2")
    assert k1 != k_diff_snapshot

    k_diff_symbol = signal_cache_key("TCS", "rsi", {"length": 14, "scalar": 100}, "snap1")
    assert k1 != k_diff_symbol

    k_diff_params = signal_cache_key("INFY", "rsi", {"length": 21, "scalar": 100}, "snap1")
    assert k1 != k_diff_params

    k_diff_name = signal_cache_key("INFY", "sma", {"length": 14, "scalar": 100}, "snap1")
    assert k1 != k_diff_name


def test_ensure_discovered_wires_up_filters_module() -> None:
    """Sanity check for the one-line registry.py edit: filters.py must be
    imported by ensure_discovered() so its @register_filter signals land."""
    ensure_discovered()
    assert get_filter("index_above_ma").name == "index_above_ma"
    assert get_filter("min_price").name == "min_price"


def test_template_file_is_skipped_by_custom_discovery() -> None:
    """`_template.py` starts with an underscore, so the `my_indicator`
    signal defined inside it must never auto-register."""
    ensure_discovered()
    names = {d.name for d in list_signals()}
    assert "my_indicator" not in names


def test_custom_plugin_discovery_via_extended_package_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercises the real discovery mechanism (pkgutil.iter_modules +
    importlib.import_module over signals/custom/*.py) without writing into
    the source tree: extend the custom package's __path__ with a tmp
    directory containing a real plugin module, force re-discovery, and
    assert the plugin's signal is registered."""
    import tradingos.strategies.signals.custom as custom_pkg

    plugin_code = (
        "from tradingos.strategies.registry import register_signal\n\n"
        '@register_signal("test_registry_dynamic_plugin", tier="custom")\n'
        "def dynamic_plugin_signal(df, **params):\n"
        "    return df['close']\n"
    )
    plugin_dir = tmp_path
    (plugin_dir / "test_registry_dynamic_plugin_mod.py").write_text(plugin_code)

    monkeypatch.setattr(custom_pkg, "__path__", [*custom_pkg.__path__, str(plugin_dir)])
    monkeypatch.setattr(registry, "_DISCOVERED", False)

    registry.ensure_discovered()

    assert "test_registry_dynamic_plugin" in {d.name for d in registry.list_signals()}

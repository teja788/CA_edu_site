"""CLI: `platform backtest run STRATEGY.yaml`.

Builds a small BarStore in tmp_path (as tests/data/test_store.py does), points
Settings at it, and drives the command with typer's CliRunner on an inline
strategy YAML. The event engine is used for the main assertions (fast, no numba);
one vectorized invocation checks the wiring end-to-end.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import polars as pl
import pytest
from fixtures.synthetic import synthetic_daily
from typer.testing import CliRunner

from tradingos.cli import main as cli_main
from tradingos.config.settings import Settings
from tradingos.core.models import Timeframe
from tradingos.data.store import BarStore
from tradingos.strategies.registry import register_signal

runner = CliRunner()


@register_signal("test_cli_mom", tier="custom", window=20)
def _cli_mom(df: pd.DataFrame, **params: object) -> pd.Series:
    return df["close"].pct_change(int(params["window"]))


def _seed_store(store: BarStore, symbols: list[str]) -> None:
    for sym in symbols:
        pdf = synthetic_daily(sym, start=date(2021, 1, 1), end=date(2021, 12, 31))
        pldf = pl.from_pandas(pdf.reset_index(names="ts"))
        store.write_raw(sym, Timeframe.DAY, pldf)


_YAML = """
name: cli_smoke
engine: event
start: 2021-01-01
end: 2021-12-31
capital: 1000000
universe:
  symbols: [AAA, BBB, CCC]
  point_in_time: false
signals:
  - id: mom
    name: test_cli_mom
    params: {window: 20}
score:
  type: single
selection:
  method: top_n
  n: 2
  exit_rank: 2
sizing:
  method: equal_weight
  max_position_pct: 0.6
rebalance:
  frequency: monthly
  trading_day: 1
execution:
  timing: same_close
  slippage_bps: 0.0
  max_participation: 1.0
"""


@pytest.fixture()
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Settings, Path]:
    settings = Settings(
        data_dir=tmp_path / "data", artifacts_dir=tmp_path / "artifacts", _env_file=None
    )
    settings.ensure_dirs()
    # backtest_cmds imports get_settings at call time; the root callback holds its
    # own module-level binding — patch both so the CLI sees the tmp store.
    monkeypatch.setattr("tradingos.config.settings.get_settings", lambda: settings)
    monkeypatch.setattr("tradingos.cli.main.get_settings", lambda: settings)
    store = BarStore(settings)
    _seed_store(store, ["AAA", "BBB", "CCC"])
    yaml_path = tmp_path / "strategy.yaml"
    yaml_path.write_text(_YAML)
    return settings, yaml_path


def test_backtest_run_event_engine_saves_artifacts(env: tuple[Settings, Path]) -> None:
    settings, yaml_path = env
    result = runner.invoke(cli_main.app, ["backtest", "run", str(yaml_path)])

    assert result.exit_code == 0, result.output
    assert "final equity" in result.output
    assert "cli_smoke" in result.output
    assert "event engine" in result.output

    # default artifacts dir: <artifacts>/runs/<name>-<hash>
    runs = settings.artifacts_dir / "runs"
    out_dirs = list(runs.iterdir())
    assert len(out_dirs) == 1
    out = out_dirs[0]
    assert (out / "meta.json").exists()
    assert (out / "equity.parquet").exists()
    assert (out / "trades.json").exists()


def test_backtest_run_out_override_and_vectorized_engine(env: tuple[Settings, Path]) -> None:
    settings, yaml_path = env
    out = settings.artifacts_dir / "custom_out"
    result = runner.invoke(
        cli_main.app,
        ["backtest", "run", str(yaml_path), "--engine", "vectorized", "--out", str(out)],
    )
    assert result.exit_code == 0, result.output
    assert "vectorized engine" in result.output
    # the fast engine's mandatory disclaimer must surface in the summary
    assert "validated on the event engine" in result.output
    assert (out / "meta.json").exists()
    assert (out / "equity.parquet").exists()
    assert (out / "trades.json").exists()


def test_backtest_run_uses_pit_resolver_and_warns_without_membership_data(
    env: tuple[Settings, Path],
) -> None:
    """A direct `backtest run` goes through the SAME point-in-time universe
    resolver as the experiments paths (hard rule 4): a point-in-time universe
    with no membership table must surface a LOUD survivorship warning in the
    run summary, not silently fall back."""
    settings, _ = env
    # Point-in-time universe, no explicit symbols: the resolver must consult the
    # (absent) membership table and warn.
    pit_yaml = _YAML.replace(
        "universe:\n  symbols: [AAA, BBB, CCC]\n  point_in_time: false",
        "universe:\n  index: NIFTY500\n  point_in_time: true",
    )
    assert "point_in_time: true" in pit_yaml  # guard against a silent no-op replace
    yaml_path = settings.artifacts_dir / "pit_strategy.yaml"
    yaml_path.write_text(pit_yaml)

    result = runner.invoke(cli_main.app, ["backtest", "run", str(yaml_path)])

    assert result.exit_code == 0, result.output
    assert "SURVIVORSHIP BIAS" in result.output
    assert "no point-in-time membership data" in result.output


def test_missing_yaml_exits_nonzero_without_stacktrace(env: tuple[Settings, Path]) -> None:
    _settings, _yaml = env
    result = runner.invoke(cli_main.app, ["backtest", "run", "does_not_exist.yaml"])
    assert result.exit_code != 0
    assert "error:" in result.output
    assert "Traceback" not in result.output


def test_no_data_for_symbols_exits_nonzero(env: tuple[Settings, Path]) -> None:
    _settings, yaml_path = env
    result = runner.invoke(
        cli_main.app, ["backtest", "run", str(yaml_path), "--symbols", "GHOST,PHANTOM"]
    )
    assert result.exit_code != 0
    assert "error:" in result.output
    assert "no day data" in result.output

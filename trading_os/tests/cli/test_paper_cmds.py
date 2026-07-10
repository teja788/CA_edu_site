"""CLI: `platform paper run|report|status`.

Builds a small BarStore in tmp_path (as tests/cli/test_backtest_cmd.py does)
and points Settings at it, then drives the paper sub-app with typer's
CliRunner. Never calls a live API: `run --schedule` is only exercised on the
"missing Kite credentials" failure path.
"""

from __future__ import annotations

from datetime import date, datetime, time
from pathlib import Path

import pandas as pd
import polars as pl
import pytest
from typer.testing import CliRunner

from tradingos.cli import main as cli_main
from tradingos.config.settings import Settings
from tradingos.core.models import Fill, Product, Side, Timeframe
from tradingos.core.timeutils import MARKET_CLOSE, now_ist
from tradingos.data.store import BarStore
from tradingos.paper.ledgerdb import PaperStore
from tradingos.strategies.registry import register_signal

runner = CliRunner()

_STRATEGY_NAME = "paper_cli_smoke"


@register_signal("paper_cli_close")
def _cli_close_signal(df: pd.DataFrame, **params: object) -> pd.Series:
    return df["close"]


def _yaml_for(name: str, capital: int) -> str:
    return f"""
name: {name}
capital: {capital}
universe:
  symbols: [AAA, BBB, CCC]
  point_in_time: false
signals:
  - id: px
    name: paper_cli_close
score:
  type: single
selection:
  method: top_n
  n: 2
  exit_rank: 2
sizing:
  method: equal_weight
  max_position_pct: 0.6
"""


_YAML = _yaml_for(_STRATEGY_NAME, 100_000)


def _seed_bar(store: BarStore, symbol: str, day: date, close: float) -> None:
    df = pl.DataFrame(
        {
            "ts": [datetime.combine(day, time(0, 0))],
            "open": [close],
            "high": [close],
            "low": [close],
            "close": [close],
            "volume": [100_000],
        }
    )
    store.write_raw(symbol, Timeframe.DAY, df)


@pytest.fixture()
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Settings, Path]:
    settings = Settings(
        data_dir=tmp_path / "data", artifacts_dir=tmp_path / "artifacts", _env_file=None
    )
    settings.ensure_dirs()
    # paper_cmds imports get_settings at call time; the root callback holds its
    # own module-level binding -- patch both so the CLI sees the tmp store.
    monkeypatch.setattr("tradingos.config.settings.get_settings", lambda: settings)
    monkeypatch.setattr("tradingos.cli.main.get_settings", lambda: settings)
    yaml_path = tmp_path / "strategy.yaml"
    yaml_path.write_text(_YAML)
    return settings, yaml_path


# ---------------------------------------------------------------------------
# paper run --once
# ---------------------------------------------------------------------------


def test_paper_run_once_end_to_end(env: tuple[Settings, Path]) -> None:
    settings, yaml_path = env
    bar_store = BarStore(settings)
    today = now_ist().date()  # --once always uses "today"; seed bars for it
    _seed_bar(bar_store, "AAA", today, 100.0)
    _seed_bar(bar_store, "BBB", today, 200.0)
    _seed_bar(bar_store, "CCC", today, 300.0)

    result = runner.invoke(
        cli_main.app, ["paper", "run", str(yaml_path), "--capital", "100000"]
    )

    assert result.exit_code == 0, result.output
    assert "EOD report" in result.output

    report_path = settings.artifacts_dir / "paper" / _STRATEGY_NAME / f"eod-{today.isoformat()}.html"
    assert report_path.exists()
    assert str(report_path) in result.output

    # the rebalance also queued delta orders for the next trading day
    store = PaperStore(settings.paper_db_path, _STRATEGY_NAME)
    assert store.capital() == pytest.approx(100_000.0)


def test_paper_run_once_missing_yaml_exits_nonzero(env: tuple[Settings, Path]) -> None:
    _settings, _yaml_path = env
    result = runner.invoke(cli_main.app, ["paper", "run", "does_not_exist.yaml"])
    assert result.exit_code != 0
    assert "error:" in result.output
    assert "Traceback" not in result.output


# ---------------------------------------------------------------------------
# paper run: capital precedence at session creation
# ---------------------------------------------------------------------------


def test_paper_run_once_defaults_capital_to_yaml_value(env: tuple[Settings, Path]) -> None:
    """No --capital given on a fresh store: the session is created with the
    strategy YAML's own (non-default) capital, not a CLI-level constant."""
    settings, yaml_path = env
    name = "paper_cli_cap_yaml"
    strat = yaml_path.parent / "strategy_cap_yaml.yaml"
    strat.write_text(_yaml_for(name, 500_000))

    result = runner.invoke(cli_main.app, ["paper", "run", str(strat)])

    assert result.exit_code == 0, result.output
    store = PaperStore(settings.paper_db_path, name)
    assert store.capital() == pytest.approx(500_000.0)


def test_paper_run_once_explicit_capital_wins_over_yaml(env: tuple[Settings, Path]) -> None:
    """--capital on a fresh store beats the YAML's declared capital."""
    settings, yaml_path = env
    name = "paper_cli_cap_flag"
    strat = yaml_path.parent / "strategy_cap_flag.yaml"
    strat.write_text(_yaml_for(name, 500_000))

    result = runner.invoke(
        cli_main.app, ["paper", "run", str(strat), "--capital", "750000"]
    )

    assert result.exit_code == 0, result.output
    store = PaperStore(settings.paper_db_path, name)
    assert store.capital() == pytest.approx(750_000.0)


# ---------------------------------------------------------------------------
# paper run --schedule (missing credentials only -- never touches the network)
# ---------------------------------------------------------------------------


def test_paper_run_schedule_without_kite_credentials_fails(env: tuple[Settings, Path]) -> None:
    settings, yaml_path = env
    assert settings.kite_api_key is None  # sanity: no credentials configured

    result = runner.invoke(cli_main.app, ["paper", "run", str(yaml_path), "--schedule"])

    assert result.exit_code != 0
    assert "error:" in result.output
    assert "TOS_KITE_API_KEY" in result.output


# ---------------------------------------------------------------------------
# paper status
# ---------------------------------------------------------------------------


def test_paper_status_prints_cash_equity_and_holdings(env: tuple[Settings, Path]) -> None:
    settings, yaml_path = env
    store = PaperStore(settings.paper_db_path, _STRATEGY_NAME)
    store.ensure_run(100_000.0)
    store.record_fill(
        Fill(
            client_order_id="seed",
            symbol="AAA",
            side=Side.BUY,
            qty=10,
            price=100.0,
            ts=datetime(2024, 2, 6, 9, 20),
            charges=0.0,
            product=Product.CNC,
        )
    )

    result = runner.invoke(cli_main.app, ["paper", "status", str(yaml_path)])

    assert result.exit_code == 0, result.output
    assert "cash" in result.output.lower()
    assert "equity" in result.output.lower()
    assert "AAA" in result.output
    assert "fills today" in result.output.lower()


def test_paper_status_no_holdings_says_none(env: tuple[Settings, Path]) -> None:
    settings, yaml_path = env
    store = PaperStore(settings.paper_db_path, _STRATEGY_NAME)
    store.ensure_run(100_000.0)

    result = runner.invoke(cli_main.app, ["paper", "status", str(yaml_path)])

    assert result.exit_code == 0, result.output
    assert "none" in result.output.lower()


# ---------------------------------------------------------------------------
# paper report
# ---------------------------------------------------------------------------


def test_paper_report_writes_report_for_explicit_date(env: tuple[Settings, Path]) -> None:
    settings, yaml_path = env
    store = PaperStore(settings.paper_db_path, _STRATEGY_NAME)
    store.ensure_run(100_000.0)
    day = date(2024, 2, 8)
    store.snapshot_equity(datetime.combine(day, MARKET_CLOSE), 100_000.0, cash=100_000.0)

    result = runner.invoke(
        cli_main.app, ["paper", "report", str(yaml_path), "--date", day.isoformat()]
    )

    assert result.exit_code == 0, result.output
    report_path = settings.artifacts_dir / "paper" / _STRATEGY_NAME / f"eod-{day.isoformat()}.html"
    assert report_path.exists()
    assert str(report_path) in result.output


def test_paper_report_invalid_date_exits_nonzero(env: tuple[Settings, Path]) -> None:
    _settings, yaml_path = env
    result = runner.invoke(cli_main.app, ["paper", "report", str(yaml_path), "--date", "not-a-date"])
    assert result.exit_code != 0
    assert "error:" in result.output


def test_paper_report_no_snapshots_exits_nonzero(env: tuple[Settings, Path]) -> None:
    _settings, yaml_path = env
    result = runner.invoke(cli_main.app, ["paper", "report", str(yaml_path)])
    assert result.exit_code != 0
    assert "error:" in result.output

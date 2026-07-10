"""CLI: `platform live run|status|reconcile|killswitch`.

Builds a small BarStore in tmp_path and points Settings at it (mirrors
``tests/cli/test_paper_cmds.py``), then drives the live sub-app with typer's
``CliRunner``. Never touches the network: the broker-construction seam
(``live_cmds._build_broker``) is monkeypatched to inject a FakeKite-backed
``ZerodhaLiveBroker`` instead of a real Kite login, reusing the ``FakeKite`` /
``make_broker`` test seam from ``tests/live/test_broker.py``. The one
exception is the kill-switch "no credentials" path, which deliberately does
NOT monkeypatch the seam -- it exercises the real ``AuthError`` a missing
cached Kite token produces, still without any network call.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path

import pandas as pd
import polars as pl
import pytest
from live.test_broker import FakeKite, make_broker  # noqa: E402 -- test seam reuse
from typer.testing import CliRunner

from tradingos.cli import main as cli_main
from tradingos.config.settings import Settings
from tradingos.core.models import Order, OrderStatus, OrderType, Product, Side, Timeframe
from tradingos.core.timeutils import now_ist
from tradingos.data.store import BarStore
from tradingos.paper.ledgerdb import PaperStore
from tradingos.strategies.registry import register_signal

cli_runner = CliRunner()

_STRATEGY_NAME = "live_cli_smoke"


@register_signal("live_cli_close")
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
    name: live_cli_close
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
    # live_cmds imports get_settings at call time; the root callback holds its
    # own module-level binding -- patch both so the CLI sees the tmp store.
    monkeypatch.setattr("tradingos.config.settings.get_settings", lambda: settings)
    monkeypatch.setattr("tradingos.cli.main.get_settings", lambda: settings)
    yaml_path = tmp_path / "strategy.yaml"
    yaml_path.write_text(_YAML)
    return settings, yaml_path


def _install_fake_broker(monkeypatch: pytest.MonkeyPatch, kite: FakeKite) -> list[bool]:
    """Replace ``live_cmds._build_broker`` with one that injects a FakeKite
    -backed ZerodhaLiveBroker instead of a real Kite login. Returns a list the
    dry_run flag each call was made with is appended to."""
    dry_run_flags: list[bool] = []

    def _build(settings: object, config: object, store: object, calendar: object, *, dry_run: bool):
        dry_run_flags.append(dry_run)
        return make_broker(settings, store, kite, dry_run=dry_run)

    monkeypatch.setattr("tradingos.cli.live_cmds._build_broker", _build)
    return dry_run_flags


@dataclass
class _FakeMismatch:
    """Stand-in for tradingos.live.reconcile.Mismatch matching its documented
    contract (kind/client_order_id/symbol/detail) -- decouples this CLI test
    from that module's exact shape, mirroring the runner tests' seam."""

    kind: str
    client_order_id: str | None
    symbol: str | None
    detail: str


# ---------------------------------------------------------------------------
# live run --once
# ---------------------------------------------------------------------------


def test_live_run_once_dry_run_prints_intended_orders_and_dry_run_line(
    env: tuple[Settings, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    settings, yaml_path = env
    bar_store = BarStore(settings)
    today = now_ist().date()
    _seed_bar(bar_store, "AAA", today, 100.0)
    _seed_bar(bar_store, "BBB", today, 200.0)
    _seed_bar(bar_store, "CCC", today, 300.0)

    # Pre-seed a planned order for today's open (as a prior session-close
    # would have) so on_session_open actually places something in dry-run.
    store = PaperStore(settings.live_db_path, _STRATEGY_NAME)
    store.save_order(
        Order(
            client_order_id="pre-a",
            symbol="AAA",
            side=Side.BUY,
            qty=10,
            order_type=OrderType.MARKET,
            product=Product.CNC,
            tag="rebalance",
        ),
        planned_for=today,
    )

    kite = FakeKite(ltp_price=100.0)
    dry_run_flags = _install_fake_broker(monkeypatch, kite)

    result = cli_runner.invoke(cli_main.app, ["live", "run", str(yaml_path)])

    assert result.exit_code == 0, result.output
    assert dry_run_flags == [True]  # --dry-run is the default
    assert "session open: placed 1 order(s)" in result.output
    assert "pre-a" in result.output and "AAA" in result.output
    assert "intended broker calls (1):" in result.output
    assert "AAA" in result.output and "BUY" in result.output and "MARKET" in result.output
    assert "session close: queued 2 order(s) for next open" in result.output  # BBB + CCC
    assert "DRY RUN -- nothing was sent to the broker." in result.output
    assert kite.place_calls == []  # dry-run never calls the mutating API


def test_live_run_once_missing_yaml_exits_nonzero(env: tuple[Settings, Path]) -> None:
    _settings, _yaml_path = env
    result = cli_runner.invoke(cli_main.app, ["live", "run", "does_not_exist.yaml"])
    assert result.exit_code != 0
    assert "error:" in result.output
    assert "Traceback" not in result.output


def test_live_run_once_live_flag_prints_loud_warning_and_sends_no_dry_run_line(
    env: tuple[Settings, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    settings, yaml_path = env
    bar_store = BarStore(settings)
    today = now_ist().date()
    _seed_bar(bar_store, "AAA", today, 100.0)
    _seed_bar(bar_store, "BBB", today, 200.0)
    _seed_bar(bar_store, "CCC", today, 300.0)

    kite = FakeKite(ltp_price=100.0)
    dry_run_flags = _install_fake_broker(monkeypatch, kite)

    result = cli_runner.invoke(cli_main.app, ["live", "run", str(yaml_path), "--live"])

    assert result.exit_code == 0, result.output
    assert dry_run_flags == [False]
    assert "LIVE TRADING ENABLED" in result.output
    assert "real orders WILL be sent to Zerodha" in result.output
    assert "DRY RUN" not in result.output


# ---------------------------------------------------------------------------
# live status
# ---------------------------------------------------------------------------


def test_live_status_prints_cash_equity_and_holdings(
    env: tuple[Settings, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    settings, yaml_path = env
    kite = FakeKite(
        holdings_response=[
            {
                "tradingsymbol": "AAA",
                "quantity": 10,
                "t1_quantity": 0,
                "average_price": 100.0,
                "last_price": 110.0,
            }
        ]
    )
    dry_run_flags = _install_fake_broker(monkeypatch, kite)

    result = cli_runner.invoke(cli_main.app, ["live", "status", str(yaml_path)])

    assert result.exit_code == 0, result.output
    assert dry_run_flags == [True]  # status is always read-only
    assert "cash" in result.output.lower()
    assert "equity" in result.output.lower()
    assert "AAA" in result.output
    assert "fills today" in result.output.lower()


# ---------------------------------------------------------------------------
# live reconcile
# ---------------------------------------------------------------------------


def test_live_reconcile_no_mismatches_exits_zero(
    env: tuple[Settings, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    settings, yaml_path = env
    kite = FakeKite()
    _install_fake_broker(monkeypatch, kite)
    monkeypatch.setattr("tradingos.cli.live_cmds._reconcile_once", lambda broker: [])

    result = cli_runner.invoke(cli_main.app, ["live", "reconcile", str(yaml_path)])

    assert result.exit_code == 0, result.output
    assert "no mismatches" in result.output.lower()


def test_live_reconcile_mismatches_exits_one(
    env: tuple[Settings, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    settings, yaml_path = env
    kite = FakeKite()
    _install_fake_broker(monkeypatch, kite)
    mismatch = _FakeMismatch(
        kind="qty_drift", client_order_id="cid-1", symbol="AAA", detail="qty 10 vs kite 5"
    )
    monkeypatch.setattr("tradingos.cli.live_cmds._reconcile_once", lambda broker: [mismatch])

    result = cli_runner.invoke(cli_main.app, ["live", "reconcile", str(yaml_path)])

    assert result.exit_code == 1
    assert "qty_drift" in result.output
    assert "AAA" in result.output
    assert "qty 10 vs kite 5" in result.output


# ---------------------------------------------------------------------------
# live killswitch status|engage|disengage
# ---------------------------------------------------------------------------


def test_killswitch_status_engage_disengage_round_trip(env: tuple[Settings, Path]) -> None:
    settings, _yaml_path = env

    result = cli_runner.invoke(cli_main.app, ["live", "killswitch", "status"])
    assert result.exit_code == 0, result.output
    assert "not engaged" in result.output.lower()

    result = cli_runner.invoke(
        cli_main.app,
        ["live", "killswitch", "engage", "--reason", "test halt", "--no-cancel-open"],
    )
    assert result.exit_code == 0, result.output
    assert "kill switch engaged" in result.output.lower()
    assert "test halt" in result.output
    assert settings.kill_switch_path.exists()

    result = cli_runner.invoke(cli_main.app, ["live", "killswitch", "status"])
    assert result.exit_code == 0, result.output
    assert "engaged" in result.output.lower()
    assert "test halt" in result.output

    result = cli_runner.invoke(cli_main.app, ["live", "killswitch", "disengage"])
    assert result.exit_code == 0, result.output
    assert "disengaged" in result.output.lower()
    assert not settings.kill_switch_path.exists()


def test_killswitch_engage_without_strategy_warns_open_orders_not_touched(
    env: tuple[Settings, Path],
) -> None:
    settings, _yaml_path = env

    result = cli_runner.invoke(cli_main.app, ["live", "killswitch", "engage", "--reason", "halt"])

    assert result.exit_code == 0, result.output
    assert settings.kill_switch_path.exists()  # engaged regardless
    assert "not touched" in result.output.lower()


def test_killswitch_engage_no_cancel_open_flag_skips_cancellation(
    env: tuple[Settings, Path],
) -> None:
    settings, yaml_path = env

    result = cli_runner.invoke(
        cli_main.app,
        [
            "live",
            "killswitch",
            "engage",
            "--reason",
            "halt",
            "--strategy",
            str(yaml_path),
            "--no-cancel-open",
        ],
    )

    assert result.exit_code == 0, result.output
    assert settings.kill_switch_path.exists()
    assert "not touched" in result.output.lower()


def test_killswitch_engage_with_strategy_no_creds_warns_open_orders_not_cancelled(
    env: tuple[Settings, Path],
) -> None:
    """No cached Kite token in this tmp settings dir -> broker construction
    raises AuthError. Engage must still succeed (file written first); the
    cancel-open step must fail with a clear warning, no network touched."""
    settings, yaml_path = env
    assert not settings.token_cache_path.exists()  # sanity: no cached token

    result = cli_runner.invoke(
        cli_main.app,
        ["live", "killswitch", "engage", "--reason", "halt", "--strategy", str(yaml_path)],
    )

    assert result.exit_code == 0, result.output
    assert settings.kill_switch_path.exists()  # engaged FIRST regardless
    assert "not cancelled" in result.output.lower()
    assert "kite" in result.output.lower()


def test_killswitch_engage_with_strategy_cancels_open_orders(
    env: tuple[Settings, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    settings, yaml_path = env
    kite = FakeKite()
    _install_fake_broker(monkeypatch, kite)
    store = PaperStore(settings.live_db_path, _STRATEGY_NAME)
    store.save_order(
        Order(
            client_order_id="open-1",
            symbol="AAA",
            side=Side.BUY,
            qty=5,
            order_type=OrderType.MARKET,
            product=Product.CNC,
            status=OrderStatus.OPEN,
            broker_order_id="KITE-OPEN-1",
            created_at=datetime(2024, 1, 1, 10, 0),
        )
    )

    result = cli_runner.invoke(
        cli_main.app,
        ["live", "killswitch", "engage", "--reason", "halt", "--strategy", str(yaml_path)],
    )

    assert result.exit_code == 0, result.output
    assert settings.kill_switch_path.exists()
    assert "cancelled 1 open order" in result.output.lower()
    assert store.get_order("open-1").status == OrderStatus.CANCELLED

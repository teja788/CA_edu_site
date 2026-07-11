"""CLI: `platform data login|sync|instruments|doctor|import-*|adjust`.

Never calls a live API: KiteAuth's login/kite-client methods and the
sync_symbols / sync_instruments entry points are monkeypatched with fakes
that record args and return canned results; `doctor`/importers/`adjust`
need no Kite auth at all and are driven against a real tmp_path BarStore.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

import polars as pl
import pytest
from fixtures.synthetic import synthetic_daily
from typer.testing import CliRunner

from tradingos.cli import main as cli_main
from tradingos.config.settings import Settings
from tradingos.core.errors import AuthError
from tradingos.core.models import Timeframe
from tradingos.core.timeutils import now_ist
from tradingos.data.calendar import NSECalendar
from tradingos.data.store import BarStore
from tradingos.data.sync import SyncResult

runner = CliRunner()

_FAKE_TOKEN = "supersecrettoken123"


@pytest.fixture()
def _cli_settings(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setattr("tradingos.config.settings.get_settings", lambda: settings)
    return settings


def test_login_interactive_success(
    _cli_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict] = []

    def fake_interactive(self, open_browser: bool = True, timeout: float = 120.0) -> str:
        calls.append({"open_browser": open_browser})
        return _FAKE_TOKEN

    monkeypatch.setattr("tradingos.data.auth.KiteAuth.interactive_login", fake_interactive)

    result = runner.invoke(cli_main.app, ["data", "login"])

    assert result.exit_code == 0, result.output
    assert calls == [{"open_browser": True}]
    assert "access token cached for today" in result.output
    assert _FAKE_TOKEN not in result.output  # the token itself is never printed


def test_login_no_browser_flag_routed(
    _cli_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict] = []

    def fake_interactive(self, open_browser: bool = True, timeout: float = 120.0) -> str:
        calls.append({"open_browser": open_browser})
        return _FAKE_TOKEN

    monkeypatch.setattr("tradingos.data.auth.KiteAuth.interactive_login", fake_interactive)

    result = runner.invoke(cli_main.app, ["data", "login", "--no-browser"])

    assert result.exit_code == 0, result.output
    assert calls == [{"open_browser": False}]


def test_login_totp_flag_uses_totp_login(
    _cli_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    interactive_calls: list[dict] = []
    totp_calls: list[dict] = []

    monkeypatch.setattr(
        "tradingos.data.auth.KiteAuth.interactive_login",
        lambda self, **kw: interactive_calls.append(kw) or _FAKE_TOKEN,
    )
    monkeypatch.setattr(
        "tradingos.data.auth.KiteAuth.totp_login",
        lambda self: totp_calls.append({}) or _FAKE_TOKEN,
    )

    result = runner.invoke(cli_main.app, ["data", "login", "--totp"])

    assert result.exit_code == 0, result.output
    assert totp_calls == [{}]
    assert interactive_calls == []


def test_login_auth_error_is_clean_failure(
    _cli_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_interactive(self, open_browser: bool = True, timeout: float = 120.0) -> str:
        raise AuthError("TOS_KITE_API_KEY is not set")

    monkeypatch.setattr("tradingos.data.auth.KiteAuth.interactive_login", fake_interactive)

    result = runner.invoke(cli_main.app, ["data", "login"])

    assert result.exit_code == 1
    assert "error: TOS_KITE_API_KEY is not set" in result.output
    assert "Traceback" not in result.output


# ---------------------------------------------------------------------------
# data sync
# ---------------------------------------------------------------------------


def _fake_kite_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    """No real Kite login: KiteAuth.kite() just returns a sentinel object."""
    monkeypatch.setattr("tradingos.data.auth.KiteAuth.kite", lambda self: object())


def test_sync_routes_symbols_timeframes_and_start(
    _cli_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict] = []
    canned = [
        SyncResult(
            symbol="AAA",
            timeframe=Timeframe.DAY,
            rows_added=5,
            from_ts=datetime(2024, 1, 1, 9, 15),
            to_ts=datetime(2024, 1, 5, 9, 15),
        ),
        SyncResult(
            symbol="BBB", timeframe=Timeframe.MINUTE, rows_added=0, from_ts=None, to_ts=None
        ),
    ]

    def fake_sync_symbols(kite, settings, symbols, timeframes, *, default_start, **kw):
        calls.append(
            {
                "kite": kite,
                "settings": settings,
                "symbols": symbols,
                "timeframes": timeframes,
                "default_start": default_start,
            }
        )
        return canned

    _fake_kite_ok(monkeypatch)
    monkeypatch.setattr("tradingos.data.sync.sync_symbols", fake_sync_symbols)

    result = runner.invoke(
        cli_main.app,
        [
            "data",
            "sync",
            "AAA",
            "BBB",
            "--timeframe",
            "day",
            "--timeframe",
            "minute",
            "--start",
            "2020-01-01",
        ],
    )

    assert result.exit_code == 0, result.output
    assert len(calls) == 1
    assert calls[0]["symbols"] == ["AAA", "BBB"]
    assert calls[0]["timeframes"] == [Timeframe.DAY, Timeframe.MINUTE]
    assert calls[0]["default_start"] == date(2020, 1, 1)
    assert calls[0]["settings"] is _cli_settings
    assert "AAA" in result.output and "+5 bar(s)" in result.output
    assert "BBB" in result.output and "already up to date" in result.output
    assert "synced 2/2" in result.output


def test_sync_default_timeframe_is_day(
    _cli_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict] = []

    def fake_sync_symbols(kite, settings, symbols, timeframes, *, default_start, **kw):
        calls.append({"timeframes": timeframes})
        return [
            SyncResult(
                symbol="AAA", timeframe=Timeframe.DAY, rows_added=0, from_ts=None, to_ts=None
            )
        ]

    _fake_kite_ok(monkeypatch)
    monkeypatch.setattr("tradingos.data.sync.sync_symbols", fake_sync_symbols)

    result = runner.invoke(cli_main.app, ["data", "sync", "AAA"])

    assert result.exit_code == 0, result.output
    assert calls[0]["timeframes"] == [Timeframe.DAY]


def test_sync_any_failure_exits_nonzero(
    _cli_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    canned = [
        SyncResult(
            symbol="AAA",
            timeframe=Timeframe.DAY,
            rows_added=0,
            from_ts=None,
            to_ts=None,
            error="instrument token not found",
        )
    ]

    _fake_kite_ok(monkeypatch)
    monkeypatch.setattr(
        "tradingos.data.sync.sync_symbols", lambda *a, **kw: canned
    )

    result = runner.invoke(cli_main.app, ["data", "sync", "AAA"])

    assert result.exit_code == 1
    assert "FAILED: instrument token not found" in result.output
    assert "synced 0/1" in result.output


def test_sync_stale_token_fails_cleanly_without_calling_sync(
    _cli_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_kite(self):
        raise AuthError(
            "cached Kite access token is stale (from a previous day); "
            "run `platform data login` to authenticate"
        )

    sync_calls: list[object] = []
    monkeypatch.setattr("tradingos.data.auth.KiteAuth.kite", fake_kite)
    monkeypatch.setattr(
        "tradingos.data.sync.sync_symbols",
        lambda *a, **kw: sync_calls.append(1) or [],
    )

    result = runner.invoke(cli_main.app, ["data", "sync", "AAA"])

    assert result.exit_code == 1
    assert "run `platform data login`" in result.output
    assert sync_calls == []
    assert "Traceback" not in result.output


# ---------------------------------------------------------------------------
# data instruments
# ---------------------------------------------------------------------------


def test_instruments_calls_sync_and_prints_counts(
    _cli_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple] = []

    def fake_sync_instruments(kite, settings):
        calls.append((kite, settings))
        return {"fetched": 10, "added": 3, "updated": 7, "symbol_changes": 1}

    _fake_kite_ok(monkeypatch)
    monkeypatch.setattr("tradingos.data.instruments.sync_instruments", fake_sync_instruments)

    result = runner.invoke(cli_main.app, ["data", "instruments"])

    assert result.exit_code == 0, result.output
    assert len(calls) == 1
    assert calls[0][1] is _cli_settings
    assert "10" in result.output
    assert "3" in result.output
    assert "7" in result.output
    assert "1" in result.output


def test_instruments_auth_error_is_clean_failure(
    _cli_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_kite(self):
        raise AuthError(
            "no cached Kite access token found; run `platform data login` to authenticate"
        )

    monkeypatch.setattr("tradingos.data.auth.KiteAuth.kite", fake_kite)

    result = runner.invoke(cli_main.app, ["data", "instruments"])

    assert result.exit_code == 1
    assert "run `platform data login`" in result.output
    assert "Traceback" not in result.output


# ---------------------------------------------------------------------------
# data doctor
# ---------------------------------------------------------------------------


def _clean_bar_frame(settings: Settings, symbol: str, end: date) -> pl.DataFrame:
    """A synthetic daily bar frame with no data-quality issues, ending on
    `end` -- mirrors tests/data/test_doctor.py::clean_frame but against real
    NSECalendar holidays so the CLI's own DataDoctor/NSECalendar agree with
    what was seeded."""
    cal = NSECalendar(settings)
    start = end - timedelta(days=400)
    holidays: set[date] = set()
    for year in range(start.year, end.year + 1):
        holidays |= cal.holidays(year)
    pdf = synthetic_daily(symbol=symbol, start=start, end=end, seed=11, holidays=holidays)
    pdf = pdf.reset_index().rename(columns={"index": "ts"})
    return pl.from_pandas(pdf[["ts", "open", "high", "low", "close", "volume"]])


def test_doctor_clean_store_exits_zero(_cli_settings: Settings) -> None:
    store = BarStore(_cli_settings)
    today = now_ist().date()
    store.write_raw("CLEANCO", Timeframe.DAY, _clean_bar_frame(_cli_settings, "CLEANCO", today))

    result = runner.invoke(cli_main.app, ["data", "doctor"])

    assert result.exit_code == 0, result.output
    assert "No findings. All checks passed." in result.output


def test_doctor_missing_trading_day_is_error_and_exits_one(_cli_settings: Settings) -> None:
    store = BarStore(_cli_settings)
    today = now_ist().date()
    df = _clean_bar_frame(_cli_settings, "BADCO", today)
    dropped_ts = df["ts"][20]
    corrupted = df.filter(pl.col("ts") != dropped_ts)
    store.write_raw("BADCO", Timeframe.DAY, corrupted)

    result = runner.invoke(cli_main.app, ["data", "doctor"])

    assert result.exit_code == 1
    assert "missing_trading_days" in result.output
    assert "ERROR" in result.output


def test_doctor_symbols_argument_filters_which_symbols_are_checked(
    _cli_settings: Settings,
) -> None:
    store = BarStore(_cli_settings)
    today = now_ist().date()
    store.write_raw("CLEANCO", Timeframe.DAY, _clean_bar_frame(_cli_settings, "CLEANCO", today))
    df = _clean_bar_frame(_cli_settings, "BADCO", today)
    corrupted = df.filter(pl.col("ts") != df["ts"][20])
    store.write_raw("BADCO", Timeframe.DAY, corrupted)

    result = runner.invoke(cli_main.app, ["data", "doctor", "CLEANCO"])

    assert result.exit_code == 0, result.output
    assert "BADCO" not in result.output
    assert "symbols checked: 1" in result.output


# ---------------------------------------------------------------------------
# data import-universe / import-actions / import-dividends
# ---------------------------------------------------------------------------


def test_import_universe_reports_row_count(_cli_settings: Settings, tmp_path: Path) -> None:
    csv_path = tmp_path / "membership.csv"
    csv_path.write_text(
        "index_name,symbol,start_date,end_date\n"
        "NIFTY50,RELIANCE,2015-01-01,\n"
        "NIFTY50,INFY,2015-01-01,2020-06-30\n"
    )

    result = runner.invoke(cli_main.app, ["data", "import-universe", str(csv_path)])

    assert result.exit_code == 0, result.output
    assert "imported 2 row(s)" in result.output


def test_import_universe_missing_file_is_clean_failure(_cli_settings: Settings) -> None:
    result = runner.invoke(cli_main.app, ["data", "import-universe", "does_not_exist.csv"])

    assert result.exit_code == 1
    assert "error:" in result.output
    assert "Traceback" not in result.output


def test_import_actions_reports_row_count(_cli_settings: Settings, tmp_path: Path) -> None:
    csv_path = tmp_path / "actions.csv"
    csv_path.write_text(
        "symbol,ex_date,action_type,ratio_num,ratio_den,new_symbol,note\n"
        "AAA,2020-01-03,split,10,2,,ten-to-two\n"
        "AAA,2021-06-01,bonus,1,1,,\n"
    )

    result = runner.invoke(cli_main.app, ["data", "import-actions", str(csv_path)])

    assert result.exit_code == 0, result.output
    assert "imported 2 row(s)" in result.output


def test_import_actions_missing_file_is_clean_failure(_cli_settings: Settings) -> None:
    result = runner.invoke(cli_main.app, ["data", "import-actions", "does_not_exist.csv"])

    assert result.exit_code == 1
    assert "error:" in result.output
    assert "Traceback" not in result.output


def test_import_actions_parse_error_is_clean_failure(
    _cli_settings: Settings, tmp_path: Path
) -> None:
    csv_path = tmp_path / "bad_actions.csv"
    csv_path.write_text(
        "symbol,ex_date,action_type,ratio_num,ratio_den,new_symbol,note\n"
        "AAA,2020-01-03,merger,,,,\n"
    )

    result = runner.invoke(cli_main.app, ["data", "import-actions", str(csv_path)])

    assert result.exit_code == 1
    assert "error:" in result.output
    assert "unknown action_type" in result.output
    assert "Traceback" not in result.output


def test_import_dividends_reports_row_count(_cli_settings: Settings, tmp_path: Path) -> None:
    csv_path = tmp_path / "dividends.csv"
    csv_path.write_text("symbol,ex_date,amount\nAAA,2020-03-01,5.5\nAAA,2021-03-01,6.0\n")

    result = runner.invoke(cli_main.app, ["data", "import-dividends", str(csv_path)])

    assert result.exit_code == 0, result.output
    assert "imported 2 row(s)" in result.output


def test_import_dividends_missing_file_is_clean_failure(_cli_settings: Settings) -> None:
    result = runner.invoke(cli_main.app, ["data", "import-dividends", "does_not_exist.csv"])

    assert result.exit_code == 1
    assert "error:" in result.output
    assert "Traceback" not in result.output


# ---------------------------------------------------------------------------
# data adjust
# ---------------------------------------------------------------------------


def test_adjust_rebuilds_adjusted_series_from_raw(_cli_settings: Settings) -> None:
    store = BarStore(_cli_settings)
    today = now_ist().date()
    df = _clean_bar_frame(_cli_settings, "AAA", today)
    store.write_raw("AAA", Timeframe.DAY, df)

    result = runner.invoke(cli_main.app, ["data", "adjust", "AAA"])

    assert result.exit_code == 0, result.output
    assert f"{df.height} adjusted bar(s) written" in result.output
    assert "adjusted 1/1 symbol(s)" in result.output
    assert store.has_adjusted("AAA", Timeframe.DAY)


def test_adjust_missing_raw_data_fails_that_symbol_and_exits_nonzero(
    _cli_settings: Settings,
) -> None:
    result = runner.invoke(cli_main.app, ["data", "adjust", "NODATA"])

    assert result.exit_code == 1
    assert "NODATA" in result.output
    assert "FAILED" in result.output
    assert "adjusted 0/1 symbol(s)" in result.output

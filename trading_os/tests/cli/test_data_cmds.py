"""CLI: `platform data login`.

Never calls a live API: KiteAuth's login methods are monkeypatched; only the
CLI wiring (flag routing, success/failure output, exit codes, no token ever
printed) is under test.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from tradingos.cli import main as cli_main
from tradingos.config.settings import Settings
from tradingos.core.errors import AuthError

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

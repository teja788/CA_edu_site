"""TelegramAlerter tests. requests.post is entirely faked -- no network."""

from __future__ import annotations

from datetime import datetime

import pytest
import requests

from tradingos.core import alerts as alerts_module
from tradingos.core.alerts import TelegramAlerter
from tradingos.core.models import Fill, Order, Side


class FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


def _order(**overrides) -> Order:
    fields = dict(symbol="INFY", side=Side.BUY, qty=10)
    fields.update(overrides)
    return Order(**fields)


def _fill(**overrides) -> Fill:
    fields = dict(
        client_order_id="abc123",
        symbol="INFY",
        side=Side.BUY,
        qty=10,
        price=1500.5,
        ts=datetime(2024, 1, 15, 10, 0, 0),
        charges=12.34,
    )
    fields.update(overrides)
    return Fill(**fields)


class TestDisabled:
    def test_disabled_when_token_missing(self) -> None:
        alerter = TelegramAlerter(None, "chat123")
        assert alerter.enabled is False

    def test_disabled_when_chat_id_missing(self) -> None:
        alerter = TelegramAlerter("token123", None)
        assert alerter.enabled is False

    def test_disabled_when_both_missing(self) -> None:
        alerter = TelegramAlerter(None, None)
        assert alerter.enabled is False

    def test_enabled_when_both_set(self) -> None:
        alerter = TelegramAlerter("token123", "chat123")
        assert alerter.enabled is True

    def test_send_returns_false_when_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls = []
        monkeypatch.setattr(alerts_module.requests, "post", lambda *a, **kw: calls.append((a, kw)))
        alerter = TelegramAlerter(None, "chat123")
        assert alerter.send("hello") is False
        assert calls == []

    def test_send_returns_false_when_token_missing_no_call(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls = []
        monkeypatch.setattr(alerts_module.requests, "post", lambda *a, **kw: calls.append((a, kw)))
        alerter = TelegramAlerter(None, None)
        assert alerter.send("hello") is False
        assert calls == []


class TestSend:
    def test_success_returns_true_and_correct_payload(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured = {}

        def fake_post(url, json=None, timeout=None):
            captured["url"] = url
            captured["json"] = json
            captured["timeout"] = timeout
            return FakeResponse(200)

        monkeypatch.setattr(alerts_module.requests, "post", fake_post)
        alerter = TelegramAlerter("TOKEN789", "CHAT456", timeout=3.0)
        assert alerter.send("hello world") is True
        assert captured["url"] == "https://api.telegram.org/botTOKEN789/sendMessage"
        assert captured["url"].endswith("/sendMessage")
        assert "TOKEN789" in captured["url"]
        assert captured["json"] == {
            "chat_id": "CHAT456",
            "text": "hello world",
            "parse_mode": "HTML",
        }
        assert captured["timeout"] == 3.0

    def test_non_200_returns_false_no_raise(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(alerts_module.requests, "post", lambda *a, **kw: FakeResponse(500))
        alerter = TelegramAlerter("TOKEN789", "CHAT456")
        assert alerter.send("hello") is False

    def test_network_exception_returns_false_no_raise(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def raise_connection_error(*a, **kw):
            raise requests.exceptions.ConnectionError("boom")

        monkeypatch.setattr(alerts_module.requests, "post", raise_connection_error)
        alerter = TelegramAlerter("TOKEN789", "CHAT456")
        assert alerter.send("hello") is False

    def test_bot_token_never_logged(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        def raise_connection_error(*a, **kw):
            raise requests.exceptions.ConnectionError("boom")

        monkeypatch.setattr(alerts_module.requests, "post", raise_connection_error)
        alerter = TelegramAlerter("SUPERSECRETTOKEN", "CHAT456")
        with caplog.at_level("WARNING"):
            assert alerter.send("hello") is False
        assert "SUPERSECRETTOKEN" not in caplog.text


class TestFormattingHelpers:
    def test_alert_fill(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured = {}
        monkeypatch.setattr(
            alerts_module.requests,
            "post",
            lambda url, json=None, timeout=None: captured.update(json=json) or FakeResponse(200),
        )
        alerter = TelegramAlerter("TOKEN789", "CHAT456")
        fill = _fill(symbol="TCS", qty=5, price=3500.0, side=Side.SELL)
        assert alerter.alert_fill(fill) is True
        text = captured["json"]["text"]
        assert text
        assert "TCS" in text
        assert "5" in text
        assert "SELL" in text

    def test_alert_rejection(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured = {}
        monkeypatch.setattr(
            alerts_module.requests,
            "post",
            lambda url, json=None, timeout=None: captured.update(json=json) or FakeResponse(200),
        )
        alerter = TelegramAlerter("TOKEN789", "CHAT456")
        order = _order(symbol="RELIANCE", qty=7)
        assert alerter.alert_rejection(order, "kill switch") is True
        text = captured["json"]["text"]
        assert text
        assert "RELIANCE" in text
        assert "7" in text
        assert "kill switch" in text

    def test_alert_risk(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured = {}
        monkeypatch.setattr(
            alerts_module.requests,
            "post",
            lambda url, json=None, timeout=None: captured.update(json=json) or FakeResponse(200),
        )
        alerter = TelegramAlerter("TOKEN789", "CHAT456")
        assert alerter.alert_risk("daily loss limit breached") is True
        text = captured["json"]["text"]
        assert text
        assert "daily loss limit breached" in text

    def test_alert_token_expiry_default_message(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured = {}
        monkeypatch.setattr(
            alerts_module.requests,
            "post",
            lambda url, json=None, timeout=None: captured.update(json=json) or FakeResponse(200),
        )
        alerter = TelegramAlerter("TOKEN789", "CHAT456")
        assert alerter.alert_token_expiry() is True
        text = captured["json"]["text"]
        assert text
        assert "token" in text.lower()

    def test_formatting_helpers_return_send_result_when_disabled(self) -> None:
        alerter = TelegramAlerter(None, None)
        fill = _fill()
        order = _order()
        assert alerter.alert_fill(fill) is False
        assert alerter.alert_rejection(order, "reason") is False
        assert alerter.alert_risk("msg") is False
        assert alerter.alert_token_expiry() is False


class TestFromSettings:
    def test_from_settings_disabled_by_default(self, settings) -> None:
        alerter = TelegramAlerter.from_settings(settings)
        assert alerter.enabled is False

    def test_from_settings_enabled_when_configured(self, settings) -> None:
        settings.telegram_bot_token = "TOKEN789"
        settings.telegram_chat_id = "CHAT456"
        alerter = TelegramAlerter.from_settings(settings)
        assert alerter.enabled is True

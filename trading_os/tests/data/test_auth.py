"""Auth flow tests. kiteconnect and requests are entirely faked -- no network."""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from tradingos.config.settings import Settings
from tradingos.core.errors import AuthError
from tradingos.core.timeutils import now_ist
from tradingos.data import auth as auth_module
from tradingos.data.auth import KiteAuth, _extract_request_token


class FakeKiteConnect:
    """Stand-in for kiteconnect.KiteConnect used across all auth tests."""

    last_generate_session_args: tuple | None = None

    def __init__(self, api_key: str, access_token: str | None = None) -> None:
        self.api_key = api_key
        self.access_token = access_token

    def generate_session(self, request_token: str, api_secret: str) -> dict:
        FakeKiteConnect.last_generate_session_args = (request_token, api_secret)
        return {
            "access_token": f"tok-for-{request_token}",
            "user_id": "AB1234",
            "login_time": "2026-07-09 09:00:00",
        }


@pytest.fixture(autouse=True)
def fake_kiteconnect(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth_module, "KiteConnect", FakeKiteConnect)


@pytest.fixture()
def creds(settings: Settings) -> Settings:
    settings.kite_api_key = "test-api-key"
    settings.kite_api_secret = "test-api-secret"
    return settings


def test_extract_request_token_from_full_url() -> None:
    url = "https://127.0.0.1:8721/?request_token=abc123&action=login&status=success"
    assert _extract_request_token(url) == "abc123"


def test_extract_request_token_missing_returns_none() -> None:
    assert _extract_request_token("https://127.0.0.1:8721/?status=success") is None
    assert _extract_request_token("") is None


class TestLoginUrl:
    def test_raises_when_api_key_missing(self, settings: Settings) -> None:
        ka = KiteAuth(settings)
        with pytest.raises(AuthError):
            ka.login_url()

    def test_builds_expected_url(self, creds: Settings) -> None:
        ka = KiteAuth(creds)
        assert ka.login_url() == "https://kite.zerodha.com/connect/login?api_key=test-api-key&v=3"


class TestTokenCache:
    def test_get_access_token_raises_when_no_cache(self, settings: Settings) -> None:
        ka = KiteAuth(settings)
        with pytest.raises(AuthError, match="platform data login"):
            ka.get_access_token()

    def test_get_access_token_returns_cached_token_for_today(self, settings: Settings) -> None:
        ka = KiteAuth(settings)
        today = now_ist().date().isoformat()
        settings.token_cache_path.parent.mkdir(parents=True, exist_ok=True)
        settings.token_cache_path.write_text(
            json.dumps({"access_token": "cached-tok", "date": today})
        )
        assert ka.get_access_token() == "cached-tok"

    def test_get_access_token_raises_when_cache_is_from_a_previous_day(
        self, settings: Settings
    ) -> None:
        ka = KiteAuth(settings)
        yesterday = (now_ist() - timedelta(days=1)).date().isoformat()
        settings.token_cache_path.parent.mkdir(parents=True, exist_ok=True)
        settings.token_cache_path.write_text(
            json.dumps({"access_token": "stale-tok", "date": yesterday})
        )
        with pytest.raises(AuthError, match="stale"):
            ka.get_access_token()

    def test_get_access_token_raises_on_malformed_cache(self, settings: Settings) -> None:
        ka = KiteAuth(settings)
        settings.token_cache_path.parent.mkdir(parents=True, exist_ok=True)
        settings.token_cache_path.write_text("not json")
        with pytest.raises(AuthError):
            ka.get_access_token()

    def test_clear_token_removes_cache(self, settings: Settings) -> None:
        ka = KiteAuth(settings)
        today = now_ist().date().isoformat()
        settings.token_cache_path.parent.mkdir(parents=True, exist_ok=True)
        settings.token_cache_path.write_text(
            json.dumps({"access_token": "cached-tok", "date": today})
        )
        ka.clear_token()
        assert not settings.token_cache_path.exists()
        with pytest.raises(AuthError):
            ka.get_access_token()

    def test_clear_token_is_a_noop_when_no_cache(self, settings: Settings) -> None:
        KiteAuth(settings).clear_token()  # must not raise


class TestExchangeRequestToken:
    def test_exchanges_and_caches(self, creds: Settings) -> None:
        ka = KiteAuth(creds)
        token = ka.exchange_request_token("req-tok-1")
        assert token == "tok-for-req-tok-1"
        assert FakeKiteConnect.last_generate_session_args == ("req-tok-1", "test-api-secret")

        cached = json.loads(creds.token_cache_path.read_text())
        assert cached["access_token"] == "tok-for-req-tok-1"
        assert cached["date"] == now_ist().date().isoformat()

        # And it's now usable via get_access_token / kite().
        assert ka.get_access_token() == "tok-for-req-tok-1"
        client = ka.kite()
        assert isinstance(client, FakeKiteConnect)
        assert client.access_token == "tok-for-req-tok-1"

    def test_raises_without_secret(self, settings: Settings) -> None:
        settings.kite_api_key = "only-key"
        ka = KiteAuth(settings)
        with pytest.raises(AuthError):
            ka.exchange_request_token("req-tok")

    def test_wraps_kiteconnect_failure(self, creds: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
        class BoomKiteConnect(FakeKiteConnect):
            def generate_session(self, request_token: str, api_secret: str) -> dict:
                raise RuntimeError("boom")

        monkeypatch.setattr(auth_module, "KiteConnect", BoomKiteConnect)
        ka = KiteAuth(creds)
        with pytest.raises(AuthError, match="boom"):
            ka.exchange_request_token("req-tok")

    def test_raises_when_no_access_token_in_response(
        self, creds: Settings, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class EmptyKiteConnect(FakeKiteConnect):
            def generate_session(self, request_token: str, api_secret: str) -> dict:
                return {"user_id": "AB1234"}

        monkeypatch.setattr(auth_module, "KiteConnect", EmptyKiteConnect)
        ka = KiteAuth(creds)
        with pytest.raises(AuthError):
            ka.exchange_request_token("req-tok")


class TestKite:
    def test_raises_without_api_key(self, settings: Settings) -> None:
        with pytest.raises(AuthError):
            KiteAuth(settings).kite()

    def test_raises_without_cached_token(self, creds: Settings) -> None:
        with pytest.raises(AuthError):
            KiteAuth(creds).kite()


class TestInteractiveLogin:
    def test_uses_server_captured_token(
        self, creds: Settings, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            auth_module, "_capture_request_token_via_server", lambda port, timeout: "srv-tok"
        )
        monkeypatch.setattr(auth_module.webbrowser, "open", lambda url: True)
        ka = KiteAuth(creds)
        token = ka.interactive_login(open_browser=True, timeout=1.0)
        assert token == "tok-for-srv-tok"

    def test_falls_back_to_manual_paste_when_server_capture_fails(
        self, creds: Settings, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            auth_module, "_capture_request_token_via_server", lambda port, timeout: None
        )
        monkeypatch.setattr(auth_module.webbrowser, "open", lambda url: True)
        pasted_url = "https://127.0.0.1:8721/?request_token=pasted-tok&status=success"
        monkeypatch.setattr("builtins.input", lambda prompt="": pasted_url)
        ka = KiteAuth(creds)
        token = ka.interactive_login(open_browser=False, timeout=0.1)
        assert token == "tok-for-pasted-tok"

    def test_raises_when_nothing_captured_or_pasted(
        self, creds: Settings, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            auth_module, "_capture_request_token_via_server", lambda port, timeout: None
        )
        monkeypatch.setattr(auth_module.webbrowser, "open", lambda url: True)
        monkeypatch.setattr("builtins.input", lambda prompt="": "")
        ka = KiteAuth(creds)
        with pytest.raises(AuthError):
            ka.interactive_login(open_browser=False, timeout=0.1)


class FakeResponse:
    def __init__(self, json_data: dict | None = None, headers: dict | None = None, status_code: int = 200) -> None:
        self._json_data = json_data or {}
        self.headers = headers or {}
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def json(self) -> dict:
        return self._json_data


class FakeSession:
    def __init__(self, login_resp: FakeResponse, twofa_resp: FakeResponse, redirect_resp: FakeResponse) -> None:
        self.login_resp = login_resp
        self.twofa_resp = twofa_resp
        self.redirect_resp = redirect_resp
        self.calls: list[tuple] = []

    def post(self, url: str, data: dict | None = None, timeout: float | None = None) -> FakeResponse:
        self.calls.append(("POST", url, data))
        if url.endswith("/login"):
            return self.login_resp
        if url.endswith("/twofa"):
            return self.twofa_resp
        raise AssertionError(f"unexpected POST {url}")

    def get(self, url: str, timeout: float | None = None, allow_redirects: bool | None = None) -> FakeResponse:
        self.calls.append(("GET", url))
        return self.redirect_resp


@pytest.fixture()
def totp_creds(creds: Settings) -> Settings:
    creds.kite_user_id = "AB1234"
    creds.kite_password = "secret-pass"
    creds.kite_totp_secret = "JBSWY3DPEHPK3PXP"
    return creds


class TestTotpLogin:
    def test_missing_credentials_raises(self, creds: Settings) -> None:
        with pytest.raises(AuthError):
            KiteAuth(creds).totp_login()

    def test_full_flow_success(self, totp_creds: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_session = FakeSession(
            login_resp=FakeResponse(json_data={"data": {"request_id": "req-id-1"}}),
            twofa_resp=FakeResponse(json_data={"data": {}}),
            redirect_resp=FakeResponse(
                status_code=302,
                headers={
                    "Location": "https://kite.zerodha.com/connect/finish?request_token=totp-tok&status=success"
                },
            ),
        )
        monkeypatch.setattr(auth_module.requests, "Session", lambda: fake_session)
        ka = KiteAuth(totp_creds)
        token = ka.totp_login()
        assert token == "tok-for-totp-tok"
        assert any(call[0] == "POST" and call[1].endswith("/login") for call in fake_session.calls)
        assert any(call[0] == "POST" and call[1].endswith("/twofa") for call in fake_session.calls)

    def test_wraps_http_failure(self, totp_creds: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_session = FakeSession(
            login_resp=FakeResponse(status_code=401),
            twofa_resp=FakeResponse(),
            redirect_resp=FakeResponse(),
        )
        monkeypatch.setattr(auth_module.requests, "Session", lambda: fake_session)
        ka = KiteAuth(totp_creds)
        with pytest.raises(AuthError):
            ka.totp_login()

    def test_wraps_missing_request_token_in_redirect(
        self, totp_creds: Settings, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_session = FakeSession(
            login_resp=FakeResponse(json_data={"data": {"request_id": "req-id-1"}}),
            twofa_resp=FakeResponse(json_data={"data": {}}),
            redirect_resp=FakeResponse(status_code=302, headers={}),
        )
        monkeypatch.setattr(auth_module.requests, "Session", lambda: fake_session)
        ka = KiteAuth(totp_creds)
        with pytest.raises(AuthError):
            ka.totp_login()

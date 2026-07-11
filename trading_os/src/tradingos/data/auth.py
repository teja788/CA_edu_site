"""Kite Connect authentication: login-url generation, request-token exchange,
daily access-token caching, and two login flows (interactive browser redirect,
and an optional best-effort TOTP-automated flow).

Kite access tokens expire at the start of each trading day, so the cache is
keyed by IST calendar date -- a cached token from a previous date is stale and
`get_access_token` raises `AuthError` rather than silently returning it.
"""

from __future__ import annotations

import json
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pyotp
import requests
from kiteconnect import KiteConnect

from tradingos.config.settings import Settings
from tradingos.core.errors import AuthError
from tradingos.core.logging import get_logger
from tradingos.core.timeutils import now_ist

logger = get_logger(__name__)

_LOGIN_URI = "https://kite.zerodha.com/connect/login"
_KITE_LOGIN_API = "https://kite.zerodha.com/api/login"
_KITE_TWOFA_API = "https://kite.zerodha.com/api/twofa"
_KITE_VERSION = "3"


def _extract_request_token(url_or_query: str) -> str | None:
    """Pull `request_token` out of a redirect URL (or a bare query string)."""
    if not url_or_query:
        return None
    parsed = urlparse(url_or_query)
    query = parsed.query or url_or_query
    values = parse_qs(query)
    tokens = values.get("request_token")
    return tokens[0] if tokens else None


class _CallbackHandler(BaseHTTPRequestHandler):
    """One-shot HTTP handler that captures `request_token` from the redirect
    query string and shows the user a short confirmation page."""

    def do_GET(self) -> None:  # noqa: N802 -- stdlib-mandated name
        token = _extract_request_token(self.path)
        self.server.captured_token = token  # type: ignore[attr-defined]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        body = (
            "<html><body><p>Login captured. You can close this tab.</p></body></html>"
            if token
            else "<html><body><p>No request_token found in redirect.</p></body></html>"
        )
        self.wfile.write(body.encode())

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        # Silence BaseHTTPRequestHandler's default stderr access logging.
        pass


def _capture_request_token_via_server(port: int, timeout: float) -> str | None:
    """Run a one-shot local HTTP server on 127.0.0.1:port that captures the
    redirect from Kite's login flow. Returns None on timeout or bind failure."""
    server = HTTPServer(("127.0.0.1", port), _CallbackHandler)
    server.timeout = timeout
    server.captured_token = None  # type: ignore[attr-defined]
    try:
        server.handle_request()
    finally:
        server.server_close()
    return server.captured_token  # type: ignore[attr-defined]


class KiteAuth:
    """Manages the Kite Connect login flow and the daily access-token cache."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    # -- login URL -----------------------------------------------------

    def login_url(self) -> str:
        if not self.settings.kite_api_key:
            raise AuthError("TOS_KITE_API_KEY is not set; cannot build a login URL")
        return f"{_LOGIN_URI}?api_key={self.settings.kite_api_key}&v={_KITE_VERSION}"

    # -- token cache -----------------------------------------------------

    def _cache_path(self) -> Path:
        return self.settings.token_cache_path

    def _today_ist(self) -> str:
        return now_ist().date().isoformat()

    def _read_cache(self) -> dict | None:
        path = self._cache_path()
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("token cache at %s is unreadable: %s", path, exc)
            return None

    def _write_cache(self, access_token: str) -> None:
        path = self._cache_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"access_token": access_token, "date": self._today_ist()}))

    def get_access_token(self) -> str:
        """Return today's cached access token, or raise AuthError with an
        actionable message if there is none / it is from a previous day."""
        cached = self._read_cache()
        if cached is None:
            raise AuthError(
                "no cached Kite access token found; run `platform data login` to authenticate"
            )
        token = cached.get("access_token")
        cached_date = cached.get("date")
        if not token or not cached_date:
            raise AuthError(
                "token cache is malformed; run `platform data login` to re-authenticate"
            )
        if cached_date != self._today_ist():
            raise AuthError(
                "cached Kite access token is stale (from a previous day); "
                "run `platform data login` to authenticate"
            )
        return token

    def clear_token(self) -> None:
        path = self._cache_path()
        if path.exists():
            path.unlink()

    # -- kite client -----------------------------------------------------

    def kite(self) -> KiteConnect:
        if not self.settings.kite_api_key:
            raise AuthError("TOS_KITE_API_KEY is not set")
        access_token = self.get_access_token()
        return KiteConnect(api_key=self.settings.kite_api_key, access_token=access_token)

    # -- exchange / login flows -------------------------------------------

    def exchange_request_token(self, request_token: str) -> str:
        if not self.settings.kite_api_key or not self.settings.kite_api_secret:
            raise AuthError("TOS_KITE_API_KEY / TOS_KITE_API_SECRET must be set to log in")
        kite = KiteConnect(api_key=self.settings.kite_api_key)
        try:
            session_data = kite.generate_session(
                request_token, api_secret=self.settings.kite_api_secret
            )
        except Exception as exc:  # kiteconnect raises its own exception types
            raise AuthError(f"failed to exchange request_token for access_token: {exc}") from exc
        access_token = session_data.get("access_token")
        if not access_token:
            raise AuthError("Kite did not return an access_token for this request_token")
        self._write_cache(access_token)
        return access_token

    def interactive_login(self, open_browser: bool = True, timeout: float = 120.0) -> str:
        """Interactive login: print the login URL, capture the `request_token`
        from Kite's redirect via a one-shot local HTTP server, and fall back to
        prompting the user to paste the redirect URL if that fails."""
        url = self.login_url()
        print(f"Open this URL to log in to Kite:\n{url}")  # noqa: T201 -- interactive CLI output
        if open_browser:
            try:
                webbrowser.open(url)
            except Exception as exc:  # pragma: no cover -- environment dependent
                logger.debug("could not open browser automatically: %s", exc)

        request_token: str | None = None
        try:
            request_token = _capture_request_token_via_server(
                self.settings.kite_redirect_port, timeout
            )
        except OSError as exc:
            logger.warning("local callback server unavailable (%s); falling back to manual paste", exc)

        if not request_token:
            redirect_url = input(
                "Could not capture the redirect automatically.\n"
                "Paste the full redirect URL (or just the request_token) here: "
            ).strip()
            request_token = _extract_request_token(redirect_url) or redirect_url or None

        if not request_token:
            raise AuthError("login aborted: no request_token captured")

        return self.exchange_request_token(request_token)

    def totp_login(self) -> str:
        """Best-effort automated login using Kite's *unofficial* web endpoints
        (kite.zerodha.com/api/login, /api/twofa), driven by
        TOS_KITE_USER_ID / TOS_KITE_PASSWORD / TOS_KITE_TOTP_SECRET.

        These endpoints are undocumented and Zerodha can change or block them
        without notice -- this flow may break at any time. `interactive_login`
        (which only relies on the official Connect login redirect) is the
        reliable fallback.
        """
        s = self.settings
        if not (s.kite_user_id and s.kite_password and s.kite_totp_secret):
            raise AuthError(
                "totp_login requires TOS_KITE_USER_ID, TOS_KITE_PASSWORD and "
                "TOS_KITE_TOTP_SECRET to be set"
            )

        session = requests.Session()
        try:
            login_resp = session.post(
                _KITE_LOGIN_API,
                data={"user_id": s.kite_user_id, "password": s.kite_password},
                timeout=15,
            )
            login_resp.raise_for_status()
            request_id = login_resp.json()["data"]["request_id"]

            totp_code = pyotp.TOTP(s.kite_totp_secret).now()
            twofa_resp = session.post(
                _KITE_TWOFA_API,
                data={
                    "user_id": s.kite_user_id,
                    "request_id": request_id,
                    "twofa_value": totp_code,
                    "twofa_type": "totp",
                },
                timeout=15,
            )
            twofa_resp.raise_for_status()

            location = ""
            next_url = self.login_url()
            for _ in range(5):
                redirect_resp = session.get(next_url, timeout=15, allow_redirects=False)
                location = redirect_resp.headers.get("Location", "")
                if "request_token" in location:
                    break
                if not location:
                    break
                next_url = location

            request_token = _extract_request_token(location)
            if not request_token:
                raise AuthError("totp_login: could not find request_token in redirect chain")
        except AuthError:
            raise
        except Exception as exc:  # requests errors, KeyError/JSON errors, etc.
            raise AuthError(f"totp_login failed: {exc}") from exc

        return self.exchange_request_token(request_token)

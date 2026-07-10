"""Telegram alerting. Optional: disabled (no-op) unless both bot token and chat id are set.

``send`` never raises — network/HTTP errors are logged at WARNING (without leaking the bot
token) and the call returns False.
"""

from __future__ import annotations

import requests

from tradingos.config.settings import Settings
from tradingos.core.logging import get_logger
from tradingos.core.models import Fill, Order

logger = get_logger(__name__)

_TELEGRAM_API = "https://api.telegram.org"


class TelegramAlerter:
    """Sends alert messages to a Telegram chat via the Bot API.

    Disabled (no-op, logged once at INFO) unless both ``bot_token`` and ``chat_id`` are set.
    """

    def __init__(self, bot_token: str | None, chat_id: str | None, timeout: float = 5.0) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout = timeout
        if not self.enabled:
            logger.info("TelegramAlerter disabled (bot token and/or chat id not configured)")

    @classmethod
    def from_settings(cls, settings: Settings) -> TelegramAlerter:
        return cls(settings.telegram_bot_token, settings.telegram_chat_id)

    @property
    def enabled(self) -> bool:
        return bool(self.bot_token) and bool(self.chat_id)

    def send(self, text: str) -> bool:
        if not self.enabled:
            return False
        url = f"{_TELEGRAM_API}/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"}
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
        except requests.RequestException as exc:
            logger.warning("telegram send failed: %s", type(exc).__name__)
            return False
        if response.status_code != 200:
            logger.warning("telegram send failed: status %s", response.status_code)
            return False
        return True

    def alert_fill(self, fill: Fill) -> bool:
        text = (
            f"<b>Fill</b> {fill.side.value} {fill.qty} {fill.symbol} @ {fill.price:.2f}"
            f" (charges {fill.charges:.2f})"
        )
        return self.send(text)

    def alert_rejection(self, order: Order, reason: str) -> bool:
        text = (
            f"<b>Order rejected</b> {order.side.value} {order.qty} {order.symbol}: {reason}"
        )
        return self.send(text)

    def alert_risk(self, message: str) -> bool:
        text = f"<b>Risk alert</b> {message}"
        return self.send(text)

    def alert_token_expiry(self, message: str = "Kite access token expired") -> bool:
        text = f"<b>Token expiry</b> {message}"
        return self.send(text)

"""Environment settings. All secrets come from environment / .env — never code.

Copy .env.example to .env and fill in credentials. `Settings()` reads both.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="TOS_", extra="ignore"
    )

    # --- paths (all relative to project root by default) ---
    data_dir: Path = Path("data")
    artifacts_dir: Path = Path("artifacts")

    # --- Kite Connect (secrets; leave unset until live/paper) ---
    kite_api_key: str | None = None
    kite_api_secret: str | None = None
    kite_user_id: str | None = None
    kite_password: str | None = None  # only used by optional TOTP-assisted login
    kite_totp_secret: str | None = None
    kite_redirect_port: int = 8721  # local port that captures the request_token redirect

    # --- Telegram alerts (optional) ---
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    # --- risk defaults for live trading (override via env) ---
    max_order_value: float = 200_000.0
    max_position_pct: float = 0.10
    max_daily_loss: float = 25_000.0
    max_orders_per_day: int = 50

    log_level: str = "INFO"

    # --- derived paths ---
    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "parquet" / "raw"

    @property
    def adjusted_dir(self) -> Path:
        return self.data_dir / "parquet" / "adjusted"

    @property
    def ticks_dir(self) -> Path:
        return self.data_dir / "ticks"

    @property
    def duckdb_path(self) -> Path:
        return self.data_dir / "market.duckdb"

    @property
    def meta_db_path(self) -> Path:
        return self.data_dir / "meta.sqlite"  # instruments, corp actions, universe

    @property
    def experiments_db_path(self) -> Path:
        return self.artifacts_dir / "experiments.sqlite"

    @property
    def paper_db_path(self) -> Path:
        return self.data_dir / "paper_ledger.sqlite"

    @property
    def live_db_path(self) -> Path:
        return self.data_dir / "live.sqlite"  # live order journal (reuses the paper schema)

    @property
    def token_cache_path(self) -> Path:
        return self.data_dir / "kite_token.json"

    @property
    def kill_switch_path(self) -> Path:
        return self.data_dir / "KILL_SWITCH"

    def ensure_dirs(self) -> None:
        for p in (self.raw_dir, self.adjusted_dir, self.ticks_dir, self.artifacts_dir):
            p.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    """For tests."""
    get_settings.cache_clear()


# Convenience holder so tests can construct isolated Settings easily.
def settings_for(tmp_root: Path) -> Settings:
    return Settings(data_dir=tmp_root / "data", artifacts_dir=tmp_root / "artifacts")

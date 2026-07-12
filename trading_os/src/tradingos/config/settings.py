"""Environment settings. All secrets come from environment / .env — never code.

Copy .env.example to .env and fill in credentials. `Settings()` reads both.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_env_file() -> str | Path:
    """Locate the ``.env`` to load, tolerant of the CLI being launched from a
    subdirectory (e.g. ``scripts/adhoc/``) rather than the project root.

    Precedence (highest first): explicit ``TOS_*`` environment variables
    (pydantic-settings always prefers real env vars over any dotenv value, so
    that ordering falls out of the source priority and needs no help here) >
    a ``.env`` in the current working directory (pydantic-settings' existing,
    cwd-relative default -- unchanged, and what every normal "run from repo
    root" invocation already hits) > a ``.env`` at the project root, found by
    walking up from cwd to the nearest ancestor containing ``pyproject.toml``.

    Returns a bare ``".env"`` (resolved by pydantic-settings relative to cwd,
    same as the old hardcoded default) when cwd already has one, or when no
    project root / project-root .env can be found -- i.e. this only ever
    *adds* a fallback, never changes behavior for a cwd that already has a
    ``.env`` (including the common case of running from the project root).
    """
    cwd = Path.cwd()
    if (cwd / ".env").exists():
        return ".env"

    for parent in (cwd, *cwd.parents):
        if (parent / "pyproject.toml").exists():
            root_env = parent / ".env"
            return root_env if root_env.exists() else ".env"

    return ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="TOS_", extra="ignore"
    )

    def __init__(self, **data: Any) -> None:
        # Only compute a resolved default when the caller didn't pass
        # `_env_file` themselves -- tests pass `_env_file=None` to opt out of
        # dotenv loading entirely, and that must keep working unchanged.
        if "_env_file" not in data:
            data["_env_file"] = _resolve_env_file()
        super().__init__(**data)

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

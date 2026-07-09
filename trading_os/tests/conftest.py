from __future__ import annotations

import sys
from pathlib import Path

import pytest

# make tests/fixtures importable as `fixtures`
sys.path.insert(0, str(Path(__file__).parent))

from tradingos.config.settings import Settings  # noqa: E402


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    """Isolated Settings rooted in tmp_path (no real data dirs touched)."""
    s = Settings(
        data_dir=tmp_path / "data",
        artifacts_dir=tmp_path / "artifacts",
        _env_file=None,  # tests never read the developer's .env
    )
    s.ensure_dirs()
    return s

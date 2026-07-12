"""Project-root .env discovery (see settings.py::_resolve_env_file).

Motivating incident: a script launched with cwd inside scripts/adhoc/ found
no .env (pydantic-settings resolves the default "env_file=.env" relative to
cwd), silently fell back to default paths pointing at nothing, and loaded
zero symbols. These tests pin the fallback-discovery precedence:
explicit TOS_ env var > cwd .env > project-root .env (nearest ancestor of
cwd containing pyproject.toml).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tradingos.config.settings import Settings


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    """<tmp>/project/pyproject.toml + .env, and an empty <tmp>/project/sub/
    subdirectory that tests chdir into to stand in for scripts/adhoc/."""
    root = tmp_path / "project"
    (root / "sub").mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname = 'dummy'\n")
    (root / ".env").write_text("TOS_KITE_USER_ID=root_value\n")
    return root


class TestEnvFileDiscovery:
    def test_cwd_subdir_falls_back_to_project_root_env(
        self, project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(project / "sub")
        s = Settings()
        assert s.kite_user_id == "root_value"

    def test_cwd_env_overrides_project_root_env(
        self, project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (project / "sub" / ".env").write_text("TOS_KITE_USER_ID=cwd_value\n")
        monkeypatch.chdir(project / "sub")
        s = Settings()
        assert s.kite_user_id == "cwd_value"

    def test_env_var_overrides_both_cwd_and_root_env(
        self, project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (project / "sub" / ".env").write_text("TOS_KITE_USER_ID=cwd_value\n")
        monkeypatch.setenv("TOS_KITE_USER_ID", "env_value")
        monkeypatch.chdir(project / "sub")
        s = Settings()
        assert s.kite_user_id == "env_value"

    def test_running_from_project_root_is_unchanged(
        self, project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The common case: cwd IS the project root, so cwd's own .env wins
        (identical to pydantic-settings' original hardcoded default)."""
        monkeypatch.chdir(project)
        s = Settings()
        assert s.kite_user_id == "root_value"

    def test_no_project_root_found_falls_back_to_plain_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No pyproject.toml anywhere above cwd (and no cwd .env): resolution
        must not raise, and Settings() must construct with plain defaults."""
        lonely = tmp_path / "lonely"
        lonely.mkdir()
        monkeypatch.chdir(lonely)
        monkeypatch.delenv("TOS_KITE_USER_ID", raising=False)
        s = Settings()
        assert s.kite_user_id is None

    def test_explicit_env_file_override_still_respected(
        self, project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """tests/conftest.py::settings passes `_env_file=None` to opt out of
        dotenv loading entirely for isolated test settings -- that must keep
        working exactly as before."""
        monkeypatch.chdir(project / "sub")
        s = Settings(_env_file=None)
        assert s.kite_user_id is None

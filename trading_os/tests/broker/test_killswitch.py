from __future__ import annotations

import json
from pathlib import Path

import pytest

from tradingos.broker.killswitch import KillSwitch
from tradingos.config.settings import Settings
from tradingos.core.errors import KillSwitchActive, RiskViolation


def test_not_active_when_file_absent(tmp_path: Path) -> None:
    ks = KillSwitch(tmp_path / "nested" / "KILL_SWITCH")
    assert ks.is_active is False
    assert ks.reason() is None
    ks.check()  # must not raise


def test_engage_creates_file_and_parent_dirs(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "dir" / "KILL_SWITCH"
    ks = KillSwitch(path)
    ks.engage("manual stop")
    assert path.exists()
    assert ks.is_active is True


def test_engage_writes_expected_json_content(tmp_path: Path) -> None:
    path = tmp_path / "KILL_SWITCH"
    ks = KillSwitch(path)
    ks.engage("broker disconnect")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["reason"] == "broker disconnect"
    assert "engaged_at" in data
    # engaged_at must be a parseable ISO datetime string
    from datetime import datetime

    datetime.fromisoformat(data["engaged_at"])


def test_engage_default_reason_is_empty_string(tmp_path: Path) -> None:
    path = tmp_path / "KILL_SWITCH"
    ks = KillSwitch(path)
    ks.engage()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["reason"] == ""
    assert ks.reason() is None  # empty reason normalizes to None


def test_engage_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "KILL_SWITCH"
    ks = KillSwitch(path)
    ks.engage("first")
    ks.engage("second")
    assert ks.is_active is True
    assert ks.reason() == "second"


def test_disengage_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "KILL_SWITCH"
    ks = KillSwitch(path)
    ks.engage("stop")
    ks.disengage()
    assert ks.is_active is False
    ks.disengage()  # calling again on an already-absent file must not raise
    assert ks.is_active is False


def test_reason_roundtrip(tmp_path: Path) -> None:
    ks = KillSwitch(tmp_path / "KILL_SWITCH")
    ks.engage("risk breach: daily loss")
    assert ks.reason() == "risk breach: daily loss"


def test_check_raises_kill_switch_active_when_engaged(tmp_path: Path) -> None:
    ks = KillSwitch(tmp_path / "KILL_SWITCH")
    ks.engage("halt trading")
    with pytest.raises(KillSwitchActive, match="halt trading"):
        ks.check()


def test_kill_switch_active_is_a_risk_violation(tmp_path: Path) -> None:
    ks = KillSwitch(tmp_path / "KILL_SWITCH")
    ks.engage("halt")
    with pytest.raises(RiskViolation):
        ks.check()


def test_check_does_not_raise_after_disengage(tmp_path: Path) -> None:
    ks = KillSwitch(tmp_path / "KILL_SWITCH")
    ks.engage("halt")
    ks.disengage()
    ks.check()  # must not raise


def test_corrupt_json_content_still_counts_as_active_with_reason_none(tmp_path: Path) -> None:
    path = tmp_path / "KILL_SWITCH"
    path.write_text("not valid json {{{", encoding="utf-8")
    ks = KillSwitch(path)
    assert ks.is_active is True
    assert ks.reason() is None
    with pytest.raises(KillSwitchActive):
        ks.check()


def test_legacy_non_dict_json_content_still_counts_as_active_with_reason_none(
    tmp_path: Path,
) -> None:
    path = tmp_path / "KILL_SWITCH"
    path.write_text(json.dumps(["legacy", "format"]), encoding="utf-8")
    ks = KillSwitch(path)
    assert ks.is_active is True
    assert ks.reason() is None


def test_empty_file_still_counts_as_active_with_reason_none(tmp_path: Path) -> None:
    path = tmp_path / "KILL_SWITCH"
    path.touch()
    ks = KillSwitch(path)
    assert ks.is_active is True
    assert ks.reason() is None


def test_from_settings_uses_configured_path(settings: Settings) -> None:
    ks = KillSwitch.from_settings(settings)
    assert ks.path == settings.kill_switch_path
    assert ks.is_active is False
    ks.engage("via settings")
    assert settings.kill_switch_path.exists()

"""File-based global kill switch, shared by paper and live trading.

The presence of the file at ``path`` means the switch is *engaged*: no new
orders may be placed anywhere in the platform until it is disengaged (or the
file is manually removed). File content is JSON::

    {"engaged_at": "<isoformat>", "reason": "<str>"}

The file is the single source of truth across processes (paper runner, live
runner, an operator's shell) — there is no in-memory state to get out of
sync.
"""

from __future__ import annotations

import json
from pathlib import Path

from tradingos.config.settings import Settings
from tradingos.core.errors import KillSwitchActive
from tradingos.core.logging import get_logger
from tradingos.core.timeutils import now_ist

logger = get_logger(__name__)


class KillSwitch:
    """File-based global kill switch shared by paper and live. Presence of the file at
    `path` = engaged. File content is JSON: {"engaged_at": <iso>, "reason": <str>}."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    @classmethod
    def from_settings(cls, settings: Settings) -> KillSwitch:
        return cls(settings.kill_switch_path)

    @property
    def is_active(self) -> bool:
        return self.path.exists()

    def reason(self) -> str | None:
        """The engaged reason, or None if not active.

        Tolerates corrupt or legacy file content: any read/parse failure is
        treated as "active but reason unknown" rather than raised, since the
        presence of the file (not its content) is what makes the switch
        active.
        """
        if not self.is_active:
            return None
        try:
            raw = self.path.read_text(encoding="utf-8")
            data = json.loads(raw)
            reason = data.get("reason")
        except (OSError, ValueError, AttributeError):
            return None
        return str(reason) if reason else None

    def engage(self, reason: str = "") -> None:
        """Engage the switch. Idempotent: safe to call while already engaged
        (overwrites the file with a fresh timestamp/reason)."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"engaged_at": now_ist().isoformat(), "reason": reason}
        self.path.write_text(json.dumps(payload), encoding="utf-8")
        logger.warning("kill switch engaged: reason=%r path=%s", reason, self.path)

    def disengage(self) -> None:
        """Disengage the switch. Idempotent: safe to call while already
        disengaged (no-op)."""
        if self.path.exists():
            self.path.unlink()
            logger.warning("kill switch disengaged: path=%s", self.path)

    def check(self) -> None:
        """Raise KillSwitchActive if the switch is engaged; no-op otherwise."""
        if self.is_active:
            reason = self.reason()
            message = f"kill switch active (reason: {reason})" if reason else "kill switch active"
            raise KillSwitchActive(message)

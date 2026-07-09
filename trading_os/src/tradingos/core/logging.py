"""Central logging setup. Use get_logger(__name__) everywhere; never print()."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
_configured = False


def setup_logging(level: int = logging.INFO, log_file: Path | None = None) -> None:
    global _configured
    root = logging.getLogger("tradingos")
    root.setLevel(level)
    if _configured:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(_FORMAT))
    root.addHandler(handler)
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setFormatter(logging.Formatter(_FORMAT))
        root.addHandler(fh)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    if not name.startswith("tradingos"):
        name = f"tradingos.{name}"
    return logging.getLogger(name)

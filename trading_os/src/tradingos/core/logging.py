"""Central logging setup. Use get_logger(__name__) everywhere; never print()."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, TextIO

_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
_configured = False


class _StderrHandler(logging.StreamHandler):
    """A StreamHandler that resolves ``sys.stderr`` at EMIT time.

    Binding the stream once at handler creation is a bug under anything that
    swaps and later closes ``sys.stderr`` (click/typer's ``CliRunner`` does
    exactly that): the handler keeps the closed captured stream, and every
    subsequent log call prints a "--- Logging error ---" block instead of the
    record. Looking the stream up per record means the handler always writes
    to whatever ``sys.stderr`` currently is.
    """

    @property
    def stream(self) -> TextIO:
        return sys.stderr

    @stream.setter
    def stream(self, value: Any) -> None:
        # StreamHandler.__init__/setStream assign this; the lookup stays dynamic.
        pass


def setup_logging(level: int = logging.INFO, log_file: Path | None = None) -> None:
    global _configured
    root = logging.getLogger("tradingos")
    root.setLevel(level)
    if _configured:
        return
    handler = _StderrHandler()
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

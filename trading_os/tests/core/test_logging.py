"""Regression tests for tradingos.core.logging.

The critical property: the stderr handler must resolve ``sys.stderr`` at EMIT
time, never hold the stream captured at setup time. Under click/typer's
``CliRunner`` the captured stream is CLOSED once the invocation returns, so a
handler that bound it at first-logger creation turns every later log call into
a "--- Logging error ---" block and silently drops the record.
"""

from __future__ import annotations

import io
import logging
import sys
from collections.abc import Iterator

import pytest

import tradingos.core.logging as tlog


@pytest.fixture()
def fresh_logging(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Run setup_logging from a clean slate, restoring global state afterwards."""
    root = logging.getLogger("tradingos")
    saved_handlers = root.handlers[:]
    saved_level = root.level
    monkeypatch.setattr(tlog, "_configured", False)
    root.handlers = []
    yield
    for handler in root.handlers:
        try:
            handler.close()
        except Exception:
            pass
    root.handlers = saved_handlers
    root.setLevel(saved_level)


def test_get_logger_prefixes_names() -> None:
    assert tlog.get_logger("costs.model").name == "tradingos.costs.model"
    assert tlog.get_logger("tradingos.engine").name == "tradingos.engine"


def test_stderr_handler_tracks_current_stderr(
    fresh_logging: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    tlog.setup_logging()
    root = logging.getLogger("tradingos")
    handler = next(h for h in root.handlers if isinstance(h, logging.StreamHandler))
    swapped = io.StringIO()
    monkeypatch.setattr(sys, "stderr", swapped)
    # The stream is looked up per use, not frozen at handler creation.
    assert handler.stream is swapped


def test_emit_survives_swapped_and_closed_stderr(
    fresh_logging: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The CliRunner scenario: configure while stderr is stream A, then A is
    closed and replaced — later emits must land on the NEW stderr, cleanly."""
    stream_a = io.StringIO()
    monkeypatch.setattr(sys, "stderr", stream_a)
    tlog.setup_logging()
    log = tlog.get_logger("core.test_logging")

    log.warning("first message")
    assert "first message" in stream_a.getvalue()

    # CliRunner closes the captured stream after the invocation returns.
    stream_b = io.StringIO()
    monkeypatch.setattr(sys, "stderr", stream_b)
    stream_a.close()

    log.warning("second message")
    out = stream_b.getvalue()
    assert "--- Logging error ---" not in out  # no stale-stream blowup
    assert "WARNING tradingos.core.test_logging: second message" in out


def test_file_handler_still_writes(fresh_logging: None, tmp_path) -> None:
    log_file = tmp_path / "logs" / "run.log"
    tlog.setup_logging(log_file=log_file)
    tlog.get_logger("core.test_logging").warning("to file")
    for handler in logging.getLogger("tradingos").handlers:
        handler.flush()
    assert "to file" in log_file.read_text()

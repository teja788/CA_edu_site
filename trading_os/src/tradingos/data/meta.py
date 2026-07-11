"""Shared SQLite (sqlmodel) metadata database seam.

Instruments, symbol-mapping, corporate-actions, dividend and point-in-time
universe tables all live in one file (settings.meta_db_path). Table models are
defined in their domain modules; this module only owns the engine/session
factory so parallel modules never fight over connection setup.

Note: SQLModel.metadata.create_all only creates tables whose models have been
imported — domain modules are imported here so any session sees all tables.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

_engines: dict[Path, Engine] = {}


def _import_table_models() -> None:
    # Deferred to avoid import cycles: domain modules import meta_session from here.
    for mod in ("tradingos.data.instruments", "tradingos.data.actions", "tradingos.data.universe"):
        try:
            __import__(mod)
        except ImportError:  # module not built yet — fine during incremental development
            pass


def meta_engine(db_path: Path) -> Engine:
    path = Path(db_path).resolve()
    eng = _engines.get(path)
    if eng is None:
        path.parent.mkdir(parents=True, exist_ok=True)
        eng = create_engine(f"sqlite:///{path}")
        _engines[path] = eng
    _import_table_models()
    SQLModel.metadata.create_all(eng)
    return eng


def meta_session(db_path: Path) -> Session:
    """Session on the shared metadata DB. Use as a context manager."""
    return Session(meta_engine(db_path))

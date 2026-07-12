"""Engine/session factory for the experiments SQLite registry.

Keyed on ``settings.experiments_db_path`` so repeated calls reuse one engine per
file (mirrors ``data/meta.py``). ``create_all`` is idempotent and only touches
the experiments tables. **All writes happen in the parent process only** — the
grid workers return plain row dicts and never open a session.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from tradingos.config.settings import Settings

# Import the table models so SQLModel.metadata knows them before create_all.
from tradingos.experiments import models as _models  # noqa: F401

_engines: dict[Path, Engine] = {}


def get_engine(settings: Settings) -> Engine:
    """Return (creating on first use) the SQLAlchemy engine for this settings'
    experiments DB. Creates parent dirs and the experiments tables idempotently.
    """
    path = Path(settings.experiments_db_path).resolve()
    eng = _engines.get(path)
    if eng is None:
        path.parent.mkdir(parents=True, exist_ok=True)
        eng = create_engine(f"sqlite:///{path}")
        SQLModel.metadata.create_all(eng)
        _migrate_columns(eng)
        _engines[path] = eng
    return eng


def _migrate_columns(eng: Engine) -> None:
    """Additive, idempotent column migrations for pre-existing registry files.

    ``create_all`` never alters existing tables, so columns added to
    :class:`ExperimentRun` after a DB was created must be back-filled here or
    every SELECT against an old registry fails.
    """
    with eng.connect() as conn:
        cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(experimentrun)")}
        if cols and "warnings_json" not in cols:
            conn.exec_driver_sql(
                "ALTER TABLE experimentrun ADD COLUMN warnings_json TEXT NOT NULL DEFAULT '[]'"
            )
            conn.commit()
        if cols and "is_marked" not in cols:
            conn.exec_driver_sql(
                "ALTER TABLE experimentrun ADD COLUMN is_marked BOOLEAN NOT NULL DEFAULT 0"
            )
            conn.commit()


@contextmanager
def session_scope(settings: Settings) -> Iterator[Session]:
    """Transactional session context manager: commits on success, rolls back on
    error, always closes. Parent-process use only."""
    session = Session(get_engine(settings))
    try:
        yield session
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


__all__ = ["get_engine", "session_scope"]

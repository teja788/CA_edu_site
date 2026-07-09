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
        _engines[path] = eng
    SQLModel.metadata.create_all(eng)
    return eng


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

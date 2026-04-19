"""DB engine and sessions. Schema changes: use Alembic; ``init_db`` is for tests / quick local bootstrap only."""

from __future__ import annotations

import os
from contextlib import contextmanager
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.db.models import Base

load_dotenv()


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    path = os.environ.get("SQLITE_PATH", "data/app.sqlite3")
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    return f"sqlite:///{os.path.abspath(path)}"


@lru_cache
def get_engine() -> Engine:
    url = _database_url()
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(url, echo=os.environ.get("SQL_ECHO", "").lower() in ("1", "true"), connect_args=connect_args)


def get_session_factory():
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    """Create tables (for tests / local bootstrap). Prefer Alembic migrations in production."""
    Base.metadata.create_all(bind=get_engine())


@contextmanager
def session_scope():
    """Context manager yielding a Session."""
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

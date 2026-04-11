"""SQLite engine and session helpers."""
from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

from hear_say.config import DB_URL

# check_same_thread=False so background job workers can share the connection
engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


def init_db() -> None:
    """Create tables on startup (idempotent)."""
    from hear_say import models  # noqa: F401 — register metadata

    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """FastAPI dependency — one session per request."""
    with Session(engine) as session:
        yield session

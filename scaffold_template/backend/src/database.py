"""Database setup: one engine per process, one session per request.

Tables are SQLAlchemy models (each entity's models.py). init_db() creates missing
tables at startup; switch to migrations (Alembic) once the schema needs to change
without losing data.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config import settings


class Base(DeclarativeBase):
    """Parent of every table model."""


_sqlite = settings.database_url.startswith("sqlite")
engine = create_engine(
    settings.database_url,
    # SQLite connections are used from FastAPI's thread pool.
    connect_args={"check_same_thread": False} if _sqlite else {},
)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def init_db() -> None:
    """Create any missing tables. Import every models module here so its tables register."""
    import src.auth.models  # noqa: F401

    if _sqlite:
        settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: a session for one request, closed afterwards."""
    with SessionLocal() as session:
        yield session

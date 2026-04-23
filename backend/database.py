"""Database configuration for the AICES backend."""

import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DEFAULT_DB_PATH = Path(os.getenv("AICES_DB_PATH", PROJECT_ROOT / "data" / "aices.db")).expanduser()
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")


def _get_sqlite_file_path(database_url: str) -> Path | None:
    """Return a SQLite file path for local database URLs."""
    if not database_url.startswith("sqlite:///") or database_url.endswith(":memory:"):
        return None

    raw_path = database_url.replace("sqlite:///", "", 1)
    if not raw_path:
        return None

    return Path(raw_path).expanduser()


sqlite_file_path = _get_sqlite_file_path(DATABASE_URL)
if sqlite_file_path is not None:
    sqlite_file_path.parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine_kwargs = {"connect_args": connect_args}

if DATABASE_URL.endswith(":memory:"):
    engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, **engine_kwargs)


if DATABASE_URL.startswith("sqlite") and not DATABASE_URL.endswith(":memory:"):
    @event.listens_for(engine, "connect")
    def _configure_sqlite_connection(dbapi_connection, _):
        """Make file-backed SQLite reliable on constrained demo filesystems."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=OFF")
        cursor.execute("PRAGMA synchronous=OFF")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Yield a database session for each request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

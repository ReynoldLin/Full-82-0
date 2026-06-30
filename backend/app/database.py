"""
Database engine and session configuration.

This is the single source of truth for how we connect to SQLite. Both the
live FastAPI app and the offline pipeline scripts import from here so there
is only ever one engine/session setup for the whole project.
"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# backend/app/database.py -> backend/
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR / 'nba.db'}"

# check_same_thread=False is needed because FastAPI can handle a request
# in a different thread than the one that created the session.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db() -> None:
    """Create all tables that don't already exist. Safe to call repeatedly."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency that yields a session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
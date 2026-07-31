from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# If using SQLite, we disable thread validation so FastAPI threads can read/write on the same db
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=settings.debug,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a db session and closing it on completion.
    Why: Safe resource teardown inside FastAPI middleware/routes execution chain.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings
import datetime

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def utcnow() -> datetime.datetime:
    """Current UTC time as a naive datetime — matches the existing DB columns
    (plain DateTime, not timezone-aware), while avoiding the deprecated
    datetime.datetime.utcnow(). Use this everywhere instead of utcnow()."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

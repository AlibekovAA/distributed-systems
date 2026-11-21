from contextlib import contextmanager

from app.core.config import DATABASE_URL
from app.core.logger import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

database_url = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(database_url, pool_pre_ping=True, pool_recycle=3600)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        logging.error("Database session error")
        raise
    finally:
        db.close()


def get_db_dependency():
    with get_db() as db:
        yield db

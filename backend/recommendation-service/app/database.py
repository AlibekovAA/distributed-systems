from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from app.config import DATABASE_URL
from app.logger import logging

Base = declarative_base()
_engine = None
_SessionLocal = None


def _init_db_connection() -> None:
    global _engine, _SessionLocal
    try:
        _engine = create_engine(
            DATABASE_URL,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={"connect_timeout": 5},
            echo=False
        )
        Base.metadata.create_all(bind=_engine)
        _SessionLocal = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        )
        logging.info("Database connection initialized")
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        raise


@contextmanager
def get_db() -> Generator[Session, None, None]:
    if _SessionLocal is None:
        _init_db_connection()

    db = _SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"Database error: {e}")
        raise
    finally:
        db.close()
        logging.debug("Database session closed")

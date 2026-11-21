from contextlib import contextmanager
from typing import Any, Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import DATABASE_URL
from app.logger import logging

Base = declarative_base()
database_url = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
engine_options: dict[str, Any] = {"pool_pre_ping": True, "pool_recycle": 3600}
if not database_url.startswith("sqlite"):
    engine_options.update({"pool_size": 20, "max_overflow": 10, "connect_args": {"connect_timeout": 5}})
engine = create_engine(database_url, **engine_options)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
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

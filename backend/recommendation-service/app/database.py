from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

from app.config import DATABASE_URL
from app.logger import log_time, logging

Base = declarative_base()

try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logging.error(f"{log_time()} - Database connection failed: {str(e)}")
    raise e

SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logging.error(f"{log_time()} - Database session error: {str(e)}")
        raise e
    finally:
        db.close()

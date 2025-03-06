from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

from app.core.config import DATABASE_URL
from app.core.logger import log_time, logging


class Base(DeclarativeBase):
    pass


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

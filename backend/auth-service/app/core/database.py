from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import DATABASE_URL
from app.core.logger import log_time, logging

Base = declarative_base()

try:
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logging.error(f"{log_time()} - Database connection failed: {str(e)}")
    raise e

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        logging.info(f"{log_time()} - New database session created")
        yield db
    except Exception as e:
        logging.error(f"{log_time()} - Database session error: {str(e)}")
        raise e
    finally:
        logging.info(f"{log_time()} - Database session closed")
        db.close()

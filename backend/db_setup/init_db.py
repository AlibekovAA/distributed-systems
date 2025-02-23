import os
import logging
from sqlalchemy import create_engine
from models.base import Base
from config import DATABASE_URL

log_file_path = 'logs/init_db.log'
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

try:
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    logging.info("Database has been successfully initialized")
except Exception as e:
    logging.error(f"Error initializing database: {str(e)}")
    raise

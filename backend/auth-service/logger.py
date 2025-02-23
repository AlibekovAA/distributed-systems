import logging
import os
from datetime import datetime
import pytz

moscow_tz = pytz.timezone('Europe/Moscow')

log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

log_file_path = os.path.join(log_dir, 'app.log')

logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


def log_time():
    return datetime.now(moscow_tz).strftime('%Y-%m-%d %H:%M:%S')

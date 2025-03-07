import logging
from datetime import datetime
import pytz

moscow_tz = pytz.timezone('Europe/Moscow')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler()
    ]
)


def log_time():
    return datetime.now(moscow_tz).strftime('%Y-%m-%d %H:%M:%S')

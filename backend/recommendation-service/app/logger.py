import logging
from datetime import datetime
import pytz

from app.config import LOG_LEVEL

moscow_tz = pytz.timezone('Europe/Moscow')

log_level = getattr(logging, LOG_LEVEL, logging.WARNING)


class MoscowTimeFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created)
        dt = moscow_tz.localize(dt)
        return dt.strftime(datefmt or '%Y-%m-%d %H:%M:%S')


formatter = MoscowTimeFormatter(
    fmt='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logging.root.handlers = []
logging.root.addHandler(handler)
logging.root.setLevel(log_level)

logging.info(f"Logger initialized with level: {LOG_LEVEL}")

pika_logger = logging.getLogger("pika")
pika_logger.setLevel(logging.WARNING)

app_logger = logging.getLogger("recommendation_app")
app_logger.setLevel(logging.WARNING)


def log_message(message: str) -> str:
    return message

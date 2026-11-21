import logging
from datetime import datetime, timedelta, timezone

from app.config import LOG_LEVEL

moscow_tz = timezone(timedelta(hours=3), name="Europe/Moscow")

log_level = getattr(logging, LOG_LEVEL, logging.WARNING)


class MoscowTimeFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=moscow_tz)
        return dt.strftime(datefmt or "%Y-%m-%d %H:%M:%S")


formatter = MoscowTimeFormatter(fmt="%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

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

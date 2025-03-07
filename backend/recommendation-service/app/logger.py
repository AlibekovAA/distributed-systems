import logging
from datetime import datetime
import pytz

moscow_tz = pytz.timezone('Europe/Moscow')

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler()]
)

pika_logger = logging.getLogger("pika")
pika_logger.setLevel(logging.WARNING)

app_logger = logging.getLogger("recommendation_app")
app_logger.setLevel(logging.WARNING)


def log_time() -> str:
    return datetime.now(moscow_tz).strftime("%Y-%m-%d %H:%M:%S")

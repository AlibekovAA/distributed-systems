import signal
import sys

from app.crud import get_recommendations_for_user, update_user_preferences
from app.database import get_db
from app.logger import logging
from app.messaging import RabbitMQConnection


def handle_sigterm(*args) -> None:
    sys.exit(0)


def process_message(message: dict, properties) -> dict:
    raw_user_id = message.get("user_id") if isinstance(message, dict) else message
    if raw_user_id is None:
        raise ValueError("user_id is required")
    user_id = int(raw_user_id)
    logging.info("Processing recommendation request: request_id=%s", properties.correlation_id)

    with get_db() as db:
        update_user_preferences(db, user_id)
        return {"user_id": user_id, "recommendations": get_recommendations_for_user(db, user_id)}


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_sigterm)
    rabbit = RabbitMQConnection(queue_name="recommendations")

    try:
        logging.info("Starting recommendation service")
        rabbit.connect()
        rabbit.receive_message(process_message)
    except KeyboardInterrupt:
        logging.info("Shutting down service")
    finally:
        rabbit.close()

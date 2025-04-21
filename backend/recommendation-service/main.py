import signal
import sys

from app.crud import get_recommendations_for_user, update_user_preferences
from app.database import get_db
from app.logger import logging
from app.messaging import RabbitMQConnection


def handle_sigterm(*args) -> None:
    sys.exit(0)


def process_message(message: dict, properties) -> dict:
    try:
        user_id = message.get('user_id') if isinstance(message, dict) else int(message)
        logging.info(f"Processing user {user_id}")

        with get_db() as db:
            update_user_preferences(db, user_id)
            return {
                'user_id': user_id,
                'recommendations': get_recommendations_for_user(db, user_id)
            }
    except Exception as e:
        logging.error(f"Processing failed: {e}")
        return None


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

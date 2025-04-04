import json
import signal
import sys

from app.crud import get_recommendations_for_user, update_user_preferences
from app.database import get_db
from app.logger import logging
from app.messaging import RabbitMQConnection


def handle_sigterm(*args):
    sys.exit(0)


def process_message(message, properties):
    try:
        logging.info(f"Received message: {message}, type: {type(message)}")

        if isinstance(message, dict):
            logging.info(f"Message content: {json.dumps(message, indent=2)}")
            user_id = message.get('user_id')
            if user_id is None:
                raise ValueError("No user_id in message")
        else:
            user_id = int(message)

        logging.info(f"Processing for user_id: {user_id}")

        with get_db() as db:
            update_user_preferences(db, user_id)
            recommendations = get_recommendations_for_user(db, user_id)
            response = {
                'user_id': user_id,
                'recommendations': recommendations
            }
            logging.info(f"Prepared response: {json.dumps(response, indent=2)}")
            return response

    except Exception as e:
        logging.error(f"Error processing message: {e}")
        logging.exception("Full traceback:")
        return None


signal.signal(signal.SIGTERM, handle_sigterm)

rabbit = RabbitMQConnection(queue_name="recommendations")

try:
    logging.info(f"Starting recommendation service")
    rabbit.connect()
    rabbit.receive_message(process_message)
except KeyboardInterrupt:
    logging.info(f"Shutting down recommendation service")
    rabbit.close()

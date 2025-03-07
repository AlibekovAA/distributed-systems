import signal
import sys
import json

from app.messaging import RabbitMQConnection
from app.logger import logging, log_time
from app.database import get_db
from app.crud import get_recommendations_for_user


def handle_sigterm(*args):
    sys.exit(0)


def process_message(message):
    try:
        logging.info(f"{log_time()} - Received message: {message}, type: {type(message)}")

        if isinstance(message, dict):
            logging.info(f"{log_time()} - Message content: {json.dumps(message, indent=2)}")
            user_id = message.get('user_id')
            if user_id is None:
                raise ValueError("No user_id in message")
        else:
            user_id = int(message)

        logging.info(f"{log_time()} - Processing for user_id: {user_id}")

        with get_db() as db:
            recommendations = get_recommendations_for_user(db, user_id)
            response = {
                'user_id': user_id,
                'recommendations': recommendations
            }
            logging.info(f"{log_time()} - Sending response: {json.dumps(response, indent=2)}")
            rabbit.send_message(response)

    except Exception as e:
        logging.error(f"{log_time()} - Error processing message: {e}")
        logging.exception("Full traceback:")


signal.signal(signal.SIGTERM, handle_sigterm)

rabbit = RabbitMQConnection(queue_name="recommendations")

try:
    logging.info(f"{log_time()} - Starting recommendation service")
    rabbit.connect()
    rabbit.receive_message(process_message)
except KeyboardInterrupt:
    logging.info(f"{log_time()} - Shutting down recommendation service")
    rabbit.close()

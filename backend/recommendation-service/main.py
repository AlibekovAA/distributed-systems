import signal
import sys

from app.messaging import RabbitMQConnection
from app.logger import logging, log_time
from app.database import get_db
from app.crud import get_order_history_by_user_id


def handle_sigterm(*args):
    sys.exit(0)


def process_message(message):
    try:
        user_id = message.get('user_id')
        if not user_id:
            logging.error(f"{log_time()} - Received message without user_id")
            return

        with get_db() as db:
            history = get_order_history_by_user_id(db, user_id)
            recommendations = []
            rabbit.send_message({
                'user_id': user_id,
                'recommendations': recommendations
            })

    except Exception as e:
        logging.error(f"{log_time()} - Error processing message: {e}")


signal.signal(signal.SIGTERM, handle_sigterm)

rabbit = RabbitMQConnection(queue_name="recommendations")

try:
    logging.info(f"{log_time()} - Starting recommendation service")
    rabbit.connect()
    rabbit.receive_message(process_message)
except KeyboardInterrupt:
    logging.info(f"{log_time()} - Shutting down recommendation service")
    rabbit.close()

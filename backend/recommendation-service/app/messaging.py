import json
import pika
from urllib.parse import urlparse

from app.logger import logging
from app.config import RABBITMQ_URL
from app.database import get_db
from app.crud import get_recommendations_for_user


def process_message(message):
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
            recommendations = get_recommendations_for_user(db, user_id)
            response = {
                'user_id': user_id,
                'recommendations': recommendations
            }
            logging.info(f"Sending response: {json.dumps(response, indent=2)}")
            return response

    except Exception as e:
        logging.error(f"Error processing message: {e}")
        logging.exception("Full traceback:")
        return {"error": str(e)}


class RabbitMQConnection:
    def __init__(self, url: str = RABBITMQ_URL, queue_name: str = "recommendations"):
        self.url = urlparse(url)
        self.queue_name = queue_name
        self.response_queue = "recommendations_response"
        self.connection = None
        self.channel = None

    def connect(self):
        try:
            credentials = pika.PlainCredentials(self.url.username, self.url.password)
            parameters = pika.ConnectionParameters(
                host=self.url.hostname,
                port=self.url.port,
                credentials=credentials,
                virtual_host=self.url.path[1:] or '/',
                heartbeat=600,
                blocked_connection_timeout=300,
                connection_attempts=3,
                retry_delay=5
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            for queue in [self.queue_name, self.response_queue]:
                self.channel.queue_declare(
                    queue=queue,
                    durable=True,
                    auto_delete=False,
                    exclusive=False,
                )
        except Exception as e:
            logging.error(f"Error connecting to RabbitMQ: {e}")
            raise

    def close(self):
        if self.connection:
            self.connection.close()
            logging.info("Connection to RabbitMQ closed.")

    def send_message(self, message: dict):
        if not self.channel:
            raise Exception("Connection to RabbitMQ is not established")
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key=self.response_queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
        except Exception as e:
            logging.error(f"Error sending message: {e}")

    def receive_message(self, callback):
        if not self.channel:
            raise Exception("Connection to RabbitMQ is not established")

        def on_message(ch, method, properties, body):
            try:
                message = json.loads(body)
            except json.JSONDecodeError:
                message = body.decode()

            result = callback(message)

            if properties.reply_to:
                self.channel.basic_publish(
                    exchange='',
                    routing_key=properties.reply_to,
                    body=json.dumps(result),
                    properties=pika.BasicProperties(
                        correlation_id=properties.correlation_id,
                        content_type='application/json'
                    )
                )

        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=on_message,
            auto_ack=True
        )
        self.channel.start_consuming()

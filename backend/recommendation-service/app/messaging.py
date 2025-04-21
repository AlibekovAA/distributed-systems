import json
from urllib.parse import urlparse

import pika

from app.config import RABBITMQ_URL
from app.crud import get_recommendations_for_user
from app.database import get_db
from app.logger import logging


def _parse_message(body) -> dict:
    message = body.decode() if isinstance(body, bytes) else body

    if isinstance(message, str):
        try:
            return json.loads(message)
        except json.JSONDecodeError:
            return {"user_id": int(message)}
    return message


def process_message(ch, method, properties, body) -> None:
    try:
        logging.info(f"Received message: {body}")

        message = _parse_message(body)
        user_id = message.get("user_id") or int(message)
        logging.info(f"Processing recommendations for user {user_id}")

        with get_db() as db:
            response = {
                'user_id': user_id,
                'recommendations': get_recommendations_for_user(db, user_id)
            }

            ch.basic_publish(
                exchange='',
                routing_key='recommendations_response',
                body=json.dumps(response),
                properties=pika.BasicProperties(
                    content_type='application/json',
                    message_id=str(user_id)
                )
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logging.error(f"Message processing failed: {e}")
        logging.exception("Error details:")


class RabbitMQConnection:
    def __init__(self, url: str = RABBITMQ_URL, queue_name: str = "recommendations"):
        self.url = urlparse(url)
        self.queue_name = queue_name
        self.response_queue = "recommendations_response"
        self.connection = None
        self.channel = None

    def connect(self) -> None:
        try:
            credentials = pika.PlainCredentials(self.url.username, self.url.password)
            parameters = pika.ConnectionParameters(
                host=self.url.hostname,
                port=self.url.port,
                credentials=credentials,
                virtual_host=self.url.path[1:] or '/',
                heartbeat=600,
                blocked_connection_timeout=300
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            for queue in (self.queue_name, self.response_queue):
                self.channel.queue_declare(
                    queue=queue,
                    durable=True,
                    auto_delete=False
                )

            self.channel.basic_qos(prefetch_count=1)
            logging.info("RabbitMQ connection established")

        except Exception as e:
            logging.error(f"RabbitMQ connection failed: {e}")
            raise

    def close(self) -> None:
        if self.connection:
            self.connection.close()
            logging.info("RabbitMQ connection closed")

    def send_message(self, message: dict, routing_key: str = None, correlation_id: str = None) -> None:
        if not self.channel:
            raise RuntimeError("RabbitMQ connection not established")

        properties = pika.BasicProperties(
            delivery_mode=2,
            content_type='application/json',
            correlation_id=correlation_id
        )

        self.channel.basic_publish(
            exchange='',
            routing_key=routing_key or self.response_queue,
            body=json.dumps(message),
            properties=properties
        )
        logging.debug(f"Message sent to {routing_key}")

    def receive_message(self, callback) -> None:
        if not self.channel:
            raise RuntimeError("RabbitMQ connection not established")

        def wrapped_callback(ch, method, properties, body):
            try:
                message = _parse_message(body)
                result = callback(message, properties)

                if result and properties.reply_to:
                    self.send_message(
                        message=result,
                        routing_key=properties.reply_to,
                        correlation_id=properties.correlation_id
                    )
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logging.error(f"Message processing failed: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=wrapped_callback,
            auto_ack=False
        )
        logging.info(f"Listening to queue: {self.queue_name}")
        self.channel.start_consuming()

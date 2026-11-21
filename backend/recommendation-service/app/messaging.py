import json
from typing import Any
from urllib.parse import urlparse

import pika
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection

from app.config import RABBITMQ_URL
from app.logger import logging


def _parse_message(body: bytes | str) -> dict[str, Any]:
    message = body.decode() if isinstance(body, bytes) else body
    try:
        decoded = json.loads(message)
    except json.JSONDecodeError:
        return {"user_id": int(message)}
    if isinstance(decoded, dict):
        return decoded
    if isinstance(decoded, (int, str)) and not isinstance(decoded, bool):
        return {"user_id": int(decoded)}
    raise ValueError("RabbitMQ message must contain a JSON object or user ID")


class RabbitMQConnection:
    def __init__(self, url: str = RABBITMQ_URL, queue_name: str = "recommendations"):
        self.url = urlparse(url)
        self.queue_name = queue_name
        self.connection: BlockingConnection | None = None
        self.channel: BlockingChannel | None = None

    def connect(self) -> None:
        if self.url.username is None or self.url.password is None or self.url.hostname is None or self.url.port is None:
            raise ValueError("RabbitMQ URL must include username, password, host, and port")
        credentials = pika.PlainCredentials(self.url.username, self.url.password)
        parameters = pika.ConnectionParameters(
            host=self.url.hostname,
            port=self.url.port,
            credentials=credentials,
            virtual_host=self.url.path[1:] or "/",
            heartbeat=600,
            blocked_connection_timeout=300,
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name, durable=True, auto_delete=False)
        self.channel.basic_qos(prefetch_count=1)
        logging.info("RabbitMQ connection established")

    def close(self) -> None:
        if self.connection and self.connection.is_open:
            self.connection.close()
            logging.info("RabbitMQ connection closed")

    def send_message(self, message: dict, routing_key: str, correlation_id: str | None = None) -> None:
        if not self.channel:
            raise RuntimeError("RabbitMQ connection not established")

        properties = pika.BasicProperties(
            delivery_mode=2, content_type="application/json", correlation_id=correlation_id
        )

        self.channel.basic_publish(
            exchange="",
            routing_key=routing_key,
            body=json.dumps(message).encode(),
            properties=properties,
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
                        message=result, routing_key=properties.reply_to, correlation_id=properties.correlation_id
                    )
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logging.error(
                    "Message processing failed: request_id=%s error=%s",
                    properties.correlation_id,
                    e,
                )
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self.channel.basic_consume(queue=self.queue_name, on_message_callback=wrapped_callback, auto_ack=False)
        logging.info(f"Listening to queue: {self.queue_name}")
        self.channel.start_consuming()

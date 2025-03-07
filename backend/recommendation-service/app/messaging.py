import json
import pika
from urllib.parse import urlparse

from app.logger import log_time, logging
from app.config import RABBITMQ_URL


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
                blocked_connection_timeout=300
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue_name, durable=True)
        except Exception as e:
            logging.error(f"{log_time()} - Error connecting to RabbitMQ: {e}")
            raise

    def close(self):
        if self.connection:
            self.connection.close()
            logging.info(f"{log_time()} - Connection to RabbitMQ closed.")

    def send_message(self, message: dict):
        if not self.channel:
            raise Exception("Connection to RabbitMQ is not established")
        try:
            self.channel.queue_declare(queue=self.response_queue, durable=False)
            self.channel.basic_publish(
                exchange='',
                routing_key=self.response_queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)
            )
        except Exception as e:
            logging.error(f"{log_time()} - Error sending message: {e}")

    def receive_message(self, callback):
        if not self.channel:
            raise Exception("Connection to RabbitMQ is not established")

        def on_message(ch, method, properties, body):
            callback(json.loads(body))
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=on_message,
            auto_ack=True
        )
        self.channel.start_consuming()

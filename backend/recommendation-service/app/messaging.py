import pika
import json
from app.logger import log_time, logging
from app.config import RABBITMQ_URL


class RabbitMQConnection:
    def __init__(self, host: str = RABBITMQ_URL, queue_name: str = "default_queue"):
        self.host = host
        self.queue_name = queue_name
        self.connection = None
        self.channel = None

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(self.host))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            logging.info(f"{log_time()} - Connected to RabbitMQ server at {self.host} and queue {self.queue_name}")
        except Exception as e:
            logging.error(f"{log_time()} - Error connecting to RabbitMQ: {e}")

    def close(self):
        if self.connection:
            self.connection.close()
            logging.info(f"{log_time()} - Connection to RabbitMQ closed.")

    def send_message(self, message: dict):
        if not self.channel:
            raise Exception("Connection to RabbitMQ is not established. Call connect() first.")

        try:
            message_json = json.dumps(message)
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=message_json,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                )
            )
            logging.info(f"{log_time()} - Sent message: {message_json}")
        except Exception as e:
            logging.error(f"{log_time()} - Error sending message: {e}")

    def receive_message(self, callback):
        if not self.channel:
            raise Exception("Connection to RabbitMQ is not established. Call connect() first.")

        def on_message(ch, method, properties, body):
            message = json.loads(body)
            logging.info(f"{log_time()} - Received message: {message}")
            callback(message)

        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=on_message,
            auto_ack=True
        )
        logging.info(f"{log_time()} - Waiting for messages in queue: {self.queue_name}. To exit press CTRL+C.")
        self.channel.start_consuming()

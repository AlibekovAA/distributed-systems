import json
import pika
from urllib.parse import urlparse

from app.logger import logging
from app.config import RABBITMQ_URL
from app.database import get_db
from app.crud import get_recommendations_for_user


def process_message(ch, method, properties, body):
    try:
        logging.info(f"Received message: {body}, type: {type(body)}")
        logging.info(f"Full message properties: {vars(properties)}")
        logging.info(f"Method info: {vars(method)}")

        if isinstance(body, bytes):
            message = body.decode()
        else:
            message = body

        if isinstance(message, str):
            try:
                message_data = json.loads(message)
            except json.JSONDecodeError:
                message_data = {"user_id": int(message)}
        else:
            message_data = message

        user_id = message_data.get("user_id") or int(message)
        logging.info(f"Processing for user_id: {user_id}")

        with get_db() as db:
            recommendations = get_recommendations_for_user(db, user_id)
            response = {
                'user_id': user_id,
                'recommendations': recommendations
            }

            response_json = json.dumps(response)

            ch.basic_publish(
                exchange='',
                routing_key='recommendations_response',
                body=response_json,
                properties=pika.BasicProperties(
                    content_type='application/json',
                    message_id=str(user_id)
                )
            )

            ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logging.error(f"Error processing message: {e}")
        logging.exception("Full traceback:")


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

            self.channel.basic_qos(prefetch_count=1)
            logging.info("Successfully connected to RabbitMQ")

        except Exception as e:
            logging.error(f"Error connecting to RabbitMQ: {e}")
            raise

    def close(self):
        if self.connection:
            self.connection.close()
            logging.info("Connection to RabbitMQ closed.")

    def send_message(self, message: dict, routing_key: str = None, correlation_id: str = None):
        if not self.channel:
            raise Exception("Connection to RabbitMQ is not established")
        try:
            props = {
                'delivery_mode': 2,
                'content_type': 'application/json'
            }

            if correlation_id:
                props['correlation_id'] = correlation_id

            properties = pika.BasicProperties(**props)
            routing_key = routing_key or self.response_queue

            logging.info(f"Sending message to queue {routing_key} with correlation_id {correlation_id}")
            logging.info(f"Message content: {json.dumps(message, indent=2)}")

            self.channel.basic_publish(
                exchange='',
                routing_key=routing_key,
                body=json.dumps(message),
                properties=properties
            )
            logging.info("Message sent successfully")
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            raise

    def receive_message(self, callback):
        if not self.channel:
            raise Exception("Connection to RabbitMQ is not established")

        def on_message(ch, method, properties, body):
            try:
                logging.info(f"Received message with properties: {vars(properties)}")
                logging.info(f"Message body: {body}")

                if isinstance(body, bytes):
                    message = body.decode()
                else:
                    message = body

                if isinstance(message, str):
                    try:
                        message = json.loads(message)
                    except json.JSONDecodeError:
                        pass

                result = callback(message, properties)

                if result is not None and properties.reply_to:
                    logging.info(f"Sending response to {properties.reply_to} with correlation_id {properties.correlation_id}")
                    self.send_message(
                        message=result,
                        routing_key=properties.reply_to,
                        correlation_id=properties.correlation_id
                    )

                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as e:
                logging.error(f"Error processing message: {e}")
                logging.exception("Full traceback:")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=on_message,
            auto_ack=False
        )

        logging.info(f"Started consuming from queue: {self.queue_name}")
        self.channel.start_consuming()

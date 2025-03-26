import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL")
RABBITMQ_USER: str = os.getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD")
RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT: str = os.getenv("RABBITMQ_PORT")
RABBITMQ_URL: str = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"
SECRET_KEY: str = os.getenv("SECRET_KEY")
ALGORITHM: str = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "warning").upper()

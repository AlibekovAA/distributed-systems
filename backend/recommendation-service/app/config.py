import os

from dotenv import load_dotenv

load_dotenv()


def _required_env(key: str) -> str:
    if (value := os.getenv(key)) is None:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


DATABASE_URL = _required_env("DATABASE_URL")
RABBITMQ_URL = (
    f"amqp://{_required_env('RABBITMQ_USER')}:{_required_env('RABBITMQ_PASSWORD')}"
    f"@{_required_env('RABBITMQ_HOST')}:{_required_env('RABBITMQ_PORT')}/"
)
LOG_LEVEL = os.getenv("LOG_LEVEL", "warning").upper()

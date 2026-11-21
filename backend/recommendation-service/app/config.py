import os

from dotenv import load_dotenv

load_dotenv()


class _EnvConfig:
    @property
    def DATABASE_URL(self) -> str:
        return self._get_required("DATABASE_URL")

    @property
    def RABBITMQ_URL(self) -> str:
        return f"amqp://{self._get_required('RABBITMQ_USER')}:{self._get_required('RABBITMQ_PASSWORD')}@{self._get_required('RABBITMQ_HOST')}:{self._get_required('RABBITMQ_PORT')}/"

    @property
    def LOG_LEVEL(self) -> str:
        return os.getenv("LOG_LEVEL", "warning").upper()

    def _get_required(self, key: str) -> str:
        if (value := os.getenv(key)) is None:
            raise ValueError(f"Missing required environment variable: {key}")
        return value


_config = _EnvConfig()

DATABASE_URL = _config.DATABASE_URL
RABBITMQ_URL = _config.RABBITMQ_URL
LOG_LEVEL = _config.LOG_LEVEL

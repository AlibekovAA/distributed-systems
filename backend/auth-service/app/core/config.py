import os

from dotenv import load_dotenv

load_dotenv()


def _required_env(key: str) -> str:
    if (value := os.getenv(key)) is None:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


DATABASE_URL = _required_env("DATABASE_URL")
SECRET_KEY = _required_env("SECRET_KEY")
ALGORITHM = _required_env("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(_required_env("ACCESS_TOKEN_EXPIRE_MINUTES"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "warning").upper()
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip().lower()

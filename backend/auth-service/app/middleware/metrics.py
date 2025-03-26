from collections import defaultdict
from datetime import datetime

from fastapi import Request

from app.core.logger import logging

HTTP_STATUS_COUNTS = defaultdict(int)
REQUEST_COUNT = 0
START_TIME = datetime.now()


def get_version():
    try:
        with open("version.txt", "r") as f:
            for line in f:
                if line.startswith("auth-service="):
                    return line.strip().split("=")[1]
    except Exception as e:
        logging.error(f"Error when reading the version: {str(e)}")
        return "unknown"
    return "unknown"


SERVICE_VERSION = get_version()


async def metrics_middleware(request: Request, call_next):
    global REQUEST_COUNT
    REQUEST_COUNT += 1

    response = await call_next(request)

    HTTP_STATUS_COUNTS[response.status_code] += 1
    return response

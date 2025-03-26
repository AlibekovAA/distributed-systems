import time
from collections import defaultdict
from datetime import datetime

from fastapi import Request
from prometheus_client import Counter, Gauge, Histogram, Summary

from app.core.logger import logging

HTTP_STATUS_COUNTS = defaultdict(int)
REQUEST_COUNT = 0
START_TIME = datetime.now()

MEMORY_USAGE = Gauge(
    'auth_memory_usage_bytes',
    'Memory usage in bytes'
)

CPU_USAGE = Gauge(
    'auth_cpu_usage_percent',
    'CPU usage in percent'
)

LOGIN_COUNT = Counter(
    'auth_login_count_total',
    'Total number of logins'
)

PAGE_LOAD_TIME = Histogram(
    'auth_page_load_time_seconds',
    'Page load time in seconds',
    buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)
REQUEST_COUNT_PROM = Counter(
    'auth_http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint']
)

REQUEST_LATENCY = Summary(
    'auth_http_request_duration_seconds',
    'Duration of HTTP requests',
    ['method', 'endpoint']
)

ERROR_COUNT = Counter(
    'auth_http_errors_total',
    'Total number of HTTP errors',
    ['method', 'endpoint']
)

DB_REQUEST_LATENCY = Summary(
    'auth_db_request_duration_seconds',
    'Duration of database operations',
    ['operation']
)


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


def update_resource_metrics():
    import psutil
    process = psutil.Process()
    MEMORY_USAGE.set(process.memory_info().rss)
    CPU_USAGE.set(psutil.cpu_percent(interval=None))


async def metrics_middleware(request: Request, call_next):
    global REQUEST_COUNT
    REQUEST_COUNT += 1

    update_resource_metrics()

    start_time = time.time()
    response = await call_next(request)
    response_time = time.time() - start_time

    HTTP_STATUS_COUNTS[response.status_code] += 1

    if (request.url.path.endswith('.html') or request.url.path == '/' or
            request.url.path.endswith('/profile') or request.url.path.endswith('/login')):
        PAGE_LOAD_TIME.observe(response_time)
        logging.info(f"Page load time for {request.url.path}: {response_time:.4f}s")

    return response

import signal
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import start_http_server

from app.api import router
from app.core.database import engine
from app.core.logger import logging
from app.middleware.metrics import metrics_middleware
from models import user_model


def handle_sigterm(signum, frame):
    logging.info("Received SIGTERM signal")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global START_TIME
    START_TIME = datetime.now()

    start_http_server(8001)
    logging.info("Prometheus metrics server started on port 8001")
    yield
    logging.info("Application shutdown")

signal.signal(signal.SIGTERM, handle_sigterm)
user_model.Base.metadata.create_all(bind=engine)

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost",
    "http://localhost:80",
    "http://frontend",
    "http://nginx"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(metrics_middleware)
app.include_router(router, prefix="/auth", tags=["auth"])

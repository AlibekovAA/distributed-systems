from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import signal

from app.api import router
from app.core.database import engine
from app.core.logger import log_time, logging
from models import user_model


def handle_sigterm(signum, frame):
    logging.info(f"{log_time()} - Received SIGTERM signal")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    logging.info(f"{log_time()} - Application shutdown")


signal.signal(signal.SIGTERM, handle_sigterm)
user_model.Base.metadata.create_all(bind=engine)

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://frontend:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/auth", tags=["auth"])

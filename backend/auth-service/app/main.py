from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import start_http_server

from app.api import router
from app.core.logger import logging
from app.middleware.metrics import metrics_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_http_server(8001)
    logging.info("Prometheus metrics server started on port 8001")
    yield
    logging.info("Application shutdown")


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def request_id_middleware(request, call_next):
    request_id = request.headers.get("X-Request-ID", "").strip()
    if not request_id or len(request_id) > 128:
        request_id = uuid4().hex
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


origins = ["http://localhost", "http://localhost:80", "http://frontend", "http://nginx"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(metrics_middleware)
app.include_router(router, prefix="/auth", tags=["auth"])

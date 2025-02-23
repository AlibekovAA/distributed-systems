from fastapi import FastAPI
from app.api import router
from database import engine
from models import user_model


user_model.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(router, prefix="/auth", tags=["auth"])

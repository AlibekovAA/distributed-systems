from datetime import UTC, datetime, timedelta
from typing import cast

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from app.core.logger import logging
from jose import jwt
from models.user_model import User
from passlib.context import CryptContext
from sqlalchemy.orm import Session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _create_token(data: dict, expires_delta: timedelta, token_type: str) -> str:
    expire = datetime.now(UTC) + expires_delta
    to_encode = data.copy()
    to_encode.update({"exp": expire, "type": token_type})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(data: dict) -> str:
    return _create_token(data, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), "access")


def create_refresh_token(data: dict) -> str:
    return _create_token(data, timedelta(days=7), "refresh")


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, cast(str, user.hashed_password)):
        return None
    logging.info("User authenticated successfully")
    return user


def create_user(db: Session, email: str, password: str, name: str = "") -> User:
    hashed_password = get_password_hash(password)
    db_user = User(email=email, hashed_password=hashed_password, name=name)

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logging.info("New user created")
        return db_user
    except Exception:
        logging.error("Failed to create user")
        raise

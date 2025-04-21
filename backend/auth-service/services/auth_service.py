from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from app.core.logger import logging
from models.user_model import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _create_token(data: dict, expires_delta: timedelta) -> str:
    expire = datetime.utcnow() + expires_delta
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(data: dict) -> str:
    return _create_token(data, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(data: dict) -> str:
    return _create_token(data, timedelta(days=7))


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    logging.info(f"User authenticated successfully: {email}")
    return user


def create_user(db: Session, email: str, password: str, name: str = "") -> User:
    hashed_password = get_password_hash(password)
    db_user = User(email=email, hashed_password=hashed_password, name=name)

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logging.info(f"New user created: {email}")
        return db_user
    except Exception as e:
        logging.error(f"Failed to create user {email}: {str(e)}")
        raise

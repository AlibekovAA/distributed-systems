from datetime import datetime, timedelta

from passlib.context import CryptContext
from jose import jwt
from sqlalchemy.orm import Session

from models.user_model import User
from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.logger import logging

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user and verify_password(password, user.hashed_password):
        logging.info(f"User authenticated successfully: {email}")
        return user
    return None


def create_user(db: Session, email: str, password: str, name: str = "") -> User:
    hashed_password = get_password_hash(password)
    try:
        db_user = User(
            email=email,
            hashed_password=hashed_password,
            name=name
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logging.info(f"New user created: {email}")
        return db_user
    except Exception as e:
        logging.error(f"Failed to create user {email}: {str(e)}")
        raise

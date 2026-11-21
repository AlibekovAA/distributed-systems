from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from models.user_model import User
from sqlalchemy.orm import Session

from app.core.config import ALGORITHM, SECRET_KEY
from app.core.database import get_db_dependency
from app.core.logger import logging

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
token_dependency = Depends(oauth2_scheme)
db_dependency = Depends(get_db_dependency)


def get_current_user(token: str = token_dependency, db: Session = db_dependency):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email or payload.get("type") != "access":
            raise credentials_exception
    except JWTError:
        logging.warning("Token validation failed: JWTError")
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if not user:
        logging.warning("Token validation failed: user not found")
        raise credentials_exception

    logging.info("User validated")
    return user

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.config import SECRET_KEY, ALGORITHM
from app.core.database import get_db
from models.user_model import User
from app.core.logger import logging

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
token_dependency = Depends(oauth2_scheme)
db_dependency = Depends(get_db)


def get_current_user(token: str = token_dependency, db: Session = db_dependency):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
    except JWTError:
        logging.warning("Token validation failed: JWTError")
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        logging.warning(f"Token validation failed: User not found - {email}")
        raise credentials_exception
    logging.info(f"User validated: {user.email}")
    return user

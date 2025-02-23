from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from config import SECRET_KEY, ALGORITHM
from database import get_db
from models.user_model import User

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
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

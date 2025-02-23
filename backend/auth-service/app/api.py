from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from fastapi import status

from models.user_model import User
from models.user_schemas import UserCreate, UserLogin, Token
from services.auth_service import authenticate_user, create_user, create_access_token, create_refresh_token
from database import get_db
from app.auth import get_current_user
from config import SECRET_KEY, ALGORITHM

router = APIRouter()

db_dependency = Depends(get_db)
current_user_dependency = Depends(get_current_user)


@router.post("/register", response_model=User)
def register(user: UserCreate, db: Session = db_dependency):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return create_user(db=db, email=user.email, password=user.password, full_name=user.full_name)


@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = db_dependency):
    db_user = authenticate_user(db=db, email=user.email, password=user.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": db_user.email})
    refresh_token = create_refresh_token(data={"sub": db_user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get("/profile", response_model=User)
def get_profile(db: Session = db_dependency, current_user: User = current_user_dependency):
    return current_user


@router.post("/token/refresh", response_model=Token)
def refresh_token(refresh_token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    access_token = create_access_token(data={"sub": email})
    return {"access_token": access_token, "token_type": "bearer"}

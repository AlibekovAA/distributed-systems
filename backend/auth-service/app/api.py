from sqlalchemy.orm import Session
from jose import jwt, JWTError
from fastapi import (APIRouter,
                     Depends,
                     HTTPException,
                     status)

from models.user_schemas import (UserCreate,
                                 UserLogin,
                                 Token,
                                 User)
from services.auth_service import (authenticate_user,
                                   create_user,
                                   create_access_token,
                                   create_refresh_token)
from database import get_db
from app.auth import get_current_user
from config import SECRET_KEY, ALGORITHM
from logger import log_time, logging

router = APIRouter()

db_dependency = Depends(get_db)
current_user_dependency = Depends(get_current_user)


@router.post("/register", response_model=User)
def register(user: UserCreate, db: Session = db_dependency):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        logging.info(f"{log_time()} - Registration failed: Email already registered - {user.email}")
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = create_user(
        db=db,
        email=user.email,
        password=user.password,
        name=user.name
    )
    logging.info(f"{log_time()} - User registered: {new_user.email}")
    return new_user


@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = db_dependency):
    db_user = authenticate_user(db=db, email=user.email, password=user.password)
    if not db_user:
        logging.warning(f"{log_time()} - Login failed: Invalid credentials for {user.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": db_user.email})
    refresh_token = create_refresh_token(data={"sub": db_user.email})
    logging.info(f"{log_time()} - User logged in: {db_user.email}")
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get("/profile", response_model=User)
def get_profile(db: Session = db_dependency, current_user: User = current_user_dependency):
    logging.info(f"{log_time()} - User profile accessed: {current_user.email}")
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
            logging.warning(f"{log_time()} - Token refresh failed: No email found in token")
            raise credentials_exception
    except JWTError:
        logging.warning(f"{log_time()} - Token refresh failed: JWTError")
        raise credentials_exception

    access_token = create_access_token(data={"sub": email})
    logging.info(f"{log_time()} - Access token refreshed for: {email}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/health")
async def health_check():
    return {"status": "Auth service started"}

from jose import jwt, JWTError
from fastapi import (APIRouter,
                     HTTPException,
                     status,
                     Request)
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List

from models.user_schemas import (UserCreate,
                                 UserLogin,
                                 Token,
                                 User,
                                 PasswordChange,
                                 BalanceUpdate,
                                 BalanceResponse,
                                 UserPreferenceCreate)
from models.user_model import User as UserModel
from models.preference_model import UserPreference
from models.category_model import Category
from services.auth_service import (authenticate_user,
                                   create_user,
                                   create_access_token,
                                   create_refresh_token,
                                   verify_password,
                                   get_password_hash)
from app.core.database import get_db
from app.auth import get_current_user, token_dependency, db_dependency
from app.core.config import SECRET_KEY, ALGORITHM
from app.core.logger import logging
import time
from prometheus_client import Counter, Summary

REQUEST_COUNT = Counter(
    'auth_http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint']
)

REQUEST_LATENCY = Summary(
    'auth_http_request_duration_seconds',
    'Duration of HTTP requests',
    ['method', 'endpoint']
)
ERROR_COUNT = Counter(
    'auth_http_errors_total',
    'Total number of HTTP errors',
    ['method', 'endpoint']
)

DB_REQUEST_LATENCY = Summary(
    'auth_db_request_duration_seconds',
    'Duration of database operations',
    ['operation']
)

router = APIRouter()

logging.info("API router initialized")


@router.post("/register", response_model=User)
def register(user: UserCreate, request: Request):
    REQUEST_COUNT.labels('POST', '/register').inc()
    start_time = time.time()
    with get_db() as db:
        db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
        if db_user:
            ERROR_COUNT.labels('POST', '/register').inc()
            logging.info(f"Registration failed: Email already registered - {user.email}")
            raise HTTPException(status_code=400, detail="Email already registered")

        new_user = create_user(
            db=db,
            email=user.email,
            password=user.password,
            name=user.name
        )
        logging.info(f"User registered: {new_user.email}")
        REQUEST_LATENCY.labels('POST', '/register').observe(time.time() - start_time)
        return new_user


@router.post("/login", response_model=Token)
def login(user: UserLogin, request: Request):
    REQUEST_COUNT.labels('POST', '/login').inc()
    start_time = time.time()
    with get_db() as db:
        db_user = authenticate_user(db=db, email=user.email, password=user.password)
        if not db_user:
            ERROR_COUNT.labels('POST', '/login').inc()
            logging.warning(f"Login failed: Invalid credentials for {user.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = create_access_token(data={"sub": db_user.email})
        refresh_token = create_refresh_token(data={"sub": db_user.email})
        logging.info(f"User logged in: {db_user.email}")
        REQUEST_LATENCY.labels('POST', '/login').observe(time.time() - start_time)
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get("/profile", response_model=User)
def get_profile(
    request: Request,
    token: str = token_dependency,
    db: Session = db_dependency
):
    REQUEST_COUNT.labels('GET', '/profile').inc()
    start_time = time.time()
    with get_db() as db:
        current_user = get_current_user(token, db)
        logging.info(f"User profile accessed: {current_user.email}")
        REQUEST_LATENCY.labels('GET', '/profile').observe(time.time() - start_time)
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
        if datetime.fromtimestamp(payload["exp"], tz=datetime.UTC) < datetime.now(datetime.UTC):
            raise HTTPException(status_code=401, detail="Refresh token expired")
        email: str = payload.get("sub")
    except JWTError:
        logging.warning(f"Token refresh failed: JWTError")
        raise credentials_exception

    access_token = create_access_token(data={"sub": email})
    logging.info(f"Access token refreshed for: {email}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/health")
async def health_check():
    return {"status": "Auth service started"}


@router.post("/change-password")
def change_password(password_data: PasswordChange,  token: str = token_dependency,db: Session = db_dependency):
    REQUEST_COUNT.labels('POST', '/change-password').inc()
    start_time = time.time()
    with get_db() as db:
        current_user = get_current_user(token, db)

        if not verify_password(password_data.old_password, current_user.hashed_password):
            ERROR_COUNT.labels('POST', '/change-password').inc()
            logging.warning(f"Password change failed: Invalid old password for {current_user.email}")
            raise HTTPException(status_code=400, detail="Invalid old password")

        if len(password_data.new_password) < 8:
            ERROR_COUNT.labels('POST', '/change-password').inc()
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")

        current_user.hashed_password = get_password_hash(password_data.new_password)
        db.commit()

        logging.info(f"Password changed successfully for {current_user.email}")
        REQUEST_LATENCY.labels('POST', '/change-password').observe(time.time() - start_time)
        return {"message": "Password changed successfully"}


@router.post("/add-balance", response_model=BalanceResponse)
def add_balance(balance_data: BalanceUpdate,  token: str = token_dependency,db: Session = db_dependency):
    REQUEST_COUNT.labels('POST', '/add-balance').inc()
    start_time = time.time()
    with get_db() as db:
        current_user = get_current_user(token, db)

        if balance_data.amount <= 0:
            ERROR_COUNT.labels('POST', '/add-balance').inc()
            raise HTTPException(status_code=400, detail="Amount must be positive")

        current_user.balance += balance_data.amount
        db.commit()
        db.refresh(current_user)

        logging.info(f"Balance updated for {current_user.email}: +{balance_data.amount}, new balance: {current_user.balance}")
        REQUEST_LATENCY.labels('POST', '/add-balance').observe(time.time() - start_time)
        return {"success": True, "new_balance": current_user.balance}


@router.get("/preferences/check")
def check_preferences(token: str = token_dependency,db: Session = db_dependency):
    REQUEST_COUNT.labels('GET', '/preferences/check').inc()
    start_time = time.time()
    try:
        with get_db() as db:
            current_user = get_current_user(token, db)
            has_preferences = db.query(UserPreference).filter(
                UserPreference.user_id == current_user.id
            ).first() is not None

            if has_preferences:
                logging.info(f"User {current_user.email} preferences checked: has preferences")
                return {"has_preferences": True}

            categories = db.query(Category).all()
            logging.info(f"User {current_user.email} preferences checked: needs to fill preferences")
            REQUEST_LATENCY.labels('GET', '/preferences/check').observe(time.time() - start_time)
            return {
                "has_preferences": False,
                "categories": [{"id": c.id, "name": c.name} for c in categories]
            }
    except Exception as e:
        ERROR_COUNT.labels('GET', '/preferences/check').inc()
        logging.error(f"Error checking preferences: {str(e)}")
        raise


@router.post("/preferences/save")
def save_preferences(preferences: List[UserPreferenceCreate],  token: str = token_dependency,db: Session = db_dependency):
    REQUEST_COUNT.labels('POST', '/preferences/save').inc()
    start_time = time.time()
    with get_db() as db:
        current_user = get_current_user(token, db)

        for pref in preferences:
            category = db.query(Category).filter(Category.id == pref.category_id).first()
            if not category:
                continue

            db_preference = UserPreference(
                user_id=current_user.id,
                preference_name=category.name,
                preference_value=str(pref.score)
            )
            db.add(db_preference)

        db.commit()
        REQUEST_LATENCY.labels('POST', '/preferences/save').observe(time.time() - start_time)
        return {"success": True}

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

REQUEST_COUNT = Counter('request_count', 'Total number of requests')
REQUEST_LATENCY = Summary('request_latency_seconds', 'Time spent processing request')
ERROR_COUNT = Counter('error_count', 'Total number of errors')

router = APIRouter()

logging.info("API router initialized")


@router.post("/register", response_model=User)
def register(user: UserCreate, request: Request):
    REQUEST_COUNT.inc()  
    start_time = time.time()
    with get_db() as db:
        db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
        if db_user:
            ERROR_COUNT.inc() 
            logging.info(f"Registration failed: Email already registered - {user.email}")
            raise HTTPException(status_code=400, detail="Email already registered")

        new_user = create_user(
            db=db,
            email=user.email,
            password=user.password,
            name=user.name
        )
        logging.info(f"User registered: {new_user.email}")
        REQUEST_LATENCY.observe(time.time() - start_time) 
        return new_user

@router.post("/login", response_model=Token)
def login(user: UserLogin, request: Request):
    REQUEST_COUNT.inc()
    start_time = time.time()
    with get_db() as db:
        db_user = authenticate_user(db=db, email=user.email, password=user.password)
        if not db_user:
            ERROR_COUNT.inc()
            logging.warning(f"Login failed: Invalid credentials for {user.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = create_access_token(data={"sub": db_user.email})
        refresh_token = create_refresh_token(data={"sub": db_user.email})
        logging.info(f"User logged in: {db_user.email}")
        REQUEST_LATENCY.observe(time.time() - start_time)
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get("/profile", response_model=User)
def get_profile(
    request: Request,
    token: str = token_dependency,
    db: Session = db_dependency
):
    REQUEST_COUNT.inc()
    start_time = time.time()
    with get_db() as db:
        current_user = get_current_user(token, db)
        logging.info(f"User profile accessed: {current_user.email}")
        REQUEST_LATENCY.observe(time.time() - start_time)
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
        if email is None:
            logging.warning(f"Token refresh failed: No email found in token")
            raise credentials_exception
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
    REQUEST_COUNT.inc()
    start_time = time.time()
    with get_db() as db:
        current_user = get_current_user(token, db)

        if not verify_password(password_data.old_password, current_user.hashed_password):
            ERROR_COUNT.inc()
            logging.warning(f"Password change failed: Invalid old password for {current_user.email}")
            raise HTTPException(status_code=400, detail="Invalid old password")

        if len(password_data.new_password) < 8:
            ERROR_COUNT.inc()
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")

        current_user.hashed_password = get_password_hash(password_data.new_password)
        db.commit()

        logging.info(f"Password changed successfully for {current_user.email}")
        REQUEST_LATENCY.observe(time.time() - start_time)
        return {"message": "Password changed successfully"}


@router.post("/add-balance", response_model=BalanceResponse)
def add_balance(balance_data: BalanceUpdate,  token: str = token_dependency,db: Session = db_dependency):
    REQUEST_COUNT.inc()
    start_time = time.time()
    with get_db() as db:
        current_user = get_current_user(token, db)

        if balance_data.amount <= 0:
            ERROR_COUNT.inc()
            raise HTTPException(status_code=400, detail="Amount must be positive")

        current_user.balance += balance_data.amount
        db.commit()
        db.refresh(current_user)

        logging.info(f"Balance updated for {current_user.email}: +{balance_data.amount}, new balance: {current_user.balance}")
        REQUEST_LATENCY.observe(time.time() - start_time)
        return {"success": True, "new_balance": current_user.balance}


@router.get("/preferences/check")
def check_preferences( token: str = token_dependency,db: Session = db_dependency):
    REQUEST_COUNT.inc()
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
            REQUEST_LATENCY.observe(time.time() - start_time)
            return {
                "has_preferences": False,
                "categories": [{"id": c.id, "name": c.name} for c in categories]
            }
    except Exception as e:
        ERROR_COUNT.inc()
        logging.error(f"Error checking preferences: {str(e)}")
        raise


@router.post("/preferences/save")
def save_preferences(preferences: List[UserPreferenceCreate],  token: str = token_dependency,db: Session = db_dependency):
    REQUEST_COUNT.inc()
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
        REQUEST_LATENCY.observe(time.time() - start_time)
        return {"success": True}

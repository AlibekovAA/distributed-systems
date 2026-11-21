import socket
from typing import List, cast

from fastapi import APIRouter, HTTPException, status
from jose import JWTError, jwt
from models.category_model import Category
from models.preference_model import UserPreference
from models.user_model import User as UserModel
from models.user_schemas import (
    BalanceResponse,
    BalanceUpdate,
    PasswordChange,
    RefreshTokenRequest,
    Token,
    User,
    UserCreate,
    UserLogin,
    UserPreferenceCreate,
)
from services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user,
    get_password_hash,
    verify_password,
)
from sqlalchemy.orm import Session

from app.auth import db_dependency, get_current_user, token_dependency
from app.core.config import ADMIN_EMAIL, ALGORITHM, SECRET_KEY
from app.core.logger import logging
from app.middleware.metrics import LOGIN_COUNT, get_metrics_snapshot

router = APIRouter()

logging.info("API router initialized")


@router.post("/register", response_model=User)
def register(user: UserCreate, db: Session = db_dependency):
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user:
        logging.info("Registration failed: email already registered")
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = create_user(db=db, email=user.email, password=user.password, name=user.name)
    logging.info("User registered")
    return new_user


@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = db_dependency):
    db_user = authenticate_user(db=db, email=user.email, password=user.password)
    if not db_user:
        logging.warning("Login failed: invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    role = "admin" if db_user.email.lower() == ADMIN_EMAIL else "user"
    token_data = {"sub": db_user.email, "role": role}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    LOGIN_COUNT.inc()
    logging.info("User logged in")
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get("/profile", response_model=User)
def get_profile(token: str = token_dependency, db: Session = db_dependency):
    current_user = get_current_user(token, db)
    logging.info("User profile accessed")
    return current_user


@router.post("/token/refresh", response_model=Token)
def refresh_token(request: RefreshTokenRequest, db: Session = db_dependency):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email or payload.get("type") != "refresh":
            raise credentials_exception
    except JWTError:
        logging.warning("Token refresh failed: JWTError")
        raise credentials_exception

    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        raise credentials_exception
    role = "admin" if user.email.lower() == ADMIN_EMAIL else "user"
    access_token = create_access_token(data={"sub": user.email, "role": role})
    logging.info("Access token refreshed")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/health")
async def health_check():
    hostname = socket.gethostname()
    return {"status": "Auth service started", "instance": hostname}


@router.post("/change-password")
def change_password(password_data: PasswordChange, token: str = token_dependency, db: Session = db_dependency):
    current_user = get_current_user(token, db)
    if not verify_password(password_data.old_password, current_user.hashed_password):
        logging.warning("Password change failed: invalid old password")
        raise HTTPException(status_code=400, detail="Invalid old password")
    if len(password_data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    logging.info("Password changed successfully")
    return {"message": "Password changed successfully"}


@router.post("/add-balance", response_model=BalanceResponse)
def add_balance(balance_data: BalanceUpdate, token: str = token_dependency, db: Session = db_dependency):
    current_user = get_current_user(token, db)
    if balance_data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    current_user.balance += balance_data.amount
    db.commit()
    db.refresh(current_user)
    logging.info("Balance updated")
    return {"success": True, "new_balance": current_user.balance}


@router.get("/preferences/check")
def check_preferences(token: str = token_dependency, db: Session = db_dependency):
    current_user = get_current_user(token, db)
    has_preferences = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first() is not None
    if has_preferences:
        logging.info("User preferences checked: preferences exist")
        return {"has_preferences": True}
    categories = db.query(Category).all()
    logging.info("User preferences checked: preferences required")
    return {"has_preferences": False, "categories": [{"id": c.id, "name": c.name} for c in categories]}


@router.post("/preferences/save")
def save_preferences(
    preferences: List[UserPreferenceCreate], token: str = token_dependency, db: Session = db_dependency
):
    current_user = get_current_user(token, db)
    category_ids = {pref.category_id for pref in preferences}
    categories_by_id: dict[int, Category] = {
        cast(int, category.id): category for category in db.query(Category).filter(Category.id.in_(category_ids)).all()
    }
    for pref in preferences:
        category = categories_by_id.get(pref.category_id)
        if category:
            db.add(
                UserPreference(user_id=current_user.id, preference_name=category.name, preference_value=str(pref.score))
            )
    db.commit()
    return {"success": True}


@router.get("/metrics")
async def get_metrics():
    return get_metrics_snapshot()

from jose import jwt, JWTError
from fastapi import (APIRouter,
                     HTTPException,
                     status,
                     Request)
from datetime import datetime
from sqlalchemy.orm import Session

from models.user_schemas import (UserCreate,
                                 UserLogin,
                                 Token,
                                 User,
                                 PasswordChange,
                                 BalanceUpdate,
                                 BalanceResponse)
from models.user_model import User as UserModel
from services.auth_service import (authenticate_user,
                                   create_user,
                                   create_access_token,
                                   create_refresh_token,
                                   verify_password,
                                   get_password_hash)
from app.core.database import get_db
from app.auth import get_current_user, token_dependency, db_dependency
from app.core.config import SECRET_KEY, ALGORITHM
from app.core.logger import log_time, logging

router = APIRouter()


@router.post("/register", response_model=User)
def register(user: UserCreate, request: Request):
    with get_db() as db:
        db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
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
def login(user: UserLogin, request: Request):
    with get_db() as db:
        db_user = authenticate_user(db=db, email=user.email, password=user.password)
        if not db_user:
            logging.warning(f"{log_time()} - Login failed: Invalid credentials for {user.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = create_access_token(data={"sub": db_user.email})
        refresh_token = create_refresh_token(data={"sub": db_user.email})
        logging.info(f"{log_time()} - User logged in: {db_user.email}")
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get("/profile", response_model=User)
def get_profile(
    request: Request,
    token: str = token_dependency,
    db: Session = db_dependency
):
    with get_db() as db:
        current_user = get_current_user(token, db)
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
        if datetime.fromtimestamp(payload["exp"], tz=datetime.UTC) < datetime.now(datetime.UTC):
            raise HTTPException(status_code=401, detail="Refresh token expired")
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


@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    token: str = token_dependency,
    db: Session = db_dependency
):
    with get_db() as db:
        current_user = get_current_user(token, db)

        if not verify_password(password_data.old_password, current_user.hashed_password):
            logging.warning(f"{log_time()} - Password change failed: Invalid old password for {current_user.email}")
            raise HTTPException(status_code=400, detail="Invalid old password")

        if len(password_data.new_password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")

        current_user.hashed_password = get_password_hash(password_data.new_password)
        db.commit()

        logging.info(f"{log_time()} - Password changed successfully for {current_user.email}")
        return {"message": "Password changed successfully"}


@router.post("/add-balance", response_model=BalanceResponse)
def add_balance(
    balance_data: BalanceUpdate,
    token: str = token_dependency,
    db: Session = db_dependency
):
    with get_db() as db:
        current_user = get_current_user(token, db)

        if balance_data.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")

        current_user.balance += balance_data.amount
        db.commit()
        db.refresh(current_user)

        logging.info(f"{log_time()} - Balance updated for {current_user.email}: +{balance_data.amount}, new balance: {current_user.balance}")
        return {"success": True, "new_balance": current_user.balance}

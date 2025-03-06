from pydantic import BaseModel, EmailStr, Field
from pydantic import ConfigDict
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str = None


class User(BaseModel):
    id: int
    email: str
    name: str
    balance: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class BalanceUpdate(BaseModel):
    amount: int


class BalanceResponse(BaseModel):
    success: bool
    new_balance: int


class UserPreferenceCreate(BaseModel):
    category_id: int
    score: int = Field(..., ge=1, le=10)


class Category(BaseModel):
    id: int
    name: str

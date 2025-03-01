from pydantic import BaseModel, EmailStr, Field


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
    email: EmailStr
    name: str
    balance: int = 0

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class BalanceUpdate(BaseModel):
    amount: int


class BalanceResponse(BaseModel):
    success: bool
    new_balance: int

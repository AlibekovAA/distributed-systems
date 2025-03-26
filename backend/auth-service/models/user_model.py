from sqlalchemy import BigInteger, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True)
    hashed_password = Column(String, nullable=False)
    name = Column(String(255), nullable=False)
    balance = Column(BigInteger, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    preference_name = Column(String(255), nullable=False)
    preference_value = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

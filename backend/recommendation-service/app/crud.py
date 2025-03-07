from sqlalchemy.orm import Session

from app.models import History, UserPreferences, Product


def get_order_history_by_user_id(db: Session, user_id: int):
    return db.query(History).filter(History.user_id == user_id).all()


def get_user_preferences_by_user_id(db: Session, user_id: int):
    return db.query(UserPreferences).filter(UserPreferences.user_id == user_id).all()


def get_recommendations_for_user(db: Session, user_id: int):
    products = db.query(Product).order_by(Product.name.asc()).all()
    return [product.to_dict() for product in products]

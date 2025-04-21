from sqlalchemy.orm import Session

from app.logger import logging
from app.models import History, Product, UserPreferences
from app.recommendation_engine import RecommendationEngine


def get_recommendations_for_user(db: Session, user_id: int) -> list[dict]:
    recommendations = RecommendationEngine(db, user_id).get_recommendations()
    return [
        {**product.to_dict(), 'similarity_score': score}
        for product, score in recommendations
    ]


def update_user_preferences(db: Session, user_id: int) -> None:
    """Update user preferences based on purchase history."""
    logging.info(f"Updating preferences for user {user_id}")

    history = db.query(History).filter(History.user_id == user_id).all()
    if not history:
        logging.info(f"No purchase history for user {user_id}")
        return

    category_counts = {}
    for purchase in history:
        product = db.query(Product).get(purchase.product_id)
        if product:
            for category in product.categories:
                category_counts[category.name] = category_counts.get(category.name, 0) + 1

    if not category_counts:
        return

    max_count = max(category_counts.values())
    normalized_prefs = {
        category: (count / max_count) * 10.0
        for category, count in category_counts.items()
    }

    existing_prefs = {
        pref.preference_name: pref
        for pref in db.query(UserPreferences)
            .filter(UserPreferences.user_id == user_id)
            .filter(UserPreferences.preference_name.in_(normalized_prefs.keys()))
            .all()
    }

    for category, value in normalized_prefs.items():
        if category in existing_prefs:
            existing_prefs[category].preference_value = value
        else:
            db.add(UserPreferences(
                user_id=user_id,
                preference_name=category,
                preference_value=value
            ))

    try:
        db.commit()
        logging.info(f"Updated preferences for user {user_id}: {normalized_prefs}")
    except Exception as e:
        db.rollback()
        logging.error(f"Error updating preferences: {e}")
        raise

from sqlalchemy.orm import Session

from app.logger import logging
from app.models import History, Product, UserPreferences
from app.recommendation_engine import RecommendationEngine


def get_recommendations_for_user(db: Session, user_id: int):
    engine = RecommendationEngine(db, user_id)
    recommendations = engine.get_recommendations()

    result = []
    for product, score in recommendations:
        product_dict = product.to_dict()
        product_dict['similarity_score'] = score
        result.append(product_dict)

    return result


def update_user_preferences(db: Session, user_id: int):
    logging.info(f"Updating preferences for user {user_id}")

    history = (
        db.query(History)
        .filter(History.user_id == user_id)
        .all()
    )

    if not history:
        logging.info(f"No purchase history for user {user_id}")
        return

    category_counts = {}
    total_purchases = 0

    for purchase in history:
        product = db.query(Product).filter(Product.id == purchase.product_id).first()
        if product:
            for category in product.categories:
                if category.name not in category_counts:
                    category_counts[category.name] = 0
                category_counts[category.name] += 1
                total_purchases += 1

    if not total_purchases:
        return

    max_count = max(category_counts.values())
    normalized_preferences = {
        category: (count / max_count) * 10.0
        for category, count in category_counts.items()
    }

    for category, value in normalized_preferences.items():
        preference = (
            db.query(UserPreferences)
            .filter(
                UserPreferences.user_id == user_id,
                UserPreferences.preference_name == category
            )
            .first()
        )

        if preference:
            preference.preference_value = value
        else:
            preference = UserPreferences(
                user_id=user_id,
                preference_name=category,
                preference_value=value
            )
            db.add(preference)

    try:
        db.commit()
        logging.info(f"Successfully updated preferences for user {user_id}: {normalized_preferences}")
    except Exception as e:
        db.rollback()
        logging.error(f"Error updating preferences: {e}")
        raise

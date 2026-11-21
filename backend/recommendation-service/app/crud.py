from typing import Any, cast

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.logger import logging
from app.models import Category, History, ProductCategory, UserPreferences
from app.recommendation_engine import RecommendationEngine


def get_recommendations_for_user(db: Session, user_id: int) -> list[dict]:
    recommendations = RecommendationEngine(db, user_id).get_recommendations()
    return [{**product.to_dict(), "similarity_score": score} for product, score in recommendations]


def update_user_preferences(db: Session, user_id: int) -> None:
    """Update user preferences based on purchase history."""
    logging.info("Updating user preferences")

    category_rows = cast(
        list[tuple[Any, int]],
        db.query(Category.name, func.count(History.id))
        .join(ProductCategory, ProductCategory.product_id == History.product_id)
        .join(Category, Category.id == ProductCategory.category_id)
        .filter(History.user_id == user_id)
        .group_by(Category.name)
        .all(),
    )
    category_counts: dict[str, int] = {cast(str, category): count for category, count in category_rows}

    if not category_counts:
        return

    max_count = max(category_counts.values())
    normalized_prefs = {category: (count / max_count) * 10.0 for category, count in category_counts.items()}

    existing_prefs: dict[str, UserPreferences] = {
        cast(str, pref.preference_name): pref
        for pref in db.query(UserPreferences)
        .filter(UserPreferences.user_id == user_id)
        .filter(UserPreferences.preference_name.in_(normalized_prefs.keys()))
        .all()
    }

    for category, value in normalized_prefs.items():
        if category in existing_prefs:
            preference = cast(Any, existing_prefs[category])
            preference.preference_value = str(value)
        else:
            db.add(UserPreferences(user_id=user_id, preference_name=category, preference_value=str(value)))

    db.flush()
    logging.info("User preferences updated")

from typing import List, Tuple
from sqlalchemy.orm import Session

from app.models import History, UserPreferences, Product
from app.logger import logging, log_time


class RecommendationEngine:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.history = self._get_user_history()
        self.preferences = self._get_user_preferences()

    def _get_user_history(self) -> List[History]:
        return self.db.query(History).filter(History.user_id == self.user_id).all()

    def _get_user_preferences(self) -> List[UserPreferences]:
        return self.db.query(UserPreferences).filter(
            UserPreferences.user_id == self.user_id
        ).all()

    def _calculate_category_weights(self) -> dict:
        category_counts = {}
        for history_item in self.history:
            for category in history_item.product.categories:
                category_counts[category.id] = category_counts.get(category.id, 0) + 1

        total = sum(category_counts.values()) if category_counts else 1
        return {k: v/total for k, v in category_counts.items()}

    def _calculate_preference_score(self, product: Product) -> float:
        score = 1.0

        for pref in self.preferences:
            if any(cat.name == pref.preference_name for cat in product.categories):
                score *= float(pref.preference_value) / 10.0

        return score

    def _calculate_similarity_score(self, product: Product) -> float:
        category_weights = self._calculate_category_weights()

        category_score = 0
        if product.categories:
            category_scores = [category_weights.get(cat.id, 0) for cat in product.categories]
            category_score = sum(category_scores) / len(category_scores)

        preference_score = self._calculate_preference_score(product)
        availability_score = 1.0 if product.quantity > 0 else 0.1

        final_score = (
            preference_score * 0.5 +
            category_score * 0.4 +
            availability_score * 0.1
        )

        return final_score

    def get_recommendations(self) -> List[Tuple[Product, float]]:
        try:
            all_products = self.db.query(Product).all()

            product_scores = [
                (product, self._calculate_similarity_score(product))
                for product in all_products
            ]

            sorted_recommendations = sorted(
                product_scores,
                key=lambda x: x[1],
                reverse=True
            )

            return sorted_recommendations

        except Exception as e:
            logging.error(f"{log_time()} - Error generating recommendations: {e}")
            return []

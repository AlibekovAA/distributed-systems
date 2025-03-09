from typing import List, Tuple, Dict
from sqlalchemy.orm import Session, selectinload
from app.models import History, UserPreferences, Product
from app.logger import logging, log_time


class RecommendationEngine:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self._history = None
        self._category_weights = None
        self._preferences = None

    def _get_user_history(self) -> List[History]:
        if self._history is None:
            self._history = (
                self.db.query(History)
                .filter(History.user_id == self.user_id)
                .options(selectinload(History.product).selectinload(Product.categories))
                .all()
            )
        return self._history

    def _get_user_preferences(self) -> Dict[str, float]:
        if self._preferences is None:
            preferences = (
                self.db.query(UserPreferences)
                .filter(UserPreferences.user_id == self.user_id)
                .all()
            )
            self._preferences = {pref.preference_name: float(pref.preference_value) / 10.0 for pref in preferences}
        return self._preferences

    def _calculate_category_weights(self) -> Dict[int, float]:
        if self._category_weights is not None:
            return self._category_weights

        category_counts = {}
        history = self._get_user_history()

        for history_item in history:
            for category in history_item.product.categories:
                category_counts[category.id] = category_counts.get(category.id, 0) + 1

        total = sum(category_counts.values()) or 1
        self._category_weights = {k: v / total for k, v in category_counts.items()}
        return self._category_weights

    def _calculate_preference_score(self, product: Product) -> float:
        preferences = self._get_user_preferences()
        return max(
            (preferences.get(cat.name, 0) for cat in product.categories),
            default=0.1
        )

    def _calculate_similarity_score(self, product: Product) -> float:
        category_weights = self._calculate_category_weights()

        category_scores = [category_weights.get(cat.id, 0) for cat in product.categories]
        category_score = sum(category_scores) / len(category_scores) if category_scores else 0

        preference_score = self._calculate_preference_score(product)
        availability_score = 1.0 if product.quantity > 0 else 0.1

        return preference_score * 0.5 + category_score * 0.4 + availability_score * 0.1

    def get_recommendations(self) -> List[Tuple[Product, float]]:
        try:
            all_products = (
                self.db.query(Product)
                .options(selectinload(Product.categories))
                .all()
            )

            product_scores = [
                (product, self._calculate_similarity_score(product))
                for product in all_products
            ]

            return sorted(product_scores, key=lambda x: x[1], reverse=True)

        except Exception as e:
            logging.error(f"{log_time()} - Error generating recommendations: {e}")
            raise RuntimeError("Failed to generate recommendations") from e

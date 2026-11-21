from math import sqrt
from typing import Any, Dict, List, Tuple, cast

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.logger import logging
from app.models import History, Product, UserPreferences


class RecommendationEngine:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self._preferences_cache: dict[str, float] | None = None
        logging.debug("Recommendation engine initialized")

    def _get_user_preferences(self) -> Dict[str, float]:
        if self._preferences_cache is None:
            prefs = self.db.query(UserPreferences).filter(UserPreferences.user_id == self.user_id).all()
            self._preferences_cache = {
                cast(str, p.preference_name): float(cast(str, p.preference_value)) for p in prefs
            }
        return self._preferences_cache

    def _calculate_preference_score(self, product: Product) -> float:
        prefs = self._get_user_preferences()
        if not prefs:
            return 0.0

        return max((prefs.get(category.name, 0.0) for category in product.categories), default=0.0)

    def _get_collaborative_scores(self) -> Dict[int, float]:
        similar_users = self._find_similar_users()
        if not similar_users:
            return {}

        score_rows = cast(
            list[tuple[Any, Any]],
            self.db.query(History.product_id, func.count(History.id))
            .filter(History.user_id.in_(similar_users))
            .group_by(History.product_id)
            .all(),
        )
        scores: dict[int, int] = {cast(int, product_id): cast(int, count) for product_id, count in score_rows}

        total = sum(scores.values()) or 1
        return {pid: count / total for pid, count in scores.items()}

    def _find_similar_users(self, n_similar: int = 10) -> List[int]:
        target_products = (
            self.db.query(History.product_id).filter(History.user_id == self.user_id).distinct().subquery()
        )
        target_count = self.db.query(func.count()).select_from(target_products).scalar() or 0
        if target_count == 0:
            return []

        user_product_counts = (
            self.db.query(
                History.user_id.label("user_id"),
                func.count(func.distinct(History.product_id)).label("product_count"),
            )
            .filter(History.user_id != self.user_id)
            .group_by(History.user_id)
            .subquery()
        )
        overlap_counts = (
            self.db.query(
                History.user_id.label("user_id"),
                func.count(func.distinct(History.product_id)).label("overlap_count"),
            )
            .filter(
                History.user_id != self.user_id,
                History.product_id.in_(select(target_products.c.product_id)),
            )
            .group_by(History.user_id)
            .subquery()
        )
        aggregated_users = (
            self.db.query(
                overlap_counts.c.user_id,
                overlap_counts.c.overlap_count,
                user_product_counts.c.product_count,
            )
            .join(user_product_counts, user_product_counts.c.user_id == overlap_counts.c.user_id)
            .all()
        )

        similarities = [
            (
                user_id,
                overlap_count / sqrt(target_count * product_count),
            )
            for user_id, overlap_count, product_count in aggregated_users
        ]
        similarities.sort(key=lambda item: (item[1], item[0]), reverse=True)
        return [user_id for user_id, _ in similarities[:n_similar]]

    def get_recommendations(self) -> List[Tuple[Product, float]]:
        products = (
            self.db.query(Product)
            .options(joinedload(Product.categories))
            .filter(cast(Any, Product.quantity > 0))
            .order_by(Product.id)
            .all()
        )
        if not products:
            return []

        prefs = self._get_user_preferences()
        collab_scores = self._get_collaborative_scores() if prefs else {}
        recommendations = []
        for product in products:
            pref_score = self._calculate_preference_score(product)
            collab_score = collab_scores.get(cast(int, product.id), 0.0)
            final_score = (pref_score * 0.6) + (collab_score * 0.4)
            recommendations.append((product, final_score))
        return sorted(recommendations, key=lambda item: item[1], reverse=True)

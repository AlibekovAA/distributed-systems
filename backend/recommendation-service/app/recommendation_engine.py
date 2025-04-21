from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session, joinedload

from app.logger import logging
from app.models import History, Product, UserPreferences


class RecommendationEngine:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self._preferences_cache = None
        self._history_cache = None
        self._matrix_cache = None
        logging.debug(f"Initialized engine for user {user_id}")

    def _get_user_preferences(self) -> Dict[str, float]:
        if self._preferences_cache is None:
            prefs = self.db.query(UserPreferences).filter(UserPreferences.user_id == self.user_id).all()
            self._preferences_cache = {p.preference_name: float(p.preference_value) for p in prefs}
        return self._preferences_cache

    def _get_user_history(self) -> List[History]:
        if self._history_cache is None:
            self._history_cache = (
                self.db.query(History)
                .filter(History.user_id == self.user_id)
                .options(joinedload(History.product).joinedload(Product.categories))
                .all()
            )
        return self._history_cache

    def _calculate_preference_score(self, product: Product) -> float:
        prefs = self._get_user_preferences()
        if not prefs:
            return 0.0

        return max(
            (prefs.get(category.name, 0.0) for category in product.categories),
            default=0.0
        )

    def _get_collaborative_scores(self) -> Dict[int, float]:
        similar_users = self._find_similar_users()
        if not similar_users:
            return {}

        history = self.db.query(History).filter(History.user_id.in_(similar_users)).all()
        scores = defaultdict(int)
        for h in history:
            scores[h.product_id] += 1

        total = sum(scores.values()) or 1
        return {pid: count/total for pid, count in scores.items()}

    def _find_similar_users(self, n_similar: int = 10) -> List[int]:
        matrix, user_idx, _ = self._build_user_item_matrix()

        if self.user_id not in user_idx:
            return []

        user_sim = cosine_similarity(matrix)[user_idx[self.user_id]]
        similar_idx = np.argsort(user_sim)[-n_similar-1:-1]
        reverse_map = {idx: uid for uid, idx in user_idx.items()}
        return [reverse_map[idx] for idx in similar_idx]

    def _build_user_item_matrix(self) -> Tuple[np.ndarray, Dict[int, int], Dict[int, int]]:
        if self._matrix_cache:
            return self._matrix_cache

        history = self.db.query(History).all()
        users = sorted({h.user_id for h in history})
        products = sorted({h.product_id for h in history})

        user_idx = {uid: i for i, uid in enumerate(users)}
        product_idx = {pid: i for i, pid in enumerate(products)}

        matrix = np.zeros((len(users), len(products)))
        for h in history:
            matrix[user_idx[h.user_id], product_idx[h.product_id]] = 1

        self._matrix_cache = (matrix, user_idx, product_idx)
        return self._matrix_cache

    def get_recommendations(self) -> List[Tuple[Product, float]]:
        try:
            products = self.db.query(Product).filter(Product.quantity > 0).all()
            if not products:
                return []

            prefs = self._get_user_preferences()
            collab_scores = self._get_collaborative_scores() if prefs else {}

            recommendations = []
            for product in products:
                pref_score = self._calculate_preference_score(product)
                collab_score = collab_scores.get(product.id, 0.0)
                final_score = (pref_score * 0.6) + (collab_score * 0.4)
                recommendations.append((product, final_score))

            return sorted(recommendations, key=lambda x: x[1], reverse=True)

        except Exception as e:
            logging.error(f"Recommendation failed: {e}")
            return [
                (product, 0.0)
                for product in self.db.query(Product).filter(Product.quantity > 0).all()
            ]

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
        self._history = None
        self._preferences = None
        self._user_item_matrix = None
        self._similar_users = None
        logging.info(f"Initializing recommendation engine for user_id: {user_id}")

    def _get_user_preferences(self) -> Dict[str, float]:
        if self._preferences is None:
            preferences = (
                self.db.query(UserPreferences)
                .filter(UserPreferences.user_id == self.user_id)
                .all()
            )
            self._preferences = {
                pref.preference_name: float(pref.preference_value)
                for pref in preferences
            }
            logging.info(f"Retrieved user preferences for user_id {self.user_id}: {self._preferences}")
        return self._preferences

    def _get_user_history(self) -> List[History]:
        if self._history is None:
            self._history = (
                self.db.query(History)
                .filter(History.user_id == self.user_id)
                .options(joinedload(History.product).joinedload(Product.categories))
                .all()
            )
            logging.info(f"Retrieved user history for user_id {self.user_id}, count: {len(self._history)}")
        return self._history

    def _calculate_preference_score(self, product: Product) -> float:
        preferences = self._get_user_preferences()
        if not preferences:
            logging.info(f"No preferences found for user_id {self.user_id}")
            return 0.0

        category_scores = []
        for category in product.categories:
            if category.name in preferences:
                category_scores.append(preferences[category.name])

        score = max(category_scores) if category_scores else 0.0
        logging.info(f"Calculated preference score {score} for product {product.id}")
        return score

    def _get_collaborative_scores(self) -> Dict[int, float]:
        similar_users = self._find_similar_users()
        if not similar_users:
            logging.info(f"No similar users found for user_id {self.user_id}")
            return {}

        logging.info(f"Found {len(similar_users)} similar users for user_id {self.user_id}")

        similar_users_history = (
            self.db.query(History)
            .filter(History.user_id.in_(similar_users))
            .all()
        )
        logging.info(f"Retrieved {len(similar_users_history)} history items from similar users")

        scores = {}
        for history in similar_users_history:
            if history.product_id not in scores:
                scores[history.product_id] = 0
            scores[history.product_id] += 1

        total = sum(scores.values()) or 1
        normalized_scores = {k: v/total for k, v in scores.items()}
        logging.info(f"Calculated collaborative scores for {len(normalized_scores)} products")
        return normalized_scores

    def _find_similar_users(self, n_similar: int = 10) -> List[int]:
        matrix, user_idx, _ = self._build_user_item_matrix()

        if self.user_id not in user_idx:
            logging.info(f"User {self.user_id} not found in interaction matrix")
            return []

        user_similarities = cosine_similarity(matrix)[user_idx[self.user_id]]
        similar_users_idx = np.argsort(user_similarities)[-n_similar-1:-1]

        reverse_user_idx = {idx: user_id for user_id, idx in user_idx.items()}
        similar_users = [reverse_user_idx[idx] for idx in similar_users_idx]

        logging.info(f"Found similar users for user_id {self.user_id}: {similar_users}")
        return similar_users

    def _build_user_item_matrix(self) -> Tuple[np.ndarray, Dict[int, int], Dict[int, int]]:
        if self._user_item_matrix is not None:
            return self._user_item_matrix

        all_history = self.db.query(History).all()
        logging.info(f"Retrieved {len(all_history)} total history records")

        users = sorted(list(set(h.user_id for h in all_history)))
        products = sorted(list(set(h.product_id for h in all_history)))

        logging.info(f"Building interaction matrix for {len(users)} users and {len(products)} products")

        user_idx = {user_id: idx for idx, user_id in enumerate(users)}
        product_idx = {product_id: idx for idx, product_id in enumerate(products)}

        matrix = np.zeros((len(users), len(products)))

        for history in all_history:
            u_idx = user_idx[history.user_id]
            p_idx = product_idx[history.product_id]
            matrix[u_idx, p_idx] = 1

        self._user_item_matrix = (matrix, user_idx, product_idx)
        logging.info(f"Interaction matrix built successfully")
        return self._user_item_matrix

    def get_recommendations(self) -> List[Tuple[Product, float]]:
        try:
            logging.info(f"Starting recommendation generation for user_id {self.user_id}")

            all_products = (
                self.db.query(Product)
                .filter(Product.quantity > 0)
                .all()
            )

            if not all_products:
                logging.warning("No available products")
                return []

            recommendations = []
            user_preferences = self._get_user_preferences()
            collaborative_scores = self._get_collaborative_scores()

            for product in all_products:
                preference_score = self._calculate_preference_score(product)
                collaborative_score = collaborative_scores.get(product.id, 0.0)

                final_score = (preference_score * 0.7) + (collaborative_score * 0.3)
                recommendations.append((product, final_score))

            recommendations.sort(key=lambda x: x[1], reverse=True)

            logging.info(f"Generated {len(recommendations)} recommendations")
            return recommendations

        except Exception as e:
            logging.error(f"Error generating recommendations: {e}")
            all_products = (
                self.db.query(Product)
                .filter(Product.quantity > 0)
                .all()
            )
            return [(product, 0.0) for product in all_products]

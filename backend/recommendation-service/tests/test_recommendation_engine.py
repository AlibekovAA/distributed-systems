import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("RABBITMQ_USER", "guest")
os.environ.setdefault("RABBITMQ_PASSWORD", "guest")
os.environ.setdefault("RABBITMQ_HOST", "localhost")
os.environ.setdefault("RABBITMQ_PORT", "5672")
from app.crud import update_user_preferences
from app.database import Base
from app.models import Category, History, Product, User, UserPreferences
from app.recommendation_engine import RecommendationEngine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class RecommendationEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()

        first_user = User(email="first@example.com")
        second_user = User(email="second@example.com")
        category = Category(name="Phones")
        first_product = Product(name="First", price=100, quantity=5, categories=[category])
        second_product = Product(name="Second", price=200, quantity=5, categories=[category])
        self.db.add_all([first_user, second_user, first_product, second_product])
        self.db.flush()

        self.db.add_all(
            [
                History(user_id=first_user.id, product_id=first_product.id, order_number=1),
                History(user_id=second_user.id, product_id=first_product.id, order_number=1),
                History(user_id=second_user.id, product_id=second_product.id, order_number=1),
                UserPreferences(
                    user_id=first_user.id,
                    preference_name=category.name,
                    preference_value="10",
                ),
            ]
        )
        self.db.commit()
        self.user_id = first_user.id

    def tearDown(self) -> None:
        self.db.close()

    def test_similar_users_are_calculated_from_existing_interactions(self) -> None:
        engine = RecommendationEngine(self.db, self.user_id)

        self.assertEqual([2], engine._find_similar_users())

    def test_recommendations_keep_product_response_shape(self) -> None:
        recommendations = RecommendationEngine(self.db, self.user_id).get_recommendations()

        self.assertEqual(2, len(recommendations))
        self.assertTrue(all(isinstance(product.to_dict(), dict) for product, _ in recommendations))

    def test_preferences_are_updated_from_purchase_categories(self) -> None:
        update_user_preferences(self.db, self.user_id)

        preference = self.db.query(UserPreferences).filter(UserPreferences.user_id == self.user_id).one()
        self.assertEqual(10.0, float(preference.preference_value))


if __name__ == "__main__":
    unittest.main()

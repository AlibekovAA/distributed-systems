from sqlalchemy.orm import Session

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

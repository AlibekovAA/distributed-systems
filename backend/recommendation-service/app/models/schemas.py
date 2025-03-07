from pydantic import BaseModel


class RecommendationCreate(BaseModel):
    user_id: int
    product_id: int
    score: int


class Recommendation(BaseModel):
    id: int
    user_id: int
    product_id: int
    score: int

    class Config:
        orm_mode = True


class ProductRecommendation(BaseModel):
    id: int
    name: str
    description: str | None
    price: int
    quantity: int
    category: str | None
    similarity_score: float


class RecommendationResponse(BaseModel):
    user_id: int
    recommendations: list[ProductRecommendation]

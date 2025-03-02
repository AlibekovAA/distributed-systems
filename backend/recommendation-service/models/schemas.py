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

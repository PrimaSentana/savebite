from datetime import datetime
from typing import List
from pydantic import BaseModel, field_validator

class ReviewCreate(BaseModel):
    transaction_id: int
    rating: float
    comment: str | None = None
    
    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v):
        if v < 1.0 or v > 5.0:
            raise ValueError("Rating must be between 1 and 5")
        if round(v * 2) != v * 2:
            raise ValueError("Rating must be in 0.5 increment")
        return v

class MerchantReplyCreate(BaseModel):
    reply: str
    
class ReviewMenuResponse(BaseModel):
    id: int
    title: str
    image_url: str | None = None
    discounted_price: float
    quantity: int

    class Config:
        from_attributes = True

class ReviewResponse(BaseModel):
    id: int
    user_id: int
    merchant_id: int
    transaction_id: int
    rating: float
    comment: str | None = None
    photo_url: str | None = None
    merchant_reply: str | None = None
    replied_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None
    reviewer_username: str | None = None
    ordered_menus: List[ReviewMenuResponse] = []
    
    class Config:
        from_attributes = True
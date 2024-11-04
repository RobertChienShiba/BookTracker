import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ReviewModel(BaseModel):
    uid: str
    rating: int = Field(le=5)
    review_text: str
    user_uid: Optional[str]
    book_uid: Optional[str]
    created_at: datetime
    update_at: datetime


class ReviewCreateModel(BaseModel):
    rating: int = Field(le=5)
    review_text: str
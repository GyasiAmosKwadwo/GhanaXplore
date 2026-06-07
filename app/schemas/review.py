from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.tourism_common import ReviewTargetType
from app.schemas.user import Pagination


class ReviewCreate(BaseModel):
    attraction_id: UUID
    booking_id: Optional[UUID] = None
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    id: UUID
    reviewer_id: UUID
    attraction_id: Optional[UUID]
    booking_id: Optional[UUID]
    rating: int
    comment: Optional[str]
    target_type: ReviewTargetType
    is_verified_booking: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    items: List[ReviewResponse]
    pagination: Pagination

    class Config:
        from_attributes = True

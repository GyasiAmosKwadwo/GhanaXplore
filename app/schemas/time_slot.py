from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.user import Pagination


class TimeSlotBase(BaseModel):
    attraction_id: UUID
    start_time: str = Field(..., max_length=10)
    end_time: str = Field(..., max_length=10)
    max_capacity: Optional[int] = Field(default=1, ge=1)
    is_active: Optional[bool] = True


class TimeSlotCreate(TimeSlotBase):
    pass


class TimeSlotUpdate(BaseModel):
    start_time: Optional[str] = Field(None, max_length=10)
    end_time: Optional[str] = Field(None, max_length=10)
    max_capacity: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class TimeSlotResponse(TimeSlotBase):
    id: UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class TimeSlotListResponse(BaseModel):
    items: List[TimeSlotResponse]
    pagination: Pagination

    class Config:
        from_attributes = True

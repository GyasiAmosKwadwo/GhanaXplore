from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.user import Pagination


class ScheduleBase(BaseModel):
    attraction_id: UUID
    day_of_week: int = Field(..., ge=0, le=6)
    open_time: str = Field(..., max_length=10)
    close_time: str = Field(..., max_length=10)
    is_open: Optional[bool] = True
    max_bookings_per_slot: Optional[int] = Field(default=1, ge=1)


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    open_time: Optional[str] = Field(None, max_length=10)
    close_time: Optional[str] = Field(None, max_length=10)
    is_open: Optional[bool] = None
    max_bookings_per_slot: Optional[int] = Field(None, ge=1)


class ScheduleResponse(ScheduleBase):
    id: UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ScheduleListResponse(BaseModel):
    items: List[ScheduleResponse]
    pagination: Pagination

    class Config:
        from_attributes = True

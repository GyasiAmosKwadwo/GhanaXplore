from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.tourism_common import BookingStatus
from app.schemas.user import Pagination


class BookingCreate(BaseModel):
    attraction_id: UUID
    time_slot_id: Optional[UUID] = None
    visit_date: date
    party_size: Optional[int] = Field(default=1, ge=1)
    total_amount_ghs: Optional[Decimal] = Field(
        default=None,
        description="Optional when attraction entry_fee_ghs is set; otherwise required",
    )
    notes: Optional[str] = None


class BookingUpdate(BaseModel):
    notes: Optional[str] = None
    party_size: Optional[int] = Field(default=None, ge=1)
    time_slot_id: Optional[UUID] = None
    visit_date: Optional[date] = None



class BookingResponse(BaseModel):
    id: UUID
    tourist_id: UUID
    attraction_id: Optional[UUID]
    time_slot_id: Optional[UUID]
    booking_reference: str
    visit_date: date
    party_size: int
    total_amount_ghs: Decimal
    status: BookingStatus
    qr_code_token: Optional[str] = None
    notes: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class BookingListResponse(BaseModel):
    items: List[BookingResponse]
    pagination: Pagination

    class Config:
        from_attributes = True

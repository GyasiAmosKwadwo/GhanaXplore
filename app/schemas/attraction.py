from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from datetime import datetime

from app.models.tourism_common import ApprovalStatus
from app.schemas.user import Pagination


class AttractionBase(BaseModel):
    name: str = Field(..., max_length=255)
    region: str = Field(..., max_length=120)
    district: Optional[str] = Field(None, max_length=120)
    description: str
    category: str = Field(..., max_length=50)
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    opening_hours: Optional[str] = None
    entry_fee_ghs: Optional[Decimal] = None
    is_offline_available: Optional[bool] = False


class AttractionCreate(AttractionBase):
    pass


class AttractionUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    region: Optional[str] = Field(None, max_length=120)
    district: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    opening_hours: Optional[str] = None
    entry_fee_ghs: Optional[Decimal] = None
    is_offline_available: Optional[bool] = None


class AttractionApprovalUpdate(BaseModel):
    approval_status: ApprovalStatus


class AttractionResponse(AttractionBase):
    id: UUID
    operator_id: Optional[UUID]
    approval_status: ApprovalStatus
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class AttractionListResponse(BaseModel):
    items: List[AttractionResponse]
    pagination: Pagination

    class Config:
        from_attributes = True

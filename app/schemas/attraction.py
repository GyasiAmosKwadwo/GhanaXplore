from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from datetime import datetime

from app.models.tourism_common import ApprovalStatus, AttractionStatus
from app.schemas.user import Pagination


class AttractionActivityBase(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    price_ghs: Optional[Decimal] = None
    price_usd: Optional[Decimal] = None
    duration_minutes: Optional[int] = None
    max_participants: Optional[int] = None
    is_available: Optional[bool] = True
    requires_advance_booking: Optional[bool] = False
    display_order: Optional[int] = 0
    includes: List[str] = Field(default_factory=list)
    excludes: List[str] = Field(default_factory=list)
    restrictions: Dict[str, Any] = Field(default_factory=dict)
    images: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AttractionActivityCreate(AttractionActivityBase):
    pass


class AttractionResponseActivity(AttractionActivityBase):
    id: UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="metadata_")

    class Config:
        from_attributes = True
        populate_by_name = True


class AttractionBase(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=255)
    short_description: Optional[str] = Field(None, max_length=500)
    region: str = Field(..., max_length=120)
    location: Optional[str] = Field(None, max_length=255)
    district: Optional[str] = Field(None, max_length=120)
    description: str
    category: str = Field(..., max_length=50)
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    opening_hours: Optional[str] = None
    entry_fee_ghs: Optional[Decimal] = None
    is_available: Optional[bool] = True
    images: List[str] = Field(default_factory=list)
    amenities: List[str] = Field(default_factory=list)
    includes: List[str] = Field(default_factory=list)
    excludes: List[str] = Field(default_factory=list)
    cancellation_policy: Optional[str] = None
    special_requirements: Optional[str] = None
    is_offline_available: Optional[bool] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    activities: List[AttractionActivityCreate] = Field(default_factory=list)



class AttractionCreate(AttractionBase):
    pass


class AttractionUpdate(BaseModel):
    slug: Optional[str] = Field(None, max_length=255)
    name: Optional[str] = Field(None, max_length=255)
    short_description: Optional[str] = Field(None, max_length=500)
    region: Optional[str] = Field(None, max_length=120)
    location: Optional[str] = Field(None, max_length=255)
    district: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    opening_hours: Optional[str] = None
    entry_fee_ghs: Optional[Decimal] = None
    is_available: Optional[bool] = None
    images: Optional[List[str]] = None
    amenities: Optional[List[str]] = None
    includes: Optional[List[str]] = None
    excludes: Optional[List[str]] = None
    cancellation_policy: Optional[str] = None
    special_requirements: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[AttractionStatus] = None


class AttractionApprovalUpdate(BaseModel):
    approval_status: ApprovalStatus


class AttractionResponse(AttractionBase):
    id: UUID
    operator_id: Optional[UUID]
    approval_status: ApprovalStatus
    status: AttractionStatus
    activities: List[AttractionResponseActivity] = Field(default_factory=list)
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="metadata_")

    class Config:
        from_attributes = True
        populate_by_name = True


class AttractionListResponse(BaseModel):
    items: List[AttractionResponse]
    pagination: Pagination

    class Config:
        from_attributes = True

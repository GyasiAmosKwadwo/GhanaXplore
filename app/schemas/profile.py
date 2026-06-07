import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TouristProfileBase(BaseModel):
    preferred_language: Optional[str] = None
    nationality: Optional[str] = None
    home_region: Optional[str] = None
    bio: Optional[str] = None
    interests: list[str] = Field(default_factory=list)
    travel_preferences: list[str] = Field(default_factory=list)
    accessibility_needs: list[str] = Field(default_factory=list)


class TouristProfileCreate(TouristProfileBase):
    pass


class TouristProfileUpdate(TouristProfileBase):
    pass


class TouristProfileResponse(TouristProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OperatorProfileBase(BaseModel):
    business_name: Optional[str] = None
    business_description: Optional[str] = None
    region: Optional[str] = None
    district: Optional[str] = None
    website: Optional[str] = None
    license_number: Optional[str] = None
    registration_number: Optional[str] = None
    is_public: bool = False


class OperatorProfileCreate(OperatorProfileBase):
    pass


class OperatorProfileUpdate(OperatorProfileBase):
    pass


class OperatorProfileResponse(OperatorProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas.user import Pagination


class FavoriteCreate(BaseModel):
    attraction_id: UUID


class FavoriteResponse(BaseModel):
    id: UUID
    user_id: UUID
    attraction_id: UUID
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class FavoriteListResponse(BaseModel):
    items: List[FavoriteResponse]
    pagination: Pagination

    class Config:
        from_attributes = True

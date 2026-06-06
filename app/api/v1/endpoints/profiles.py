from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.profile import (
    OperatorProfileResponse,
    OperatorProfileUpdate,
    TouristProfileResponse,
    TouristProfileUpdate,
)
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.get("/me/tourist", response_model=TouristProfileResponse)
async def get_my_tourist_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    return await service.get_or_create_tourist_profile(current_user)


@router.post("/me/tourist", response_model=TouristProfileResponse)
@router.put("/me/tourist", response_model=TouristProfileResponse)
async def save_my_tourist_profile(
    data: TouristProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    return await service.update_tourist_profile(current_user, data)


@router.get("/me/operator", response_model=OperatorProfileResponse)
async def get_my_operator_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    return await service.get_or_create_operator_profile(current_user)


@router.post("/me/operator", response_model=OperatorProfileResponse)
@router.put("/me/operator", response_model=OperatorProfileResponse)
async def save_my_operator_profile(
    data: OperatorProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    return await service.update_operator_profile(current_user, data)

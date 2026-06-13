from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operator_profile import OperatorProfile
from app.models.tourist_profile import TouristProfile
from app.models.user import User, UserRole
from app.schemas.profile import OperatorProfileUpdate, TouristProfileUpdate


class ProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_user_profile(self, model, user_id):
        result = await self.db.execute(select(model).where(model.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_or_create_tourist_profile(self, user: User) -> TouristProfile:
        if user.role != UserRole.TOURIST:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only tourist accounts can use this profile endpoint",
            )
        profile = await self._get_user_profile(TouristProfile, user.id)
        if profile:
            return profile
        profile = TouristProfile(user_id=user.id)
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def update_tourist_profile(
        self, user: User, data: TouristProfileUpdate
    ) -> TouristProfile:
        profile = await self.get_or_create_tourist_profile(user)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, key, value)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def get_or_create_operator_profile(self, user: User) -> OperatorProfile:
        if user.role != UserRole.OPERATOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only operator accounts can use this profile endpoint",
            )
        profile = await self._get_user_profile(OperatorProfile, user.id)
        if profile:
            return profile
        profile = OperatorProfile(user_id=user.id)
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def update_operator_profile(
        self, user: User, data: OperatorProfileUpdate
    ) -> OperatorProfile:
        profile = await self.get_or_create_operator_profile(user)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, key, value)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

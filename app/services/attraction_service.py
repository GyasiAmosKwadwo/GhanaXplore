from fastapi import HTTPException, status

from app.models.attraction import Attraction
from app.models.attraction_activity import AttractionActivity
from app.models.tourism_common import ApprovalStatus, AttractionStatus
from app.models.user import User, UserRole
from app.repositories.attraction_repository import AttractionRepository
from app.schemas.attraction import AttractionCreate


class AttractionService:
    def __init__(self, db):
        self.db = db
        self.repo = AttractionRepository(db)

    async def create_attraction(self, user: User, data: AttractionCreate) -> Attraction:
        # Only operators may create attractions
        if user.role != UserRole.OPERATOR:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only operator accounts can create attractions")

        # Require operator account verification before publishing
        if not user.is_verified:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operator account must be verified before creating attractions")

        attraction = Attraction(
            slug=data.slug,
            name=data.name,
            short_description=data.short_description,
            region=data.region,
            location=data.location,
            district=data.district,
            description=data.description,
            category=data.category,
            gps_latitude=data.gps_latitude,
            gps_longitude=data.gps_longitude,
            opening_hours=data.opening_hours,
            entry_fee_ghs=data.entry_fee_ghs,
            is_available=data.is_available if data.is_available is not None else True,
            images=data.images,
            amenities=data.amenities,
            includes=data.includes,
            excludes=data.excludes,
            cancellation_policy=data.cancellation_policy,
            special_requirements=data.special_requirements,
            metadata_=data.metadata,
            is_offline_available=data.is_offline_available or False,
            operator_id=user.id,
            activities=[
                AttractionActivity(
                    name=activity.name,
                    slug=activity.slug,
                    description=activity.description,
                    category=activity.category,
                    price_ghs=activity.price_ghs,
                    price_usd=activity.price_usd,
                    duration_minutes=activity.duration_minutes,
                    max_participants=activity.max_participants,
                    includes=activity.includes,
                    excludes=activity.excludes,
                    restrictions=activity.restrictions,
                    images=activity.images,
                    metadata_=activity.metadata,
                    is_available=activity.is_available if activity.is_available is not None else True,
                    requires_advance_booking=activity.requires_advance_booking or False,
                    display_order=activity.display_order,
                )
                for activity in data.activities
            ],
        )

        await self.repo.create(attraction)
        await self.db.commit()
        return await self.repo.get_by_id(attraction.id)

    async def get_attraction(self, attraction_id) -> Attraction | None:
        return await self.repo.get_by_id(attraction_id)

    async def list_public_attractions(
        self,
        filters: dict | None = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ):
        filters = filters or {}
        filters.setdefault("approval_status", ApprovalStatus.APPROVED)
        filters.setdefault("status", AttractionStatus.ACTIVE)
        if "is_available" not in filters:
            filters["is_available"] = True

        attractions = await self.repo.list(
            skip=skip,
            limit=limit,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        total = await self.repo.count(filters=filters)
        return attractions, total

    async def list_operator_attractions(
        self,
        operator_id,
        filters: dict | None = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ):
        filters = filters or {}
        filters["operator_id"] = operator_id

        attractions = await self.repo.list(
            skip=skip,
            limit=limit,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        total = await self.repo.count(filters=filters)
        return attractions, total

    async def update_attraction(self, user: User, attraction_id, data: dict) -> Attraction:
        attraction = await self.repo.get_by_id(attraction_id)
        if not attraction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attraction not found")

        if user.role == UserRole.OPERATOR and attraction.operator_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operators may only update their own attractions")

        if user.role not in {UserRole.OPERATOR, UserRole.ADMINISTRATOR}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only operators or administrators can update attractions")

        restricted_keys = {"operator_id", "approval_status"}
        update_data = {k: v for k, v in data.items() if k not in restricted_keys}
        if "metadata" in update_data:
            update_data["metadata_"] = update_data.pop("metadata")

        updated_attraction = await self.repo.update(attraction_id, update_data)
        if not updated_attraction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attraction not found")

        await self.db.commit()
        return await self.repo.get_by_id(attraction_id)

    async def set_approval_status(self, attraction_id, approval_status: ApprovalStatus) -> Attraction:
        attraction = await self.repo.get_by_id(attraction_id)
        if not attraction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attraction not found")

        attraction.approval_status = approval_status
        if approval_status == ApprovalStatus.APPROVED:
            attraction.status = AttractionStatus.ACTIVE
        elif approval_status in {ApprovalStatus.DECLINED, ApprovalStatus.SUSPENDED}:
            attraction.status = AttractionStatus.INACTIVE
        elif approval_status == ApprovalStatus.PENDING:
            attraction.status = AttractionStatus.PENDING_APPROVAL

        await self.db.flush()
        await self.db.commit()
        return await self.repo.get_by_id(attraction_id)

    async def delete_attraction(self, user: User, attraction_id) -> None:
        attraction = await self.repo.get_by_id(attraction_id)
        if not attraction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attraction not found")

        if user.role == UserRole.OPERATOR and attraction.operator_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operators may only delete their own attractions")

        if user.role not in {UserRole.OPERATOR, UserRole.ADMINISTRATOR}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only operators or administrators can delete attractions")

        await self.repo.delete(attraction_id)
        await self.db.commit()

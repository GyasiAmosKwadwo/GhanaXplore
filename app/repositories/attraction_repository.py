from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.attraction import Attraction


class AttractionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, attraction: Attraction) -> Attraction:
        self.db.add(attraction)
        await self.db.flush()
        return attraction

    async def get_by_id(self, attraction_id):
        result = await self.db.execute(
            select(Attraction).options(selectinload(Attraction.activities)).where(Attraction.id == attraction_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: dict | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ):
        query = select(Attraction)

        if filters:
            if filters.get("operator_id") is not None:
                query = query.where(Attraction.operator_id == filters["operator_id"])
            if filters.get("approval_status") is not None:
                status_value = getattr(filters["approval_status"], "value", filters["approval_status"])
                query = query.where(Attraction.approval_status == status_value)
            if filters.get("status") is not None:
                status_value = getattr(filters["status"], "value", filters["status"])
                query = query.where(Attraction.status == status_value)
            if filters.get("is_available") is not None:
                query = query.where(Attraction.is_available == filters["is_available"])
            if filters.get("region") is not None:
                query = query.where(Attraction.region.ilike(f"%{filters['region']}%"))
            if filters.get("category") is not None:
                query = query.where(Attraction.category == filters["category"])
            if filters.get("search") is not None:
                search = f"%{filters['search']}%"
                query = query.where(
                    or_(
                        Attraction.name.ilike(search),
                        Attraction.slug.ilike(search),
                        Attraction.description.ilike(search),
                        Attraction.short_description.ilike(search),
                        Attraction.region.ilike(search),
                        Attraction.location.ilike(search),
                        Attraction.district.ilike(search),
                    )
                )

        sort_by_attr = getattr(Attraction, sort_by, Attraction.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_by_attr.asc())
        else:
            query = query.order_by(sort_by_attr.desc())

        result = await self.db.execute(query.options(selectinload(Attraction.activities)).offset(skip).limit(limit))
        return result.scalars().all()

    async def count(self, filters: dict | None = None) -> int:
        query = select(func.count()).select_from(Attraction)

        if filters:
            if filters.get("operator_id") is not None:
                query = query.where(Attraction.operator_id == filters["operator_id"])
            if filters.get("approval_status") is not None:
                status_value = getattr(filters["approval_status"], "value", filters["approval_status"])
                query = query.where(Attraction.approval_status == status_value)
            if filters.get("status") is not None:
                status_value = getattr(filters["status"], "value", filters["status"])
                query = query.where(Attraction.status == status_value)
            if filters.get("is_available") is not None:
                query = query.where(Attraction.is_available == filters["is_available"])
            if filters.get("region") is not None:
                query = query.where(Attraction.region.ilike(f"%{filters['region']}%"))
            if filters.get("category") is not None:
                query = query.where(Attraction.category == filters["category"])
            if filters.get("search") is not None:
                search = f"%{filters['search']}%"
                query = query.where(
                    or_(
                        Attraction.name.ilike(search),
                        Attraction.slug.ilike(search),
                        Attraction.description.ilike(search),
                        Attraction.short_description.ilike(search),
                        Attraction.region.ilike(search),
                        Attraction.location.ilike(search),
                        Attraction.district.ilike(search),
                    )
                )

        result = await self.db.execute(query)
        return result.scalar_one()

    async def update(self, attraction_id, data: dict):
        attraction = await self.get_by_id(attraction_id)
        if not attraction:
            return None

        for key, value in data.items():
            attr_key = "metadata_" if key == "metadata" else key
            if value is not None and hasattr(attraction, attr_key):
                setattr(attraction, attr_key, value)

        await self.db.flush()
        return attraction

    async def delete(self, attraction_id) -> bool:
        attraction = await self.get_by_id(attraction_id)
        if not attraction:
            return False

        await self.db.delete(attraction)
        await self.db.flush()
        return True

    async def list_by_operator(self, operator_id):
        return await self.list(filters={"operator_id": operator_id})

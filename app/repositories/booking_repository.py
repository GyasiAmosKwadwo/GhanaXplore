from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.tourism_common import BookingStatus


class BookingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, booking: Booking) -> Booking:
        self.db.add(booking)
        await self.db.flush()
        return booking

    async def get_by_id(self, booking_id: UUID) -> Booking | None:
        result = await self.db.execute(select(Booking).where(Booking.id == booking_id))
        return result.scalar_one_or_none()

    async def get_for_tourist(self, booking_id: UUID, tourist_id: UUID) -> Booking | None:
        result = await self.db.execute(
            select(Booking).where(Booking.id == booking_id, Booking.tourist_id == tourist_id)
        )
        return result.scalar_one_or_none()

    async def list_for_tourist(
        self,
        tourist_id: UUID,
        *,
        status: BookingStatus | None = None,
        attraction_id: UUID | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Booking]:
        query = select(Booking).where(Booking.tourist_id == tourist_id)
        if status is not None:
            query = query.where(Booking.status == status)
        if attraction_id is not None:
            query = query.where(Booking.attraction_id == attraction_id)

        result = await self.db.execute(
            query.order_by(Booking.visit_date.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count_for_tourist(
        self,
        tourist_id: UUID,
        *,
        status: BookingStatus | None = None,
        attraction_id: UUID | None = None,
    ) -> int:
        query = select(func.count()).select_from(Booking).where(Booking.tourist_id == tourist_id)
        if status is not None:
            query = query.where(Booking.status == status)
        if attraction_id is not None:
            query = query.where(Booking.attraction_id == attraction_id)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def list_for_operator(
        self,
        operator_id: UUID,
        *,
        attraction_id: UUID | None = None,
        status: BookingStatus | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Booking]:
        from app.models.attraction import Attraction

        query = (
            select(Booking)
            .join(Attraction, Booking.attraction_id == Attraction.id)
            .where(Attraction.operator_id == operator_id)
        )
        if attraction_id is not None:
            query = query.where(Booking.attraction_id == attraction_id)
        if status is not None:
            query = query.where(Booking.status == status)

        result = await self.db.execute(
            query.order_by(Booking.visit_date.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count_for_operator(
        self,
        operator_id: UUID,
        *,
        attraction_id: UUID | None = None,
        status: BookingStatus | None = None,
    ) -> int:
        from app.models.attraction import Attraction

        query = (
            select(func.count())
            .select_from(Booking)
            .join(Attraction, Booking.attraction_id == Attraction.id)
            .where(Attraction.operator_id == operator_id)
        )
        if attraction_id is not None:
            query = query.where(Booking.attraction_id == attraction_id)
        if status is not None:
            query = query.where(Booking.status == status)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def sum_party_size_for_slot(
        self,
        time_slot_id: UUID,
        visit_date: date,
        *,
        exclude_booking_id: UUID | None = None,
    ) -> int:
        query = (
            select(func.coalesce(func.sum(Booking.party_size), 0))
            .where(Booking.time_slot_id == time_slot_id)
            .where(Booking.visit_date == visit_date)
            .where(Booking.status != BookingStatus.CANCELLED)
        )
        if exclude_booking_id is not None:
            query = query.where(Booking.id != exclude_booking_id)

        result = await self.db.execute(query)
        return int(result.scalar_one())

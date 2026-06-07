import secrets
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attraction import Attraction
from app.models.booking import Booking
from app.models.time_slot import TimeSlot
from app.models.tourism_common import ApprovalStatus, BookingStatus
from app.models.user import User, UserRole
from app.repositories.booking_repository import BookingRepository
from app.schemas.booking import BookingCreate, BookingUpdate
from sqlalchemy import select


class BookingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = BookingRepository(db)

    @staticmethod
    def _generate_booking_reference() -> str:
        return f"GHX-{uuid.uuid4().hex[:12].upper()}"

    @staticmethod
    def _generate_qr_code_token() -> str:
        return secrets.token_urlsafe(32)

    async def _get_approved_attraction(self, attraction_id: UUID) -> Attraction:
        result = await self.db.execute(select(Attraction).where(Attraction.id == attraction_id))
        attraction = result.scalar_one_or_none()
        if not attraction or attraction.approval_status != ApprovalStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attraction unavailable for booking",
            )
        if not attraction.is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attraction is not currently available for booking",
            )
        return attraction

    async def _get_valid_time_slot(
        self, time_slot_id: UUID, attraction_id: UUID
    ) -> TimeSlot:
        result = await self.db.execute(select(TimeSlot).where(TimeSlot.id == time_slot_id))
        time_slot = result.scalar_one_or_none()
        if not time_slot or time_slot.attraction_id != attraction_id or not time_slot.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid time slot",
            )
        return time_slot

    def _validate_visit_date(self, visit_date: date) -> None:
        today = datetime.now(timezone.utc).date()
        if visit_date < today:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Visit date cannot be in the past",
            )

    async def _ensure_capacity(
        self,
        time_slot: TimeSlot,
        visit_date: date,
        party_size: int,
        *,
        exclude_booking_id: UUID | None = None,
    ) -> None:
        current_party_size = await self.repo.sum_party_size_for_slot(
            time_slot.id,
            visit_date,
            exclude_booking_id=exclude_booking_id,
        )
        if current_party_size + party_size > time_slot.max_capacity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Time slot capacity exceeded",
            )

    async def create_booking(self, user: User, payload: BookingCreate) -> Booking:
        attraction = await self._get_approved_attraction(payload.attraction_id)
        self._validate_visit_date(payload.visit_date)

        party_size = payload.party_size or 1
        time_slot = None

        if payload.time_slot_id:
            time_slot = await self._get_valid_time_slot(payload.time_slot_id, payload.attraction_id)
            await self._ensure_capacity(time_slot, payload.visit_date, party_size)
        elif attraction.entry_fee_ghs is not None:
            # Attractions with pricing should use a time slot when slots exist.
            slot_count = await self.db.execute(
                select(TimeSlot.id)
                .where(TimeSlot.attraction_id == payload.attraction_id)
                .where(TimeSlot.is_active.is_(True))
                .limit(1)
            )
            if slot_count.scalar_one_or_none() is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A time slot is required for this attraction",
                )

        total_amount = payload.total_amount_ghs
        if total_amount is None:
            if attraction.entry_fee_ghs is not None:
                total_amount = attraction.entry_fee_ghs * party_size
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="total_amount_ghs is required when attraction has no entry fee",
                )

        booking = Booking(
            tourist_id=user.id,
            attraction_id=payload.attraction_id,
            time_slot_id=payload.time_slot_id,
            visit_date=payload.visit_date,
            party_size=party_size,
            total_amount_ghs=total_amount,
            status=BookingStatus.PENDING,
            notes=payload.notes,
            booking_reference=self._generate_booking_reference(),
        )

        await self.repo.create(booking)
        await self.db.refresh(booking)
        return booking

    async def get_booking_for_tourist(self, booking_id: UUID, tourist_id: UUID) -> Booking:
        booking = await self.repo.get_for_tourist(booking_id, tourist_id)
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
        return booking

    async def list_tourist_bookings(
        self,
        tourist_id: UUID,
        *,
        status_filter: BookingStatus | None = None,
        attraction_id: UUID | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Booking], int]:
        skip = (page - 1) * per_page
        items = await self.repo.list_for_tourist(
            tourist_id,
            status=status_filter,
            attraction_id=attraction_id,
            skip=skip,
            limit=per_page,
        )
        total = await self.repo.count_for_tourist(
            tourist_id,
            status=status_filter,
            attraction_id=attraction_id,
        )
        return items, total

    async def list_operator_bookings(
        self,
        operator: User,
        *,
        attraction_id: UUID | None = None,
        status_filter: BookingStatus | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Booking], int]:
        if operator.role not in {UserRole.OPERATOR, UserRole.ADMINISTRATOR}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operator access only",
            )
        if operator.role == UserRole.OPERATOR and not operator.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operator account is pending verification",
            )

        skip = (page - 1) * per_page
        items = await self.repo.list_for_operator(
            operator.id,
            attraction_id=attraction_id,
            status=status_filter,
            skip=skip,
            limit=per_page,
        )
        total = await self.repo.count_for_operator(
            operator.id,
            attraction_id=attraction_id,
            status=status_filter,
        )
        return items, total

    async def update_booking(
        self, booking_id: UUID, tourist_id: UUID, payload: BookingUpdate
    ) -> Booking:
        booking = await self.repo.get_for_tourist(booking_id, tourist_id)
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

        if booking.status != BookingStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only pending bookings can be updated",
            )

        next_visit_date = payload.visit_date or booking.visit_date
        next_party_size = payload.party_size if payload.party_size is not None else booking.party_size
        next_time_slot_id = (
            payload.time_slot_id if payload.time_slot_id is not None else booking.time_slot_id
        )

        if payload.visit_date is not None:
            self._validate_visit_date(payload.visit_date)

        if next_time_slot_id:
            time_slot = await self._get_valid_time_slot(next_time_slot_id, booking.attraction_id)
            await self._ensure_capacity(
                time_slot,
                next_visit_date,
                next_party_size,
                exclude_booking_id=booking.id,
            )

        if payload.time_slot_id is not None:
            booking.time_slot_id = payload.time_slot_id
        if payload.visit_date is not None:
            booking.visit_date = payload.visit_date
        if payload.party_size is not None:
            booking.party_size = payload.party_size
        if payload.notes is not None:
            booking.notes = payload.notes

        await self.db.flush()
        await self.db.refresh(booking)
        return booking

    async def cancel_booking(self, booking_id: UUID, tourist_id: UUID) -> Booking:
        booking = await self.repo.get_for_tourist(booking_id, tourist_id)
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

        if booking.status == BookingStatus.CANCELLED:
            return booking

        if booking.status == BookingStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Completed bookings cannot be cancelled",
            )

        booking.status = BookingStatus.CANCELLED
        await self.db.flush()
        await self.db.refresh(booking)
        return booking

    async def confirm_booking(self, booking_id: UUID, operator: User) -> Booking:
        booking = await self.repo.get_by_id(booking_id)
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

        attraction = await self._get_approved_attraction(booking.attraction_id)
        if operator.role == UserRole.OPERATOR and attraction.operator_id != operator.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operators may only confirm bookings for their own attractions",
            )
        if operator.role not in {UserRole.OPERATOR, UserRole.ADMINISTRATOR}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operator access only",
            )

        if booking.status != BookingStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only pending bookings can be confirmed",
            )

        booking.status = BookingStatus.CONFIRMED
        booking.qr_code_token = self._generate_qr_code_token()
        await self.db.flush()
        await self.db.refresh(booking)
        return booking

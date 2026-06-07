import uuid
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.attraction import Attraction
from app.models.booking import Booking
from app.models.time_slot import TimeSlot
from app.models.tourism_common import ApprovalStatus, BookingStatus
from app.schemas.booking import BookingCreate, BookingListResponse, BookingResponse

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Attraction).where(Attraction.id == payload.attraction_id))
    attraction = result.scalar_one_or_none()
    if not attraction or attraction.approval_status != ApprovalStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attraction unavailable for booking")

    if payload.time_slot_id:
        result = await db.execute(select(TimeSlot).where(TimeSlot.id == payload.time_slot_id))
        time_slot = result.scalar_one_or_none()
        if not time_slot or time_slot.attraction_id != payload.attraction_id or not time_slot.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid time slot")

    booking = Booking(
        tourist_id=current_user.id,
        attraction_id=payload.attraction_id,
        time_slot_id=payload.time_slot_id,
        visit_date=payload.visit_date,
        party_size=payload.party_size or 1,
        total_amount_ghs=payload.total_amount_ghs,
        status=BookingStatus.PENDING,
        notes=payload.notes,
        booking_reference=uuid.uuid4().hex,
    )

    db.add(booking)
    await db.flush()
    await db.refresh(booking)
    return booking


@router.get("/", response_model=BookingListResponse)
async def list_bookings(
    status: Optional[BookingStatus] = Query(None, description="Filter bookings by status"),
    attraction_id: Optional[UUID] = Query(None, description="Filter by attraction"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Booking).where(Booking.tourist_id == current_user.id)
    count_query = select(func.count()).select_from(Booking).where(Booking.tourist_id == current_user.id)
    if status:
        query = query.where(Booking.status == status)
        count_query = count_query.where(Booking.status == status)
    if attraction_id:
        query = query.where(Booking.attraction_id == attraction_id)
        count_query = count_query.where(Booking.attraction_id == attraction_id)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(query.order_by(Booking.visit_date.desc()).offset((page - 1) * per_page).limit(per_page))
    items = result.scalars().all()

    total_pages = (total + per_page - 1) // per_page if per_page else 0
    return {
        "items": items,
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1 and total_pages > 0,
        },
    }


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id, Booking.tourist_id == current_user.id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return booking


@router.patch("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id, Booking.tourist_id == current_user.id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.status == BookingStatus.CANCELLED:
        return booking
    booking.status = BookingStatus.CANCELLED
    await db.flush()
    await db.refresh(booking)
    return booking

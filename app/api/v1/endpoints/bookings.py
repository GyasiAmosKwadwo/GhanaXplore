from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import build_audit_context
from app.core.deps import get_current_user, get_db, require_verified_operator
from app.models.tourism_common import BookingStatus
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingListResponse, BookingResponse, BookingUpdate
from app.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def _pagination(total: int, page: int, per_page: int) -> dict:
    total_pages = (total + per_page - 1) // per_page if per_page else 0
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1 and total_pages > 0,
    }


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = BookingService(db)
    return await service.create_booking(
        current_user,
        payload,
        audit_context=build_audit_context(request, current_user),
    )


@router.get("/", response_model=BookingListResponse)
async def list_bookings(
    status_filter: Optional[BookingStatus] = Query(None, alias="status", description="Filter bookings by status"),
    attraction_id: Optional[UUID] = Query(None, description="Filter by attraction"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = BookingService(db)
    items, total = await service.list_tourist_bookings(
        current_user.id,
        status_filter=status_filter,
        attraction_id=attraction_id,
        page=page,
        per_page=per_page,
    )
    return {"items": items, "pagination": _pagination(total, page, per_page)}


@router.get("/managed", response_model=BookingListResponse)
async def list_managed_bookings(
    attraction_id: Optional[UUID] = Query(None, description="Filter by attraction"),
    status_filter: Optional[BookingStatus] = Query(None, alias="status", description="Filter bookings by status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_verified_operator),
    db: AsyncSession = Depends(get_db),
):
    """List bookings for attractions owned by the authenticated operator."""
    service = BookingService(db)
    items, total = await service.list_operator_bookings(
        current_user,
        attraction_id=attraction_id,
        status_filter=status_filter,
        page=page,
        per_page=per_page,
    )
    return {"items": items, "pagination": _pagination(total, page, per_page)}


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = BookingService(db)
    return await service.get_booking_for_tourist(booking_id, current_user.id)


@router.patch("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: UUID,
    payload: BookingUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = BookingService(db)
    return await service.update_booking(
        booking_id,
        current_user.id,
        payload,
        audit_context=build_audit_context(request, current_user),
    )


@router.patch("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = BookingService(db)
    return await service.cancel_booking(
        booking_id,
        current_user.id,
        audit_context=build_audit_context(request, current_user),
    )


@router.patch("/{booking_id}/confirm", response_model=BookingResponse)
async def confirm_booking(
    booking_id: UUID,
    request: Request,
    current_user: User = Depends(require_verified_operator),
    db: AsyncSession = Depends(get_db),
):
    """Confirm a pending booking and issue a QR code token for entry."""
    service = BookingService(db)
    return await service.confirm_booking(
        booking_id,
        current_user,
        audit_context=build_audit_context(request, current_user),
    )

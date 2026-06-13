from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_verified_operator
from app.models.attraction import Attraction
from app.models.time_slot import TimeSlot
from app.schemas.time_slot import (
    TimeSlotCreate,
    TimeSlotListResponse,
    TimeSlotResponse,
    TimeSlotUpdate,
)

router = APIRouter(prefix="/time-slots", tags=["Time Slots"])


@router.post("/", response_model=TimeSlotResponse, status_code=status.HTTP_201_CREATED)
async def create_time_slot(
    payload: TimeSlotCreate,
    current_user=Depends(require_verified_operator),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Attraction).where(Attraction.id == payload.attraction_id))
    attraction = result.scalar_one_or_none()
    if not attraction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attraction not found")
    if attraction.operator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the attraction owner may manage time slots",
        )

    time_slot = TimeSlot(
        attraction_id=payload.attraction_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        max_capacity=payload.max_capacity or 1,
        is_active=payload.is_active if payload.is_active is not None else True,
    )

    db.add(time_slot)
    await db.flush()
    await db.refresh(time_slot)
    return time_slot


@router.get("/", response_model=TimeSlotListResponse)
async def list_time_slots(
    attraction_id: Optional[UUID] = Query(None, description="Filter time slots by attraction ID"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(TimeSlot)
    count_query = select(func.count()).select_from(TimeSlot)
    if attraction_id:
        query = query.where(TimeSlot.attraction_id == attraction_id)
        count_query = count_query.where(TimeSlot.attraction_id == attraction_id)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(
        query.order_by(TimeSlot.start_time.asc()).offset((page - 1) * per_page).limit(per_page)
    )
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


@router.patch("/{time_slot_id}", response_model=TimeSlotResponse)
async def update_time_slot(
    time_slot_id: UUID,
    payload: TimeSlotUpdate,
    current_user=Depends(require_verified_operator),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TimeSlot).where(TimeSlot.id == time_slot_id))
    time_slot = result.scalar_one_or_none()
    if not time_slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Time slot not found")

    result = await db.execute(select(Attraction).where(Attraction.id == time_slot.attraction_id))
    attraction = result.scalar_one_or_none()
    if not attraction or attraction.operator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the attraction owner may update time slots",
        )

    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(time_slot, key, value)

    await db.flush()
    await db.refresh(time_slot)
    return time_slot


@router.delete("/{time_slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_time_slot(
    time_slot_id: UUID,
    current_user=Depends(require_verified_operator),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TimeSlot).where(TimeSlot.id == time_slot_id))
    time_slot = result.scalar_one_or_none()
    if not time_slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Time slot not found")

    result = await db.execute(select(Attraction).where(Attraction.id == time_slot.attraction_id))
    attraction = result.scalar_one_or_none()
    if not attraction or attraction.operator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the attraction owner may delete time slots",
        )

    await db.delete(time_slot)
    await db.flush()
    return None

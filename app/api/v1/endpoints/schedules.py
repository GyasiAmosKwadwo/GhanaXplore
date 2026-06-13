from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_verified_operator
from app.models.attraction import Attraction
from app.models.schedule import Schedule
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleListResponse,
    ScheduleResponse,
    ScheduleUpdate,
)

router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    payload: ScheduleCreate,
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
            detail="Only the attraction owner may manage schedules",
        )

    schedule = Schedule(
        attraction_id=payload.attraction_id,
        day_of_week=payload.day_of_week,
        open_time=payload.open_time,
        close_time=payload.close_time,
        is_open=payload.is_open if payload.is_open is not None else True,
        max_bookings_per_slot=payload.max_bookings_per_slot or 1,
    )

    db.add(schedule)
    await db.flush()
    await db.refresh(schedule)
    return schedule


@router.get("/", response_model=ScheduleListResponse)
async def list_schedules(
    attraction_id: Optional[UUID] = Query(None, description="Filter schedules by attraction ID"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Schedule)
    if attraction_id:
        query = query.where(Schedule.attraction_id == attraction_id)

    count_query = select(func.count()).select_from(Schedule)
    if attraction_id:
        count_query = count_query.where(Schedule.attraction_id == attraction_id)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(
        query.order_by(Schedule.day_of_week.asc()).offset((page - 1) * per_page).limit(per_page)
    )
    items = result.scalars().all()

    return {
        "items": items,
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page if per_page else 0,
            "has_next": page * per_page < total,
            "has_prev": page > 1,
        },
    }


@router.patch("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: UUID,
    payload: ScheduleUpdate,
    current_user=Depends(require_verified_operator),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")

    result = await db.execute(select(Attraction).where(Attraction.id == schedule.attraction_id))
    attraction = result.scalar_one_or_none()
    if not attraction or attraction.operator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the attraction owner may update schedules",
        )

    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(schedule, key, value)

    await db.flush()
    await db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: UUID,
    current_user=Depends(require_verified_operator),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")

    result = await db.execute(select(Attraction).where(Attraction.id == schedule.attraction_id))
    attraction = result.scalar_one_or_none()
    if not attraction or attraction.operator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the attraction owner may delete schedules",
        )

    await db.delete(schedule)
    await db.flush()
    return None

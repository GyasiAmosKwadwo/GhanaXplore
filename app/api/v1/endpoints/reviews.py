from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.attraction import Attraction
from app.models.booking import Booking
from app.models.review import Review
from app.models.tourism_common import ReviewTargetType
from app.schemas.review import ReviewCreate, ReviewListResponse, ReviewResponse

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    payload: ReviewCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Attraction).where(Attraction.id == payload.attraction_id))
    attraction = result.scalar_one_or_none()
    if not attraction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attraction not found")

    verified_booking = False
    if payload.booking_id:
        result = await db.execute(
            select(Booking).where(
                Booking.id == payload.booking_id, Booking.tourist_id == current_user.id
            )
        )
        booking = result.scalar_one_or_none()
        if not booking or booking.attraction_id != payload.attraction_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid booking reference"
            )
        verified_booking = True

    review = Review(
        reviewer_id=current_user.id,
        target_type=ReviewTargetType.ATTRACTION,
        target_id=payload.attraction_id,
        attraction_id=payload.attraction_id,
        booking_id=payload.booking_id,
        rating=payload.rating,
        comment=payload.comment,
        is_verified_booking=verified_booking,
    )

    db.add(review)
    await db.flush()
    await db.refresh(review)
    return review


@router.get("/", response_model=ReviewListResponse)
async def list_reviews(
    attraction_id: Optional[UUID] = Query(None, description="Filter reviews by attraction ID"),
    reviewer_id: Optional[UUID] = Query(None, description="Filter reviews by reviewer ID"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Review)
    count_query = select(func.count()).select_from(Review)
    if attraction_id:
        query = query.where(Review.attraction_id == attraction_id)
        count_query = count_query.where(Review.attraction_id == attraction_id)
    if reviewer_id:
        query = query.where(Review.reviewer_id == reviewer_id)
        count_query = count_query.where(Review.reviewer_id == reviewer_id)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(
        query.order_by(Review.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
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

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.attraction import Attraction
from app.models.favorite import Favorite
from app.schemas.favorite import FavoriteCreate, FavoriteListResponse, FavoriteResponse

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.post("/", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def create_favorite(
    payload: FavoriteCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Attraction).where(Attraction.id == payload.attraction_id))
    attraction = result.scalar_one_or_none()
    if not attraction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attraction not found")

    existing = await db.execute(
        select(Favorite).where(
            Favorite.attraction_id == payload.attraction_id,
            Favorite.user_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Attraction already favorited"
        )

    favorite = Favorite(user_id=current_user.id, attraction_id=payload.attraction_id)
    db.add(favorite)
    await db.flush()
    await db.refresh(favorite)
    return favorite


@router.get("/", response_model=FavoriteListResponse)
async def list_favorites(
    attraction_id: Optional[UUID] = Query(None, description="Filter favorites by attraction"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Favorite).where(Favorite.user_id == current_user.id)
    count_query = (
        select(func.count()).select_from(Favorite).where(Favorite.user_id == current_user.id)
    )
    if attraction_id:
        query = query.where(Favorite.attraction_id == attraction_id)
        count_query = count_query.where(Favorite.attraction_id == attraction_id)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(
        query.order_by(Favorite.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
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


@router.delete("/{favorite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_favorite(
    favorite_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Favorite).where(Favorite.id == favorite_id, Favorite.user_id == current_user.id)
    )
    favorite = result.scalar_one_or_none()
    if not favorite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorite not found")

    await db.delete(favorite)
    await db.flush()
    return None

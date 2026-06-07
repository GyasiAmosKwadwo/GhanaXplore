from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.tourism_common import ApprovalStatus
from app.models.user import User
from app.schemas.attraction import (
    AttractionApprovalUpdate,
    AttractionCreate,
    AttractionListResponse,
    AttractionResponse,
    AttractionUpdate,
)
from app.services.attraction_service import AttractionService

router = APIRouter(prefix="/attractions", tags=["Attractions"])


@router.post("/", response_model=AttractionResponse, status_code=status.HTTP_201_CREATED)
async def create_attraction(
    payload: AttractionCreate,
    current_user: User = Depends(require_permission("attraction.create")),
    db: AsyncSession = Depends(get_db),
):
    """Create an attraction. Requires `attraction.create` permission and a verified operator."""
    service = AttractionService(db)
    attraction = await service.create_attraction(current_user, payload)
    return attraction


@router.get("", response_model=AttractionListResponse)
async def list_attractions(
    region: Optional[str] = Query(None, description="Filter by region"),
    category: Optional[str] = Query(None, description="Filter by category"),
    operator_id: Optional[UUID] = Query(None, description="Filter by operator ID"),
    search: Optional[str] = Query(None, description="Search by name, description, region, or district"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List approved attractions for public browsing."""
    skip = (page - 1) * per_page
    filters = {}
    if region:
        filters["region"] = region
    if category:
        filters["category"] = category
    if operator_id:
        filters["operator_id"] = operator_id
    if search:
        filters["search"] = search

    service = AttractionService(db)
    attractions, total = await service.list_public_attractions(filters, skip, per_page, sort_by=sort_by, sort_order=sort_order)

    total_pages = (total + per_page - 1) // per_page if per_page else 0
    return {
        "items": attractions,
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1 and total_pages > 0,
        },
    }


@router.get("/operator/{operator_id}", response_model=AttractionListResponse)
async def list_operator_attractions_by_id(
    operator_id: UUID,
    current_user: User = Depends(get_current_user),
    category: Optional[str] = Query(None, description="Filter by category"),
    region: Optional[str] = Query(None, description="Filter by region"),
    search: Optional[str] = Query(None, description="Search by name, description, region, or district"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Fetch approved attractions for an operator."""
    skip = (page - 1) * per_page
    filters = {"operator_id": operator_id}
    if region:
        filters["region"] = region
    if category:
        filters["category"] = category
    if search:
        filters["search"] = search

    service = AttractionService(db)
    attractions, total = await service.list_public_attractions(filters, skip, per_page, sort_by=sort_by, sort_order=sort_order)

    total_pages = (total + per_page - 1) // per_page if per_page else 0
    return {
        "items": attractions,
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1 and total_pages > 0,
        },
    }


@router.get("/me", response_model=AttractionListResponse)
async def list_my_attractions(
    current_user: User = Depends(get_current_user),
    category: Optional[str] = Query(None, description="Filter by category"),
    region: Optional[str] = Query(None, description="Filter by region"),
    search: Optional[str] = Query(None, description="Search by name, description, region, or district"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List attractions created by the current authenticated operator."""
    skip = (page - 1) * per_page
    filters = {}
    if region:
        filters["region"] = region
    if category:
        filters["category"] = category
    if search:
        filters["search"] = search

    service = AttractionService(db)
    attractions, total = await service.list_operator_attractions(
        current_user.id,
        filters=filters,
        skip=skip,
        limit=per_page,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    total_pages = (total + per_page - 1) // per_page if per_page else 0
    return {
        "items": attractions,
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1 and total_pages > 0,
        },
    }


@router.get("/{attraction_id}", response_model=AttractionResponse)
async def get_attraction(
    attraction_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a public attraction by ID."""
    service = AttractionService(db)
    attraction = await service.get_attraction(attraction_id)
    if not attraction or attraction.approval_status != ApprovalStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attraction not found")
    return attraction


@router.patch("/{attraction_id}", response_model=AttractionResponse)
async def update_attraction(
    attraction_id: UUID,
    payload: AttractionUpdate,
    current_user: User = Depends(require_permission("attraction.update")),
    db: AsyncSession = Depends(get_db),
):
    """Update an attraction. Operators may update their own listings."""
    service = AttractionService(db)
    attraction = await service.update_attraction(current_user, attraction_id, payload.dict(exclude_unset=True))
    return attraction


@router.delete("/{attraction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attraction(
    attraction_id: UUID,
    current_user: User = Depends(require_permission("attraction.delete")),
    db: AsyncSession = Depends(get_db),
):
    """Delete an attraction. Operators may delete their own listings."""
    service = AttractionService(db)
    await service.delete_attraction(current_user, attraction_id)
    return None


@router.patch("/{attraction_id}/approval", response_model=AttractionResponse)
async def approve_attraction(
    attraction_id: UUID,
    payload: AttractionApprovalUpdate,
    current_user: User = Depends(require_permission("attraction.approve")),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject an attraction. Requires review permission."""
    service = AttractionService(db)
    attraction = await service.set_approval_status(attraction_id, payload.approval_status)
    return attraction

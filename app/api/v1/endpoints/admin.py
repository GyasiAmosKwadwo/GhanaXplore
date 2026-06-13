import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_permission
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.audit import AuditLogListResponse
from app.schemas.user import (
    OperatorVerificationUpdate,
    UserResponse,
    UserRoleUpdate,
    UsersListResponse,
    UserStatusUpdate,
)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user_status(
    user_id: uuid.UUID,
    data: UserStatusUpdate,
    current_user: User = Depends(require_permission("user.update")),
    db: AsyncSession = Depends(get_db),
):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.role == UserRole.ADMINISTRATOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot update administrator status"
        )

    await user_repo.update(user_id, data.dict(exclude_unset=True))
    return user


@router.patch("/operators/{user_id}/verification", response_model=UserResponse)
async def update_operator_verification(
    user_id: uuid.UUID,
    data: OperatorVerificationUpdate,
    current_user: User = Depends(require_permission("user.update")),
    db: AsyncSession = Depends(get_db),
):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.role != UserRole.OPERATOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only operator accounts can be verified"
        )

    await user_repo.update(user_id, {"is_verified": data.is_verified})
    return await user_repo.get_by_id(user_id)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: uuid.UUID,
    data: UserRoleUpdate,
    current_user: User = Depends(require_permission("user.update")),
    db: AsyncSession = Depends(get_db),
):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.role == UserRole.ADMINISTRATOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot update administrator role"
        )

    await user_repo.update(user_id, data.dict(exclude_unset=True))
    return user


@router.get("/audit-logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by acting user"),
    action: Optional[str] = Query(None, description="Filter by action code (e.g. attraction.created)"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type (e.g. attraction, booking)"),
    resource_id: Optional[uuid.UUID] = Query(None, description="Filter by resource ID"),
    current_user: User = Depends(require_permission("audit.view")),
    db: AsyncSession = Depends(get_db),
):
    """List platform audit logs for compliance, dispute resolution, and admin review."""
    from app.services.audit_service import AuditService

    skip = (page - 1) * per_page
    service = AuditService(db)
    items, total = await service.list_logs(
        skip=skip,
        limit=per_page,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
    )
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


@router.get("/users", response_model=UsersListResponse)
async def get_all_users(
    per_page: int = 20,
    page: int = 1,
    name: Optional[str] = Query(None, description="Filter users by name"),
    role: Optional[UserRole] = Query(None, description="Filter users by role"),
    is_active: Optional[bool] = Query(None, description="Filter users by active status"),
    last_login: Optional[datetime] = Query(None, description="Filter users by last login"),
    phone_number: Optional[str] = Query(None, description="Filter users by phone number"),
    email: Optional[str] = Query(None, description="Filter users by email"),
    current_user: User = Depends(require_permission("user.view")),
    db: AsyncSession = Depends(get_db),
):
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 20

    skip = (page - 1) * per_page
    filters = {}
    if role is not None:
        filters["role"] = role
    if is_active is not None:
        filters["is_active"] = is_active
    if last_login is not None:
        filters["last_login"] = last_login
    if name is not None:
        filters["name"] = name
    if phone_number is not None:
        filters["phone_number"] = phone_number
    if email is not None:
        filters["email"] = email

    user_repo = UserRepository(db)
    items = await user_repo.get_all(skip, per_page, filters=filters or None)
    total_users = await user_repo.count(filters=filters or None)

    total_pages = (total_users + per_page - 1) // per_page if per_page else 0
    return {
        "items": items,
        "pagination": {
            "total": total_users,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1 and total_pages > 0,
        },
    }


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_permission("user.view")),
    db: AsyncSession = Depends(get_db),
):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user

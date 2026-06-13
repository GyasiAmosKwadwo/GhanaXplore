from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.models.audit import AuditLog
from app.repositories.audit_repository import AuditRepository


class AuditAction:
    # Attractions
    ATTRACTION_CREATED = "attraction.created"
    ATTRACTION_UPDATED = "attraction.updated"
    ATTRACTION_DELETED = "attraction.deleted"
    ATTRACTION_APPROVAL_CHANGED = "attraction.approval_changed"

    # Bookings
    BOOKING_CREATED = "booking.created"
    BOOKING_UPDATED = "booking.updated"
    BOOKING_CANCELLED = "booking.cancelled"
    BOOKING_CONFIRMED = "booking.confirmed"

    # Auth / admin (for future use)
    USER_LOGIN = "user.login"
    USER_VERIFIED = "user.verified"


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AuditRepository(db)

    async def log(
        self,
        context: AuditContext,
        *,
        action: str,
        resource_type: str,
        resource_id: UUID | None = None,
        details: dict[str, Any] | None = None,
        changes: dict[str, Any] | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=context.user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
            details=details or {},
            changes=changes,
        )
        return await self.repo.create(entry)

    async def list_logs(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        user_id: UUID | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        since=None,
        until=None,
    ) -> tuple[list[AuditLog], int]:
        items = await self.repo.list_logs(
            skip=skip,
            limit=limit,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            since=since,
            until=until,
        )
        total = await self.repo.count_logs(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            since=since,
            until=until,
        )
        return items, total

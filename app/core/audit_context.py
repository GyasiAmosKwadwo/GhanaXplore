from dataclasses import dataclass
from uuid import UUID

from fastapi import Request

from app.models.user import User


@dataclass(frozen=True)
class AuditContext:
    user_id: UUID
    ip_address: str | None = None
    user_agent: str | None = None


def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def build_audit_context(request: Request, user: User) -> AuditContext:
    user_agent = request.headers.get("user-agent")
    if user_agent and len(user_agent) > 500:
        user_agent = user_agent[:500]
    return AuditContext(
        user_id=user.id,
        ip_address=get_client_ip(request),
        user_agent=user_agent,
    )

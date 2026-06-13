from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError


def _integrity_detail(exc: IntegrityError) -> str:
    orig = getattr(exc, "orig", None)
    if orig is not None:
        return str(orig)
    return str(exc)


def raise_http_for_integrity(
    exc: IntegrityError,
    *,
    slug_message: str = "An attraction with this slug already exists",
    fallback_message: str = "A record with these values already exists",
) -> None:
    """Translate a database integrity error into an HTTP 409 conflict response."""
    detail = _integrity_detail(exc).lower()
    if "slug" in detail or "attractions_slug" in detail:
        message = slug_message
    else:
        message = fallback_message
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message) from exc

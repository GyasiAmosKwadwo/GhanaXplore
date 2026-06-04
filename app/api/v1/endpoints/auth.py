from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, get_redis
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer_scheme = HTTPBearer()


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Login endpoint"""
    auth_service = AuthService(db, redis)

    # Authenticate user
    user, is_first_time = await auth_service.authenticate_user(credentials.email, credentials.password)

    ip_address = request.client.host
    user_agent = request.headers.get("user-agent", "")

    return await auth_service.create_session(user, ip_address, user_agent, is_first_time)


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Logout endpoint"""
    auth_service = AuthService(db, redis)
    await auth_service.logout(credentials.credentials, user.id)
    return {"message": "Logged out successfully"}

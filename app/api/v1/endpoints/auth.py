from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, get_redis
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, SignupRequest, SignupResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer_scheme = HTTPBearer()


@router.post("/register", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Public signup for tourists and operators.
    """
    auth_service = AuthService(db, None)
    _, response = await auth_service.register_user(
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone_number=payload.phone_number,
        account_type=payload.account_type,
    )
    return response


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
    user, is_first_time = await auth_service.authenticate_user(
        credentials.email, credentials.password
    )

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

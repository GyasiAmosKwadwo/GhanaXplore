from fastapi import APIRouter, Depends, HTTPException, Request, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_redis
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.auth import SignupAccountType
from app.services.auth_service import AuthService

compat_router = APIRouter(prefix="/api", tags=["Compatibility"])


@compat_router.post("/login", response_model=LoginResponse)
async def compat_login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Template-compatible auth login.

    Frontend calls: POST /api/login with { email, password }
    Backend implementation: /api/v1/auth/login
    """
    auth_service = AuthService(db, redis)
    user, is_first_time = await auth_service.authenticate_user(payload.email, payload.password)

    ip_address = request.client.host if request.client else ""
    user_agent = request.headers.get("user-agent", "")

    return await auth_service.create_session(user, ip_address, user_agent, is_first_time)


class CompatSignupRequestLoginStyle(dict):
    pass


@compat_router.post("/register")
async def compat_register(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """Template-compatible auth register.

    Frontend calls: POST /api/register with camelCase keys:
    { firstName, lastName, email, password, phone, role }

    Backend expects snake_case:
    { first_name, last_name, email, password, phone_number, account_type }
    """

    required = ["firstName", "lastName", "email", "password", "phone", "role"]
    missing = [k for k in required if k not in body]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing fields: {', '.join(missing)}",
        )

    role = str(body.get("role")).lower()
    if role == "tourist":
        account_type = SignupAccountType.TOURIST
    elif role == "operator":
        account_type = SignupAccountType.OPERATOR
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")

    auth_service = AuthService(db, None)
    _, response = await auth_service.register_user(
        email=body["email"],
        password=body["password"],
        first_name=body["firstName"],
        last_name=body["lastName"],
        phone_number=body.get("phone"),
        account_type=account_type,
    )
    return response


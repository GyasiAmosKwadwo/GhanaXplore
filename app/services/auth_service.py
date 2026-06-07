from datetime import datetime, timedelta
from typing import Optional, Tuple

from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import SecurityService
from app.models.operator_profile import OperatorProfile
from app.models.tourist_profile import TouristProfile
from app.models.role import Role
from app.models.user import User, UserRole
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginResponse, SignupAccountType, SignupResponse


class AuthService:
    def __init__(self, db: AsyncSession, redis: Redis | None):
        self.db = db
        self.redis = redis
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)
        self.security = SecurityService()

    async def register_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone_number: str | None,
        account_type: SignupAccountType,
    ) -> tuple[User, SignupResponse]:
        """
        Register a public account for a tourist or operator.
        Operators are created as unverified so onboarding can be reviewed later.
        """
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists"
            )

        if phone_number:
            existing_phone = await self.user_repo.get_by_phone(phone_number)
            if existing_phone:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this phone number already exists",
                )

        role_map = {
            SignupAccountType.TOURIST: (UserRole.TOURIST, True, False),
            SignupAccountType.OPERATOR: (UserRole.OPERATOR, False, True),
        }
        user_role, is_verified, requires_review = role_map[account_type]

        role_record: Role | None = await self.role_repo.get_by_code(user_role.value)
        if not role_record:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Role '{user_role.value}' is not configured",
            )

        user = User(
            email=email,
            hashed_password=self.security.get_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            role=user_role,
            is_active=True,
            is_verified=is_verified,
        )
        user.roles.append(role_record)

        self.db.add(user)
        await self.db.flush()

        if account_type == SignupAccountType.TOURIST:
            self.db.add(TouristProfile(user_id=user.id))
        else:
            self.db.add(OperatorProfile(user_id=user.id))
        await self.db.commit()
        await self.db.refresh(user)

        message = (
            "Tourist account created successfully"
            if account_type == SignupAccountType.TOURIST
            else "Operator account created successfully. Verification is required before publishing listings."
        )

        return user, SignupResponse(
            message=message,
            role=user.role,
            is_verified=user.is_verified,
            requires_review=requires_review,
        )

    async def authenticate_user(
        self, email: str, password: str
    ) -> Tuple[Optional[User], bool]:
        """
        Authenticate user and return (user, is_first_time)
        """
        user = await self.user_repo.get_by_email(email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
            )

        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is locked. Please try again later.",
            )

        # Verify password
        if not self.security.verify_password(password, user.hashed_password):
            await self.user_repo.increment_failed_attempts(user.id)

            # Lock account after max attempts
            if user.failed_login_attempts + 1 >= settings.MAX_LOGIN_ATTEMPTS:
                lock_until = datetime.utcnow() + timedelta(
                    minutes=settings.LOCKOUT_DURATION_MINUTES
                )
                await self.user_repo.lock_account(user.id, lock_until)
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account locked due to too many failed attempts",
                )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
            )

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

        # Check if this is the first login before updating the timestamp
        is_first_time = user.last_login is None

        # Reset failed attempts
        await self.user_repo.update_last_login(user.id)

        return user, is_first_time

    async def create_session(
        self, user: User, ip_address: str, user_agent: str, is_first_time: bool = False
    ) -> LoginResponse:
        """Create user session and return tokens"""
        if self.redis is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Session store is not available",
            )

        # Create tokens
        token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
        access_token = self.security.create_access_token(token_data)
        refresh_token = self.security.create_refresh_token(token_data)

        # Store session in Redis
        session_key = f"session:{user.id}:{access_token}"
        session_data = {
            "user_id": user.id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": datetime.utcnow().isoformat(),
        }

        await self.redis.setex(
            session_key, timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES), str(session_data)
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            is_first_time=is_first_time,
            user_id=str(user.id),
        )

    async def logout(self, token: str, user_id) -> None:
        """Logout user and invalidate session"""
        if self.redis is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Session store is not available",
            )

        # Delete session
        session_key = f"session:{user_id}:{token}"
        await self.redis.delete(session_key)

        # Add token to blacklist
        token_exp = self.security.decode_token(token).get("exp")
        if token_exp:
            exp_seconds = token_exp - datetime.utcnow().timestamp()
            if exp_seconds > 0:
                await self.redis.setex(f"blacklist:{token}", int(exp_seconds), "1")

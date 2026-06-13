import asyncio
from datetime import date, timedelta
from decimal import Decimal
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.cache import get_redis
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import SecurityService
from app.main import app

API_PREFIX = f"/api/{settings.API_VERSION}"
from app.models.attraction import Attraction
from app.models.role import Permission, Role, user_roles
from app.models.time_slot import TimeSlot
from app.models.tourism_common import ApprovalStatus, AttractionStatus
from app.models.user import User, UserRole

# Test database URL — override via TEST_DATABASE_URL env for CI/docker.
import os

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://app_user:app_pass@localhost:5433/app_db",
)

test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


class FakeRedis:
    """In-memory Redis substitute for tests (no external Redis required)."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def setex(self, key: str, ttl: int, value: str) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def flushdb(self) -> None:
        self._store.clear()

    async def close(self) -> None:
        pass


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def redis_client() -> AsyncGenerator[FakeRedis, None]:
    redis = FakeRedis()
    yield redis
    await redis.flushdb()
    await redis.close()


@pytest.fixture(scope="function")
async def client(
    db_session: AsyncSession, redis_client: FakeRedis
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    async def override_get_redis():
        return redis_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(app=app, base_url="http://localhost") as ac:
        yield ac

    app.dependency_overrides.clear()


async def _auth_headers(user: User, redis_client: FakeRedis) -> dict[str, str]:
    security = SecurityService()
    token = security.create_access_token(
        {"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    session_key = f"session:{user.id}:{token}"
    await redis_client.setex(session_key, 3600, str({"user_id": str(user.id)}))
    return {"Authorization": f"Bearer {token}"}


OPERATOR_PERMISSION_CODES = [
    "attraction.create",
    "attraction.view",
    "attraction.update",
    "attraction.delete",
    "booking.view",
    "booking.manage",
]

async def _get_or_create_permissions(
    db_session: AsyncSession,
    permission_codes: list[str],
) -> list[Permission]:
    from sqlalchemy import select

    result = await db_session.execute(
        select(Permission).where(Permission.code.in_(permission_codes))
    )
    existing = {perm.code: perm for perm in result.scalars().all()}

    permissions: list[Permission] = []
    for code in permission_codes:
        if code in existing:
            permissions.append(existing[code])
            continue
        perm = Permission(name=code, code=code, module="test", is_active=True)
        db_session.add(perm)
        permissions.append(perm)

    await db_session.flush()
    return permissions


async def _assign_role_with_permissions(
    db_session: AsyncSession,
    user: User,
    role_code: str,
    permission_codes: list[str],
) -> None:
    """Attach an RBAC role with the given permissions to a user."""
    from sqlalchemy import select

    permissions = await _get_or_create_permissions(db_session, permission_codes)

    result = await db_session.execute(select(Role).where(Role.code == role_code))
    role = result.scalar_one_or_none()
    if role is None:
        role = Role(
            name=role_code.title(),
            code=role_code,
            description=f"Test {role_code} role",
            is_active=True,
        )
        role.permissions = permissions
        db_session.add(role)
        await db_session.flush()
    else:
        role.permissions = permissions
        await db_session.flush()

    await db_session.execute(
        user_roles.insert().values(user_id=user.id, role_id=role.id)
    )
    await db_session.commit()
    await db_session.refresh(user)


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    security = SecurityService()
    user = User(
        email="test@example.com",
        hashed_password=security.get_password_hash("Test123!"),
        first_name="Test",
        last_name="User",
        role=UserRole.TOURIST,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_operator(db_session: AsyncSession) -> User:
    security = SecurityService()
    operator = User(
        email="operator@example.com",
        hashed_password=security.get_password_hash("Operator123!"),
        first_name="Op",
        last_name="Erator",
        role=UserRole.OPERATOR,
        is_active=True,
        is_verified=True,
    )
    db_session.add(operator)
    await db_session.commit()
    await db_session.refresh(operator)
    await _assign_role_with_permissions(
        db_session, operator, "operator", OPERATOR_PERMISSION_CODES
    )
    return operator


@pytest.fixture
async def test_admin(db_session: AsyncSession) -> User:
    security = SecurityService()
    admin = User(
        email="admin@example.com",
        hashed_password=security.get_password_hash("Admin123!"),
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMINISTRATOR,
        is_active=True,
        is_verified=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
async def auth_headers(test_user: User, redis_client: FakeRedis) -> dict[str, str]:
    return await _auth_headers(test_user, redis_client)


@pytest.fixture
async def operator_auth_headers(test_operator: User, redis_client: FakeRedis) -> dict[str, str]:
    return await _auth_headers(test_operator, redis_client)


@pytest.fixture
async def admin_auth_headers(test_admin: User, redis_client: FakeRedis) -> dict[str, str]:
    return await _auth_headers(test_admin, redis_client)


@pytest.fixture
async def approved_attraction(db_session: AsyncSession, test_operator: User) -> Attraction:
    attraction = Attraction(
        slug="cape-coast-castle",
        name="Cape Coast Castle",
        region="Central",
        description="Historic castle on the coast of Ghana.",
        category="historical",
        entry_fee_ghs=Decimal("50.00"),
        approval_status=ApprovalStatus.APPROVED,
        status=AttractionStatus.ACTIVE,
        is_available=True,
        operator_id=test_operator.id,
    )
    db_session.add(attraction)
    await db_session.commit()
    await db_session.refresh(attraction)
    return attraction


@pytest.fixture
async def time_slot(db_session: AsyncSession, approved_attraction: Attraction) -> TimeSlot:
    slot = TimeSlot(
        attraction_id=approved_attraction.id,
        start_time="09:00",
        end_time="11:00",
        max_capacity=10,
        is_active=True,
    )
    db_session.add(slot)
    await db_session.commit()
    await db_session.refresh(slot)
    return slot


@pytest.fixture
def visit_date() -> date:
    return date.today() + timedelta(days=7)

import asyncio

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import SecurityService
from app.models.user import User, UserRole


async def create_admin_user(db: AsyncSession) -> User:
    security = SecurityService()
    admin = User(
        email="admin@example.com",
        hashed_password=security.get_password_hash("Admin@123"),
        first_name="Platform",
        last_name="Administrator",
        role=UserRole.ADMINISTRATOR,
        is_active=True,
        is_verified=True,
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


async def seed_database() -> None:
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(User).where(User.email == "admin@example.com"))
            admin_user = result.scalar_one_or_none()

            if admin_user:
                logger.info("Default admin already exists.")
                return

            admin_user = await create_admin_user(db)
            logger.info("GhanaXplore database seeded successfully")
            logger.info("Default admin: admin@example.com / Admin@123")
        except Exception as e:
            logger.error(f"Error seeding database: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_database())

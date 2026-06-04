# ============================================================================
# scripts/create_admin.py
# ============================================================================
"""
Simple script to create an administrator user
Usage: python scripts/create_admin.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import asyncio
import os
from getpass import getpass

from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.security import SecurityService
from app.models.role import Role
from app.models.user import User, UserRole

# Email: admin@ghanaxplore.com
#   Name: John Doe
#   Phone: +15551234567
#   Role: Super Administrator
# Password: Password@12123


def validate_email(email: str) -> bool:
    """Validate email format"""
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one digit"

    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(char.islower() for char in password):
        return False, "Password must contain at least one lowercase letter"

    return True, "Password is valid"


def _candidate_database_urls() -> list[str]:
    """Return database URLs to try, preferring the configured URL."""
    configured = os.environ.get("DATABASE_URL")
    if not configured:
        from app.core.config import settings

        configured = settings.DATABASE_URL

    candidates: list[str] = []
    if configured:
        candidates.append(configured)

        try:
            url = make_url(configured)
            if url.host in {"postgres", "db"}:
                local_variants = [
                    url.set(host="localhost", port=5433),
                    url.set(host="localhost", port=5432),
                ]
                for variant in local_variants:
                    rendered = variant.render_as_string(hide_password=False)
                    if rendered not in candidates:
                        candidates.append(rendered)
        except Exception:
            pass

    return candidates


async def _resolve_sessionmaker() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Find a database URL that is reachable from the local machine."""
    last_error: Exception | None = None
    candidates = _candidate_database_urls()

    for db_url in candidates:
        engine = create_async_engine(db_url, echo=False, future=True, pool_pre_ping=True)
        sessionmaker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        try:
            async with sessionmaker() as db:
                await db.execute(text("SELECT 1"))
            masked = make_url(db_url).render_as_string(hide_password=True)
            logger.info("Using database URL: {}", masked)
            return engine, sessionmaker
        except (OSError, DBAPIError, OperationalError) as exc:
            last_error = exc
            logger.warning("Could not reach database at {}: {}", db_url, exc)
            await engine.dispose()
        except Exception as exc:
            last_error = exc
            logger.warning("Database probe failed for {}: {}", db_url, exc)
            await engine.dispose()

    raise RuntimeError(
        "Unable to connect to any configured database URL. "
        "Check DATABASE_URL, POSTGRES_HOST, and your local Docker port mapping."
    ) from last_error


async def create_admin_user(db: AsyncSession):
    """Interactive admin user creation"""
    print("=" * 60)
    print("GhanaXplore - Create Administrator User")
    print("=" * 60)
    print()

    try:
        # Get email
        while True:
            email = input("Email address: ").strip()

            if not email:
                print("❌ Email is required")
                continue

            if not validate_email(email):
                print("❌ Invalid email format")
                continue

            # Check if user exists
            result = await db.execute(select(User).where(User.email == email))
            if result.scalar_one_or_none():
                print(f"❌ User with email '{email}' already exists")
                continue

            break

        # Get password
        while True:
            password = getpass("Password (min 8 chars, 1 uppercase, 1 digit): ")

            if not password:
                print("❌ Password is required")
                continue

            is_valid, message = validate_password(password)
            if not is_valid:
                print(f"❌ {message}")
                continue

            password_confirm = getpass("Confirm password: ")

            if password != password_confirm:
                print("❌ Passwords do not match")
                continue

            break

        # Get first name
        while True:
            first_name = input("First name: ").strip()
            if first_name:
                break
            print("❌ First name is required")

        # Get last name
        while True:
            last_name = input("Last name: ").strip()
            if last_name:
                break
            print("❌ Last name is required")

        # Get phone number (optional)
        phone_number = input("Phone number (optional, e.g., +15550000000): ").strip() or None

        # Confirm
        print()
        print("-" * 60)
        print("Please confirm the following details:")
        print(f"  Email: {email}")
        print(f"  Name: {first_name} {last_name}")
        print(f"  Phone: {phone_number or 'Not provided'}")
        print("  Role: Super Administrator")
        print("-" * 60)

        confirm = input("Create this user? (yes/no): ").strip().lower()

        if confirm not in ["yes", "y"]:
            print("❌ User creation cancelled")
            return

        # Create user
        logger.info("Creating admin user...")
        security = SecurityService()

        user = User(
            email=email,
            hashed_password=security.get_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            role=UserRole.ADMINISTRATOR,
            is_active=True,
            is_verified=True,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Assign Super Admin role if it exists
        result = await db.execute(select(Role).where(Role.code == "super_admin"))
        super_admin_role = result.scalar_one_or_none()

        if super_admin_role:
            # Insert into user_roles junction table directly
            from sqlalchemy import insert

            from app.models.role import user_roles

            stmt = insert(user_roles).values(user_id=user.id, role_id=super_admin_role.id)
            await db.execute(stmt)
            await db.commit()
            logger.info("Assigned Super Administrator role")
        else:
            logger.warning("Super Admin role not found. User created without custom role.")
            logger.warning("Run 'python scripts/seed_permissions.py' to create roles.")

        print()
        print("=" * 60)
        print("✅ Administrator user created successfully!")
        print("=" * 60)
        print(f"User ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Name: {user.first_name} {user.last_name}")
        print(f"Role: {user.role}")
        if super_admin_role:
            print("Custom Roles: Super Administrator")
        print()
        print("You can now login with these credentials.")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n❌ User creation cancelled")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)


def main():
    """Main function"""
    async def _run():
        engine, sessionmaker = await _resolve_sessionmaker()
        try:
            async with sessionmaker() as db:
                await create_admin_user(db)
        finally:
            await engine.dispose()

    asyncio.run(_run())


if __name__ == "__main__":
    main()

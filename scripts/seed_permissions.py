import asyncio
import sys
from pathlib import Path

from loguru import logger
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import AsyncSessionLocal
from app.models.role import Permission, Role, role_permissions, user_roles
from app.models.user import User


async def seed_permissions(db: AsyncSession) -> list[Permission]:
    permissions_data = [
        {"name": "Create User", "code": "user.create", "module": "users"},
        {"name": "View User", "code": "user.view", "module": "users"},
        {"name": "Update User", "code": "user.update", "module": "users"},
        {"name": "Delete User", "code": "user.delete", "module": "users"},
        {"name": "Create Role", "code": "role.create", "module": "roles"},
        {"name": "View Role", "code": "role.view", "module": "roles"},
        {"name": "Update Role", "code": "role.update", "module": "roles"},
        {"name": "Delete Role", "code": "role.delete", "module": "roles"},
        {"name": "View Notifications", "code": "notification.view", "module": "notifications"},
        {"name": "Manage Notifications", "code": "notification.manage", "module": "notifications"},
        {"name": "View Audit Logs", "code": "audit.view", "module": "audit"},
        {"name": "Create Attraction", "code": "attraction.create", "module": "attractions"},
        {"name": "View Attraction", "code": "attraction.view", "module": "attractions"},
        {"name": "Update Attraction", "code": "attraction.update", "module": "attractions"},
        {"name": "Delete Attraction", "code": "attraction.delete", "module": "attractions"},
        {"name": "Approve Attraction", "code": "attraction.approve", "module": "attractions"},
        {"name": "Create Tour Package", "code": "package.create", "module": "packages"},
        {"name": "View Tour Package", "code": "package.view", "module": "packages"},
        {"name": "Update Tour Package", "code": "package.update", "module": "packages"},
        {"name": "Delete Tour Package", "code": "package.delete", "module": "packages"},
        {"name": "Manage Bookings", "code": "booking.manage", "module": "bookings"},
        {"name": "Create Booking", "code": "booking.create", "module": "bookings"},
        {"name": "View Booking", "code": "booking.view", "module": "bookings"},
        {"name": "Cancel Booking", "code": "booking.cancel", "module": "bookings"},
        {"name": "Confirm Booking", "code": "booking.confirm", "module": "bookings"},
        {"name": "View Payments", "code": "payment.view", "module": "payments"},
        {"name": "Confirm Payment", "code": "payment.confirm", "module": "payments"},
        {"name": "Refund Payment", "code": "payment.refund", "module": "payments"},
        {"name": "Create Review", "code": "review.create", "module": "reviews"},
        {"name": "View Review", "code": "review.view", "module": "reviews"},
        {"name": "Moderate Review", "code": "review.moderate", "module": "reviews"},
        {"name": "Create Guide Profile", "code": "guide.create", "module": "guides"},
        {"name": "View Guide Profile", "code": "guide.view", "module": "guides"},
        {"name": "Update Guide Profile", "code": "guide.update", "module": "guides"},
        {"name": "Verify Guide", "code": "guide.verify", "module": "guides"},
        {"name": "Create Offline Bundle", "code": "offline_bundle.create", "module": "offline"},
        {"name": "View Offline Bundle", "code": "offline_bundle.view", "module": "offline"},
        {"name": "Update Offline Bundle", "code": "offline_bundle.update", "module": "offline"},
        {"name": "Create Event", "code": "event.create", "module": "events"},
        {"name": "View Event", "code": "event.view", "module": "events"},
        {"name": "Update Event", "code": "event.update", "module": "events"},
        {"name": "Approve Event", "code": "event.approve", "module": "events"},
        {"name": "Create Community Experience", "code": "community.create", "module": "community"},
        {"name": "View Community Experience", "code": "community.view", "module": "community"},
        {"name": "Update Community Experience", "code": "community.update", "module": "community"},
        {"name": "Approve Community Experience", "code": "community.approve", "module": "community"},
        {"name": "View Analytics", "code": "analytics.view", "module": "analytics"},
        {"name": "Export Analytics", "code": "analytics.export", "module": "analytics"},
    ]

    codes = [perm["code"] for perm in permissions_data]
    existing = await db.execute(select(Permission).where(Permission.code.in_(codes)))
    existing_by_code = {perm.code: perm for perm in existing.scalars().all()}

    created_count = 0
    for perm_data in permissions_data:
        if perm_data["code"] not in existing_by_code:
            permission = Permission(**perm_data)
            db.add(permission)
            existing_by_code[perm_data["code"]] = permission
            created_count += 1

    await db.commit()
    logger.info(f"Created {created_count} permissions")
    return [existing_by_code[perm["code"]] for perm in permissions_data]


async def seed_roles(db: AsyncSession, permissions: list[Permission]) -> None:
    role_specs = {
        "super_admin": {
            "name": "Super Administrator",
            "description": "Full system access",
            "permissions": [perm.code for perm in permissions],
            "is_system_role": True,
            "is_admin_role": True,
        },
        "tourist": {
            "name": "Tourist",
            "description": "Domestic and international traveller",
            "permissions": [
                "attraction.view",
                "package.view",
                "booking.create",
                "booking.view",
                "payment.view",
                "review.create",
                "offline_bundle.view",
                "event.view",
                "guide.view",
                "community.view",
            ],
        },
        "operator": {
            "name": "Operator",
            "description": "Manages attractions and packages",
            "permissions": [
                "attraction.create",
                "attraction.view",
                "attraction.update",
                "attraction.delete",
                "package.create",
                "package.view",
                "package.update",
                "booking.view",
                "booking.manage",
                "payment.view",
                "review.view",
                "analytics.view",
            ],
        },
        "guide": {
            "name": "Guide",
            "description": "Verified tour guide",
            "permissions": [
                "guide.view",
                "guide.update",
                "booking.view",
                "booking.manage",
                "review.view",
            ],
        },
        "community_host": {
            "name": "Community Host",
            "description": "Hosts community-based experiences",
            "permissions": [
                "community.create",
                "community.view",
                "community.update",
                "booking.view",
                "booking.manage",
                "analytics.view",
            ],
        },
        "attraction_manager": {
            "name": "Attraction Manager",
            "description": "Manages attraction operations",
            "permissions": [
                "attraction.create",
                "attraction.view",
                "attraction.update",
                "attraction.approve",
                "booking.view",
                "booking.manage",
                "review.moderate",
                "analytics.view",
            ],
        },
        "government": {
            "name": "Government",
            "description": "Read-only analytics and compliance access",
            "permissions": ["attraction.view", "booking.view", "analytics.view", "analytics.export"],
        },
        "investor": {
            "name": "Investor",
            "description": "Reviews tourism investment opportunities",
            "permissions": ["attraction.view", "event.view", "analytics.view"],
        },
    }

    seeded_roles: dict[str, Role] = {}
    for code, spec in role_specs.items():
        result = await db.execute(select(Role).where(Role.code == code))
        role = result.scalar_one_or_none()
        if role is None:
            role = Role(
                name=spec["name"],
                code=code,
                description=spec["description"],
                is_system_role=spec.get("is_system_role", False),
                is_admin_role=spec.get("is_admin_role", False),
                is_active=True,
            )
            db.add(role)
            await db.flush()
        else:
            role.name = spec["name"]
            role.description = spec["description"]
            role.is_system_role = spec.get("is_system_role", False)
            role.is_admin_role = spec.get("is_admin_role", False)
            role.is_active = True
        seeded_roles[code] = role

        role_permissions_to_add = [
            {"role_id": role.id, "permission_id": permission.id}
            for permission in permissions
            if permission.code in spec["permissions"]
        ]
        if role_permissions_to_add:
            stmt = pg_insert(role_permissions).values(role_permissions_to_add)
            stmt = stmt.on_conflict_do_nothing(index_elements=["role_id", "permission_id"])
            await db.execute(stmt)

    super_admin_role = seeded_roles["super_admin"]

    admin_result = await db.execute(select(User.id).where(User.email == "admin@example.com"))
    admin_user_id = admin_result.scalar_one_or_none()
    if admin_user_id:
        stmt = pg_insert(user_roles).values(
            {"user_id": admin_user_id, "role_id": super_admin_role.id}
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["user_id", "role_id"])
        await db.execute(stmt)
        logger.info("Assigned Super Admin role to admin user")
    else:
        logger.warning("Admin user not found; skipping role assignment")

    await db.commit()


async def seed_permissions_and_roles() -> None:
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Seeding permissions and roles...")
            permissions = await seed_permissions(db)
            await seed_roles(db, permissions)
            logger.info("Permissions and roles seeded successfully")
        except Exception as e:
            logger.error(f"Error seeding permissions and roles: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_permissions_and_roles())

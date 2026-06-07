from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    auth,
    notifications,
    password,
    profiles,
    roles,
    users,
    attractions,
)

api_router = APIRouter()

# Authentication
api_router.include_router(auth.router)

api_router.include_router(password.router)

# Roles & Permissions
api_router.include_router(roles.router)

# Notifications
api_router.include_router(notifications.router)

# Profiles
api_router.include_router(profiles.router)

# Attractions
api_router.include_router(attractions.router)

# Admin
api_router.include_router(admin.router)

# Users
api_router.include_router(users.router)

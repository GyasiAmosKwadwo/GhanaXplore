import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.role import user_roles

# from datetime import datetime


class UserRole(str, enum.Enum):
    TOURIST = "tourist"
    OPERATOR = "operator"
    GUIDE = "guide"
    COMMUNITY_HOST = "community_host"
    ATTRACTION_MANAGER = "attraction_manager"
    GOVERNMENT = "government"
    INVESTOR = "investor"
    ADMINISTRATOR = "administrator"


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone_number = Column(String(20))

    from sqlalchemy import Enum

    # Use native Postgres enum type for the `role` column so values are bound
    # as the DB enum type (avoids varchar -> enum mismatch on INSERT).
    role = Column(
        Enum(
            UserRole,
            # Map DB enum labels to enum member NAMES (the DB stores uppercase
            # names like 'ADMINISTRATOR'). This lets SQLAlchemy load those
            # labels into the `UserRole` enum correctly.
            values_callable=lambda enum: [member.name for member in enum],
            native_enum=True,
            name="userrole",
        ),
        nullable=False,
        default=UserRole.TOURIST,
    )
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Session tracking
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    audit_logs = relationship(
        "AuditLog",
        back_populates="user",
        foreign_keys="[AuditLog.user_id]",
        cascade="all, delete-orphan",
    )
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    operator_profile = relationship(
        "OperatorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    tourist_profile = relationship(
        "TouristProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

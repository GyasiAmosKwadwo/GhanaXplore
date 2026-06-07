import enum

from sqlalchemy import Column, Enum, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class AttractionStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_APPROVAL = "pending_approval"


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class ReviewTargetType(str, enum.Enum):
    ATTRACTION = "attraction"
    PACKAGE = "package"
    GUIDE = "guide"
    COMMUNITY = "community"


tour_package_attractions = Table(
    "tour_package_attractions",
    Base.metadata,
    Column(
        "tour_package_id",
        UUID(as_uuid=True),
        ForeignKey("tour_packages.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "attraction_id",
        UUID(as_uuid=True),
        ForeignKey("attractions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


event_attractions = Table(
    "event_attractions",
    Base.metadata,
    Column(
        "event_id",
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "attraction_id",
        UUID(as_uuid=True),
        ForeignKey("attractions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

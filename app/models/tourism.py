import enum
import uuid

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Boolean,
    Integer,
    JSON,
    Numeric,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


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


class Attraction(Base):
    __tablename__ = "attractions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(255), nullable=False, index=True)
    region = Column(String(120), nullable=False, index=True)
    district = Column(String(120), nullable=True, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)
    gps_latitude = Column(Float, nullable=True)
    gps_longitude = Column(Float, nullable=True)
    opening_hours = Column(String(255), nullable=True)
    entry_fee_ghs = Column(Numeric(12, 2), nullable=True)
    readiness_score = Column(Integer, nullable=False, default=5)
    accessibility_rating = Column(Integer, nullable=True)
    approval_status = Column(Enum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING)
    is_offline_available = Column(Boolean, nullable=False, default=False)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    operator_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    operator = relationship("User", foreign_keys=[operator_id])
    tour_packages = relationship(
        "TourPackage",
        secondary=tour_package_attractions,
        back_populates="attractions",
    )
    offline_bundle = relationship("OfflineBundle", back_populates="attraction", uselist=False)
    reviews = relationship("Review", back_populates="attraction")


class TourPackage(Base):
    __tablename__ = "tour_packages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    operator_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    duration = Column(String(80), nullable=True)
    group_size_limit = Column(Integer, nullable=True)
    price_ghs = Column(Numeric(12, 2), nullable=False)
    price_usd = Column(Numeric(12, 2), nullable=True)
    status = Column(Enum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    operator = relationship("User", foreign_keys=[operator_id])
    attractions = relationship(
        "Attraction",
        secondary=tour_package_attractions,
        back_populates="tour_packages",
    )
    bookings = relationship("Booking", back_populates="tour_package")
    reviews = relationship("Review", back_populates="tour_package")


class GuideProfile(Base):
    __tablename__ = "guide_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    specialisations = Column(JSON, nullable=False, default=list)
    languages = Column(JSON, nullable=False, default=list)
    certification_body = Column(String(255), nullable=True)
    years_experience = Column(Integer, nullable=True)
    hourly_rate_ghs = Column(Numeric(12, 2), nullable=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    rating = Column(Numeric(3, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", uselist=False)
    bookings = relationship("Booking", back_populates="guide")
    reviews = relationship("Review", back_populates="guide")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    tourist_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attraction_id = Column(
        UUID(as_uuid=True), ForeignKey("attractions.id", ondelete="SET NULL"), nullable=True
    )
    tour_package_id = Column(
        UUID(as_uuid=True), ForeignKey("tour_packages.id", ondelete="SET NULL"), nullable=True
    )
    guide_id = Column(
        UUID(as_uuid=True), ForeignKey("guide_profiles.id", ondelete="SET NULL"), nullable=True
    )
    booking_reference = Column(String(64), unique=True, nullable=False, index=True)
    booking_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    visit_date = Column(Date, nullable=False, index=True)
    party_size = Column(Integer, nullable=False, default=1)
    total_amount_ghs = Column(Numeric(12, 2), nullable=False)
    status = Column(Enum(BookingStatus), nullable=False, default=BookingStatus.PENDING)
    qr_code_token = Column(String(255), nullable=True, unique=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    tourist = relationship("User")
    attraction = relationship("Attraction")
    tour_package = relationship("TourPackage", back_populates="bookings")
    guide = relationship("GuideProfile", back_populates="bookings")
    payment = relationship("Payment", back_populates="booking", uselist=False)
    review = relationship("Review", back_populates="booking", uselist=False)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    booking_id = Column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    method = Column(String(40), nullable=False)
    currency_code = Column(String(8), nullable=False, default="GHS")
    amount_local = Column(Numeric(12, 2), nullable=False)
    amount_ghs = Column(Numeric(12, 2), nullable=False)
    exchange_rate = Column(Numeric(12, 6), nullable=True)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    gateway_reference = Column(String(255), nullable=True, index=True)
    payment_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    booking = relationship("Booking", back_populates="payment")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    reviewer_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_type = Column(Enum(ReviewTargetType), nullable=False, index=True)
    target_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    attraction_id = Column(
        UUID(as_uuid=True), ForeignKey("attractions.id", ondelete="SET NULL"), nullable=True
    )
    tour_package_id = Column(
        UUID(as_uuid=True), ForeignKey("tour_packages.id", ondelete="SET NULL"), nullable=True
    )
    guide_id = Column(
        UUID(as_uuid=True), ForeignKey("guide_profiles.id", ondelete="SET NULL"), nullable=True
    )
    booking_id = Column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True, unique=True
    )
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    is_verified_booking = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    reviewer = relationship("User")
    attraction = relationship("Attraction", back_populates="reviews")
    tour_package = relationship("TourPackage", back_populates="reviews")
    guide = relationship("GuideProfile", back_populates="reviews")
    booking = relationship("Booking", back_populates="review")


class OfflineBundle(Base):
    __tablename__ = "offline_bundles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    attraction_id = Column(
        UUID(as_uuid=True), ForeignKey("attractions.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    content_payload = Column(JSON, nullable=False, default=dict)
    compressed_images_url = Column(String(500), nullable=True)
    bundle_size_kb = Column(Integer, nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    version = Column(String(32), nullable=False, default="1.0")

    attraction = relationship("Attraction", back_populates="offline_bundle")


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(255), nullable=False, index=True)
    region = Column(String(120), nullable=False, index=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False)
    description = Column(Text, nullable=False)
    organizer_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    approval_status = Column(Enum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    organizer = relationship("User")
    attractions = relationship(
        "Attraction",
        secondary=event_attractions,
        backref="events",
    )


class CommunityExperience(Base):
    __tablename__ = "community_experiences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    community_host_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    region = Column(String(120), nullable=False, index=True)
    district = Column(String(120), nullable=True)
    gps_latitude = Column(Float, nullable=True)
    gps_longitude = Column(Float, nullable=True)
    price_ghs = Column(Numeric(12, 2), nullable=False)
    max_group_size = Column(Integer, nullable=True)
    jobs_supported = Column(Integer, nullable=True)
    households_supported = Column(Integer, nullable=True)
    eco_rating = Column(Integer, nullable=True)
    approval_status = Column(Enum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    community_host = relationship("User")

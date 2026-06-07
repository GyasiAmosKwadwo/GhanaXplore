import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.tourism_common import ApprovalStatus, AttractionStatus, tour_package_attractions


class Attraction(Base):
    __tablename__ = "attractions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    short_description = Column(String(500), nullable=True)
    region = Column(String(120), nullable=False, index=True)
    location = Column(String(255), nullable=True, index=True)
    district = Column(String(120), nullable=True, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)
    gps_latitude = Column(Float, nullable=True)
    gps_longitude = Column(Float, nullable=True)
    opening_hours = Column(String(255), nullable=True)
    entry_fee_ghs = Column(Numeric(12, 2), nullable=True)
    is_available = Column(Boolean, nullable=False, default=True)
    readiness_score = Column(Integer, nullable=False, default=5)
    accessibility_rating = Column(Integer, nullable=True)
    approval_status = Column(
        Enum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING
    )
    status = Column(Enum(AttractionStatus), nullable=False, default=AttractionStatus.PENDING_APPROVAL)
    images = Column(JSON, nullable=False, default=list)
    amenities = Column(JSON, nullable=False, default=list)
    includes = Column(JSON, nullable=False, default=list)
    excludes = Column(JSON, nullable=False, default=list)
    cancellation_policy = Column(Text, nullable=True)
    special_requirements = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=False, default=dict)

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
    schedules = relationship("Schedule", back_populates="attraction")
    time_slots = relationship("TimeSlot", back_populates="attraction")
    reviews = relationship("Review", back_populates="attraction")

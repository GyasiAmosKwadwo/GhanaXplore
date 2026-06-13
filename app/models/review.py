import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.tourism_common import ReviewTargetType


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
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
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

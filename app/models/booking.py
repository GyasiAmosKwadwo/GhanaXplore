import uuid

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.tourism_common import BookingStatus


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
    time_slot_id = Column(
        UUID(as_uuid=True), ForeignKey("time_slots.id", ondelete="SET NULL"), nullable=True, index=True
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
    time_slot = relationship("TimeSlot")
    tour_package = relationship("TourPackage", back_populates="bookings")
    guide = relationship("GuideProfile", back_populates="bookings")
    payment = relationship("Payment", back_populates="booking", uselist=False)
    review = relationship("Review", back_populates="booking", uselist=False)

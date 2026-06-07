import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.tourism_common import ApprovalStatus, tour_package_attractions


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

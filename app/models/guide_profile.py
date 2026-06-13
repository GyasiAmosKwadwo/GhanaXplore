import uuid

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


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

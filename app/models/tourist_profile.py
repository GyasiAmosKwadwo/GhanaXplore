import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class TouristProfile(Base):
    __tablename__ = "tourist_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    preferred_language = Column(String(40), nullable=True)
    nationality = Column(String(80), nullable=True)
    home_region = Column(String(120), nullable=True)
    bio = Column(Text, nullable=True)
    interests = Column(JSON, nullable=False, default=list)
    travel_preferences = Column(JSON, nullable=False, default=list)
    accessibility_needs = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="tourist_profile", uselist=False)

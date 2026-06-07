import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class OperatorProfile(Base):
    __tablename__ = "operator_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    business_name = Column(String(255), nullable=True, index=True)
    business_description = Column(Text, nullable=True)
    region = Column(String(120), nullable=True, index=True)
    district = Column(String(120), nullable=True, index=True)
    website = Column(String(255), nullable=True)
    license_number = Column(String(120), nullable=True, index=True)
    registration_number = Column(String(120), nullable=True, index=True)
    is_public = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="operator_profile", uselist=False)

import uuid

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.tourism_common import ApprovalStatus


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

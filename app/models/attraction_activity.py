import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AttractionActivity(Base):
    __tablename__ = "attraction_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    attraction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("attractions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)

    price_ghs = Column(Numeric(12, 2), nullable=True)
    price_usd = Column(Numeric(12, 2), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    max_participants = Column(Integer, nullable=True)

    includes = Column(JSON, nullable=False, default=list)
    excludes = Column(JSON, nullable=False, default=list)
    restrictions = Column(JSON, nullable=False, default=dict)
    images = Column(JSON, nullable=False, default=list)
    metadata_ = Column("metadata", JSON, nullable=False, default=dict)
    # NOTE: reserved SQLAlchemy Declarative 'metadata' conflict, using metadata_ attribute.

    is_available = Column(Boolean, nullable=False, default=True)
    requires_advance_booking = Column(Boolean, nullable=False, default=False)
    display_order = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    attraction = relationship("Attraction", back_populates="activities")

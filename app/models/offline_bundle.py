import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class OfflineBundle(Base):
    __tablename__ = "offline_bundles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    attraction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("attractions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    content_payload = Column(JSON, nullable=False, default=dict)
    compressed_images_url = Column(String(500), nullable=True)
    bundle_size_kb = Column(Integer, nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    version = Column(String(32), nullable=False, default="1.0")

    attraction = relationship("Attraction", back_populates="offline_bundle")

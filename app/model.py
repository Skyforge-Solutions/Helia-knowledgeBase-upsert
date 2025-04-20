from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class ResourceLink(Base):
    __tablename__ = "resource_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    link = Column(Text, nullable=False)
    type = Column(String(10), nullable=False)       # 'pdf' or 'url'
    bot = Column(String(50), nullable=False)         # selector value
    status = Column(String(20), default="pending", nullable=False)
    error_message = Column(Text, nullable=True)
    submitted_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
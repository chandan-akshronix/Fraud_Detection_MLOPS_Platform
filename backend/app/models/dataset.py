"""
Dataset SQLAlchemy Model
Database model for dataset management.
"""
from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Column, String, Integer, BigInteger, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Dataset(Base):
    """Dataset model for storing uploaded datasets metadata."""
    
    __tablename__ = "datasets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=False, default="1.0")
    
    # Storage
    storage_path = Column(String(500), nullable=False)
    file_format = Column(String(50), default="parquet")
    file_size_bytes = Column(BigInteger, nullable=True)
    
    # Data info
    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)
    schema = Column(JSON, nullable=True)  # Column definitions
    statistics = Column(JSON, nullable=True)  # Column statistics
    
    # Status and lifecycle
    status = Column(String(50), default="ACTIVE", index=True)  # ACTIVE, ARCHIVED, PROCESSING
    parent_id = Column(UUID(as_uuid=True), nullable=True)  # For versioning
    
    # Audit
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    feature_sets = relationship("FeatureSet", back_populates="dataset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Dataset {self.name} v{self.version}>"

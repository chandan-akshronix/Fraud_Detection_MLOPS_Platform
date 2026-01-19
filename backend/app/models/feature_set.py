"""
Feature Set SQLAlchemy Model
Database model for computed feature sets.
"""
from datetime import datetime
import uuid

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class FeatureSet(Base):
    """Feature set model for computed features."""
    
    __tablename__ = "feature_sets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=False, default="1.0")
    
    # Configuration
    config = Column(JSON, nullable=False)  # Feature engineering config
    
    # Results
    all_features = Column(JSON, nullable=True)  # All generated features
    selected_features = Column(JSON, nullable=True)  # After selection
    selection_report = Column(JSON, nullable=True)  # MI scores, rankings
    
    # Storage
    storage_path = Column(String(500), nullable=True)
    
    # Stats
    input_rows = Column(Integer, nullable=True)
    feature_count = Column(Integer, nullable=True)
    selected_feature_count = Column(Integer, nullable=True)
    
    # Status
    status = Column(String(50), default="PENDING", index=True)  # PENDING, PROCESSING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    processing_time_seconds = Column(Integer, nullable=True)
    
    # Audit
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    dataset = relationship("Dataset", back_populates="feature_sets")
    
    def __repr__(self):
        return f"<FeatureSet {self.name} v{self.version}>"

"""
Feature Service
Business logic for feature engineering operations.
"""
from typing import Optional, Tuple, List, Dict, Any
from uuid import UUID
import logging

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feature_set import FeatureSet
from app.models.dataset import Dataset

logger = logging.getLogger(__name__)


class FeatureService:
    """Service for feature engineering operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_feature_sets(
        self,
        dataset_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[FeatureSet], int]:
        """List feature sets with pagination and filtering."""
        query = select(FeatureSet).order_by(FeatureSet.created_at.desc())
        count_query = select(func.count(FeatureSet.id))
        
        if dataset_id:
            query = query.where(FeatureSet.dataset_id == UUID(dataset_id))
            count_query = count_query.where(FeatureSet.dataset_id == UUID(dataset_id))
        
        if status:
            query = query.where(FeatureSet.status == status)
            count_query = count_query.where(FeatureSet.status == status)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        feature_sets = result.scalars().all()
        
        return list(feature_sets), total
    
    async def get_feature_set(self, feature_set_id: str) -> Optional[FeatureSet]:
        """Get a single feature set by ID."""
        try:
            uuid_id = UUID(feature_set_id)
        except ValueError:
            return None
        
        result = await self.db.execute(
            select(FeatureSet).where(FeatureSet.id == uuid_id)
        )
        return result.scalar_one_or_none()
    
    async def create_feature_set(
        self,
        dataset_id: str,
        name: str,
        config: Dict[str, Any],
        description: Optional[str] = None,
    ) -> FeatureSet:
        """Create a new feature set and trigger computation."""
        # Verify dataset exists
        dataset = await self.db.execute(
            select(Dataset).where(Dataset.id == UUID(dataset_id))
        )
        if not dataset.scalar_one_or_none():
            raise ValueError(f"Dataset {dataset_id} not found")
        
        # Create feature set record
        feature_set = FeatureSet(
            dataset_id=UUID(dataset_id),
            name=name,
            description=description,
            config=config,
            status="QUEUED",
        )
        
        self.db.add(feature_set)
        await self.db.commit()
        await self.db.refresh(feature_set)
        
        # Trigger async computation
        from app.workers.feature_worker import compute_features
        compute_features.delay(str(feature_set.id))
        
        logger.info(f"Created feature set {feature_set.id}, computation queued")
        return feature_set
    
    async def update_feature_set_status(
        self,
        feature_set_id: str,
        status: str,
        progress: float = None,
        error_message: str = None,
        selected_features: List[str] = None,
        selection_report: Dict = None,
    ) -> bool:
        """Update feature set status and results."""
        try:
            uuid_id = UUID(feature_set_id)
        except ValueError:
            return False
        
        update_data = {"status": status}
        if selected_features:
            update_data["selected_features"] = selected_features
            update_data["selected_feature_count"] = len(selected_features)
        if selection_report:
            update_data["selection_report"] = selection_report
        if error_message:
            update_data["error_message"] = error_message
        if status == "COMPLETED":
            from datetime import datetime
            update_data["completed_at"] = datetime.utcnow()
        
        await self.db.execute(
            update(FeatureSet)
            .where(FeatureSet.id == uuid_id)
            .values(**update_data)
        )
        await self.db.commit()
        return True
    
    async def delete_feature_set(self, feature_set_id: str) -> bool:
        """Delete a feature set."""
        feature_set = await self.get_feature_set(feature_set_id)
        if not feature_set:
            return False
        
        await self.db.delete(feature_set)
        await self.db.commit()
        return True
    
    async def get_default_config(self) -> Dict[str, Any]:
        """Get default feature engineering configuration."""
        return {
            "transaction_features": True,
            "behavioral_features": True,
            "temporal_features": True,
            "aggregation_features": True,
            "aggregation_windows": ["1h", "24h", "7d"],
            "enable_feature_selection": True,
            "max_features": 30,
            "variance_threshold": 0.01,
            "correlation_threshold": 0.95,
        }

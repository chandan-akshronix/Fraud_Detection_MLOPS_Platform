"""
Training Service
Business logic for model training operations.
"""
from typing import Optional, Tuple, List, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ml_model import MLModel, Baseline

logger = logging.getLogger(__name__)


# Training job model (stored in DB)
class TrainingJob:
    """Training job representation."""
    pass


class TrainingService:
    """Service for model training operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_training_jobs(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict], int]:
        """List training jobs with pagination."""
        # For now, return mock data until training_jobs model is added
        mock_jobs = [
            {
                "id": "job-001",
                "name": "XGBoost Fraud Model v1",
                "algorithm": "xgboost",
                "status": "COMPLETED",
                "progress": 1.0,
                "created_at": datetime.utcnow().isoformat(),
                "metrics": {"precision": 0.92, "recall": 0.88, "f1": 0.90, "auc": 0.95}
            },
            {
                "id": "job-002", 
                "name": "LightGBM Experiment",
                "algorithm": "lightgbm",
                "status": "RUNNING",
                "progress": 0.65,
                "created_at": datetime.utcnow().isoformat(),
                "metrics": None
            },
        ]
        return mock_jobs, len(mock_jobs)
    
    async def create_training_job(
        self,
        name: str,
        feature_set_id: str,
        algorithm: str,
        hyperparameters: Dict[str, Any],
    ) -> Dict:
        """Create a new training job."""
        job_id = str(UUID(int=0))  # Generate proper UUID
        
        job = {
            "id": job_id,
            "name": name,
            "feature_set_id": feature_set_id,
            "algorithm": algorithm,
            "hyperparameters": hyperparameters,
            "status": "QUEUED",
            "progress": 0.0,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Trigger async training
        from app.workers.training_worker import train_model
        train_model.delay(job_id)
        
        logger.info(f"Created training job {job_id}")
        return job
    
    async def get_training_job(self, job_id: str) -> Optional[Dict]:
        """Get training job status."""
        # Mock implementation
        return {
            "id": job_id,
            "name": "Training Job",
            "status": "RUNNING",
            "progress": 0.5,
        }
    
    async def list_algorithms(self) -> List[Dict]:
        """List available ML algorithms."""
        return [
            {
                "id": "xgboost",
                "name": "XGBoost",
                "description": "Gradient boosting optimized for tabular data. Best for fraud detection.",
                "hyperparameters": [
                    {"name": "n_estimators", "type": "int", "default": 100, "min": 10, "max": 500},
                    {"name": "max_depth", "type": "int", "default": 6, "min": 2, "max": 15},
                    {"name": "learning_rate", "type": "float", "default": 0.1, "min": 0.01, "max": 1.0},
                    {"name": "subsample", "type": "float", "default": 0.8, "min": 0.5, "max": 1.0},
                    {"name": "colsample_bytree", "type": "float", "default": 0.8, "min": 0.5, "max": 1.0},
                ],
            },
            {
                "id": "lightgbm",
                "name": "LightGBM",
                "description": "Fast gradient boosting with leaf-wise tree growth.",
                "hyperparameters": [
                    {"name": "n_estimators", "type": "int", "default": 100, "min": 10, "max": 500},
                    {"name": "max_depth", "type": "int", "default": -1, "min": -1, "max": 20},
                    {"name": "learning_rate", "type": "float", "default": 0.1, "min": 0.01, "max": 1.0},
                    {"name": "num_leaves", "type": "int", "default": 31, "min": 10, "max": 100},
                ],
            },
            {
                "id": "random_forest",
                "name": "Random Forest",
                "description": "Ensemble of decision trees with bagging.",
                "hyperparameters": [
                    {"name": "n_estimators", "type": "int", "default": 100, "min": 10, "max": 500},
                    {"name": "max_depth", "type": "int", "default": 10, "min": 2, "max": 30},
                    {"name": "min_samples_split", "type": "int", "default": 2, "min": 2, "max": 20},
                ],
            },
            {
                "id": "isolation_forest",
                "name": "Isolation Forest",
                "description": "Unsupervised anomaly detection. No labels required.",
                "hyperparameters": [
                    {"name": "n_estimators", "type": "int", "default": 100, "min": 50, "max": 300},
                    {"name": "contamination", "type": "float", "default": 0.05, "min": 0.01, "max": 0.5},
                ],
            },
        ]
    
    async def get_default_hyperparameters(self, algorithm: str) -> Dict[str, Any]:
        """Get default hyperparameters for an algorithm."""
        algorithms = await self.list_algorithms()
        for algo in algorithms:
            if algo["id"] == algorithm:
                return {hp["name"]: hp["default"] for hp in algo["hyperparameters"]}
        return {}


class ModelService:
    """Service for model registry operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_models(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[MLModel], int]:
        """List models with pagination."""
        query = select(MLModel).order_by(MLModel.created_at.desc())
        count_query = select(func.count(MLModel.id))
        
        if status:
            query = query.where(MLModel.status == status)
            count_query = count_query.where(MLModel.status == status)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        models = result.scalars().all()
        
        return list(models), total
    
    async def get_model(self, model_id: str) -> Optional[MLModel]:
        """Get a single model by ID."""
        try:
            uuid_id = UUID(model_id)
        except ValueError:
            return None
        
        result = await self.db.execute(
            select(MLModel).where(MLModel.id == uuid_id)
        )
        return result.scalar_one_or_none()
    
    async def get_production_model(self) -> Optional[MLModel]:
        """Get the current production model."""
        result = await self.db.execute(
            select(MLModel).where(MLModel.status == "PRODUCTION")
        )
        return result.scalar_one_or_none()
    
    async def promote_model(
        self,
        model_id: str,
        target_status: str,
    ) -> Optional[MLModel]:
        """Promote a model to a new status."""
        model = await self.get_model(model_id)
        if not model:
            return None
        
        # If promoting to PRODUCTION, demote current production
        if target_status == "PRODUCTION":
            current_prod = await self.get_production_model()
            if current_prod and str(current_prod.id) != model_id:
                current_prod.status = "ARCHIVED"
                current_prod.archived_at = datetime.utcnow()
                current_prod.archived_reason = "Replaced by new production model"
        
        model.status = target_status
        if target_status == "PRODUCTION":
            model.promoted_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(model)
        
        logger.info(f"Model {model_id} promoted to {target_status}")
        return model
    
    async def set_baselines(
        self,
        model_id: str,
        baselines: List[Dict],
    ) -> List[Baseline]:
        """Set baseline thresholds for a model."""
        model = await self.get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
        
        created_baselines = []
        for b in baselines:
            baseline = Baseline(
                model_id=UUID(model_id),
                metric_name=b["metric"],
                threshold=b["threshold"],
                operator=b.get("operator", "gte"),
            )
            self.db.add(baseline)
            created_baselines.append(baseline)
        
        await self.db.commit()
        return created_baselines

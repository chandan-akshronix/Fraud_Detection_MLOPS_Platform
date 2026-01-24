"""
Dashboard Statistics API Endpoints
Provides aggregated statistics for the dashboard.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.dataset import Dataset
from app.models.ml_model import MLModel

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregated statistics for the dashboard.
    
    Returns:
    - total_datasets: Total number of datasets
    - total_training_jobs: Total number of training jobs
    - active_training_jobs: Number of active/running training jobs
    - production_models: Number of models in production
    - active_alerts: Number of active alerts (placeholder for now)
    """
    
    # Count total datasets
    datasets_count = await db.scalar(
        select(func.count(Dataset.id)).where(Dataset.status != "DELETED")
    )
    
    # Placeholder for training jobs (TrainingJob model doesn't exist yet)
    total_jobs = 0
    
    # Placeholder for active training jobs
    active_jobs = 0
    
    # Count production models
    production_models = await db.scalar(
        select(func.count(MLModel.id)).where(
            MLModel.status == "PRODUCTION"
        )
    )
    
    # Placeholder for active alerts (will be implemented later)
    active_alerts = 0
    
    return {
        "data": {
            "total_datasets": datasets_count or 0,
            "total_training_jobs": total_jobs or 0,
            "active_training_jobs": active_jobs or 0,
            "production_models": production_models or 0,
            "active_alerts": active_alerts,
        }
    }

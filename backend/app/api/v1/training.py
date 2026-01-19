"""
Training API Endpoints
Model training job management.
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.training_service import TrainingService

router = APIRouter(prefix="/training", tags=["Training"])


class TrainingJobRequest(BaseModel):
    """Request body for creating a training job."""
    name: str
    feature_set_id: str
    algorithm: str = "xgboost"
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    imbalanced_strategy: str = "class_weight"  # class_weight, smote, undersample
    test_size: float = 0.2


@router.get("/jobs")
async def list_training_jobs(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List all training jobs."""
    service = TrainingService(db)
    jobs, total = await service.list_training_jobs(
        status=status,
        page=page,
        page_size=min(page_size, 100),
    )
    
    return {
        "data": jobs,
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    }


@router.post("/jobs", status_code=status.HTTP_201_CREATED)
async def create_training_job(
    request: TrainingJobRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new training job.
    
    The job will be queued for async execution by Celery workers.
    """
    service = TrainingService(db)
    
    # Get default hyperparameters if not provided
    if not request.hyperparameters:
        request.hyperparameters = await service.get_default_hyperparameters(request.algorithm)
    
    job = await service.create_training_job(
        name=request.name,
        feature_set_id=request.feature_set_id,
        algorithm=request.algorithm,
        hyperparameters={
            **request.hyperparameters,
            "imbalanced_strategy": request.imbalanced_strategy,
            "test_size": request.test_size,
        },
    )
    
    return {
        "data": job,
        "message": "Training job created and queued",
    }


@router.get("/jobs/{job_id}")
async def get_training_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get training job status and details."""
    service = TrainingService(db)
    job = await service.get_training_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")
    
    return {"data": job}


@router.get("/algorithms")
async def list_algorithms(db: AsyncSession = Depends(get_db)):
    """
    List available ML algorithms with their hyperparameters.
    
    Each algorithm includes:
    - id: Algorithm identifier
    - name: Display name
    - description: Brief description
    - hyperparameters: Configurable parameters with defaults
    """
    service = TrainingService(db)
    algorithms = await service.list_algorithms()
    return {"data": algorithms}


@router.get("/algorithms/{algorithm_id}/defaults")
async def get_algorithm_defaults(
    algorithm_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get default hyperparameters for an algorithm."""
    service = TrainingService(db)
    defaults = await service.get_default_hyperparameters(algorithm_id)
    
    if not defaults:
        raise HTTPException(status_code=404, detail="Algorithm not found")
    
    return {"data": defaults}

"""
Retraining API Endpoints
Manage automated model retraining.
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.services.retraining_service import (
    get_retraining_pipeline,
    RetrainReason,
    RetrainStatus,
    RetrainConfig,
)

router = APIRouter(prefix="/retraining", tags=["Retraining"])


class TriggerRetrainRequest(BaseModel):
    """Request to trigger retraining."""
    model_id: str
    reason: str = "MANUAL"
    algorithm: str = "xgboost"
    use_latest_data: bool = True
    data_window_days: int = 90
    hyperparameter_tuning: bool = True
    fairness_constraint: bool = True
    auto_promote: bool = False


class RetrainJobResponse(BaseModel):
    """Retraining job response."""
    id: str
    model_id: str
    reason: str
    status: str
    current_step: str
    progress: float
    started_at: str
    completed_at: Optional[str] = None
    new_model_id: Optional[str] = None


@router.post("/trigger")
async def trigger_retraining(
    request: TriggerRetrainRequest,
    db: AsyncSession = Depends(get_db),
):
    """Trigger model retraining."""
    pipeline = get_retraining_pipeline()
    
    try:
        reason = RetrainReason(request.reason)
    except ValueError:
        reason = RetrainReason.MANUAL
    
    config = RetrainConfig(
        algorithm=request.algorithm,
        use_latest_data=request.use_latest_data,
        data_window_days=request.data_window_days,
        hyperparameter_tuning=request.hyperparameter_tuning,
        fairness_constraint=request.fairness_constraint,
        auto_promote=request.auto_promote,
    )
    
    job = pipeline.trigger_retraining(
        model_id=request.model_id,
        reason=reason,
        config=config,
    )
    
    return {
        "data": {
            "id": job.id,
            "model_id": job.model_id,
            "reason": job.reason.value,
            "status": job.status.value,
            "current_step": job.current_step,
            "progress": job.progress,
            "started_at": job.started_at.isoformat(),
        },
        "message": "Retraining triggered"
    }


@router.post("/{job_id}/run")
async def run_retraining(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Execute retraining pipeline."""
    pipeline = get_retraining_pipeline()
    
    job = pipeline.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = await pipeline.run_pipeline(job_id)
    
    return {
        "data": {
            "id": job.id,
            "status": job.status.value,
            "current_step": job.current_step,
            "progress": job.progress,
            "metrics": job.metrics,
            "comparison_result": job.comparison_result,
            "new_model_id": job.new_model_id,
            "error": job.error,
        }
    }


@router.get("/{job_id}")
async def get_retraining_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get retraining job details."""
    pipeline = get_retraining_pipeline()
    
    job = pipeline.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "data": {
            "id": job.id,
            "model_id": job.model_id,
            "reason": job.reason.value,
            "status": job.status.value,
            "current_step": job.current_step,
            "progress": job.progress,
            "started_at": job.started_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "metrics": job.metrics,
            "comparison_result": job.comparison_result,
            "new_model_id": job.new_model_id,
            "error": job.error,
        }
    }


@router.get("")
async def list_retraining_jobs(
    model_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List retraining jobs."""
    pipeline = get_retraining_pipeline()
    
    st = RetrainStatus(status) if status else None
    jobs = pipeline.list_jobs(model_id=model_id, status=st, limit=limit)
    
    return {
        "data": [
            {
                "id": j.id,
                "model_id": j.model_id,
                "reason": j.reason.value,
                "status": j.status.value,
                "current_step": j.current_step,
                "progress": j.progress,
                "started_at": j.started_at.isoformat(),
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
            }
            for j in jobs
        ],
        "meta": {
            "total": len(jobs),
        }
    }


@router.post("/{job_id}/promote")
async def promote_model(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Promote retrained model to production."""
    pipeline = get_retraining_pipeline()
    
    job = pipeline.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != RetrainStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")
    
    if not job.new_model_id:
        raise HTTPException(status_code=400, detail="No new model available")
    
    # In production, update model registry to promote new model
    
    return {
        "message": "Model promoted to production",
        "new_model_id": job.new_model_id,
    }


@router.get("/reasons/available")
async def get_retrain_reasons():
    """Get available retraining reasons."""
    return {
        "data": [
            {"reason": r.value, "description": {
                RetrainReason.SCHEDULED: "Regular scheduled retraining",
                RetrainReason.DRIFT_DETECTED: "Data drift detected in features",
                RetrainReason.PERFORMANCE_DEGRADATION: "Model performance dropped",
                RetrainReason.BIAS_DETECTED: "Fairness issues detected",
                RetrainReason.MANUAL: "Manually triggered",
                RetrainReason.NEW_DATA: "Significant new data available",
            }.get(r, "")}
            for r in RetrainReason
        ]
    }

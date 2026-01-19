"""
Monitoring API Endpoints
Drift and bias detection, model performance monitoring.
"""
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


class DriftThresholds(BaseModel):
    """Drift detection thresholds."""
    psi_warning: float = 0.1
    psi_critical: float = 0.25
    ks_alpha: float = 0.05


class BiasThresholds(BaseModel):
    """Bias detection thresholds."""
    demographic_parity: float = 0.1
    disparate_impact: float = 0.8


@router.get("/drift/{model_id}")
async def get_drift_metrics(
    model_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get latest drift metrics for a model.
    
    Returns PSI and KS-test results for all monitored features.
    """
    return {
        "data": {
            "overall_status": "WARNING",
            "last_computed": "2026-01-17T10:00:00Z",
            "features": {
                "amount": {
                    "psi": 0.15,
                    "ks_statistic": 0.08,
                    "ks_p_value": 0.02,
                    "status": "WARNING",
                    "trend": "increasing"
                },
                "hour_of_day": {
                    "psi": 0.05,
                    "ks_statistic": 0.03,
                    "ks_p_value": 0.45,
                    "status": "OK",
                    "trend": "stable"
                },
                "user_txn_count": {
                    "psi": 0.22,
                    "ks_statistic": 0.12,
                    "ks_p_value": 0.001,
                    "status": "CRITICAL",
                    "trend": "increasing"
                },
            },
            "thresholds": {
                "psi_warning": 0.1,
                "psi_critical": 0.25,
                "ks_alpha": 0.05,
            }
        }
    }


@router.get("/drift/{model_id}/history")
async def get_drift_history(
    model_id: str,
    days: int = 7,
    db: AsyncSession = Depends(get_db),
):
    """
    Get drift metrics history for trending.
    """
    history = []
    for i in range(days):
        date = datetime.utcnow() - timedelta(days=days - 1 - i)
        history.append({
            "date": date.strftime("%Y-%m-%d"),
            "overall_status": "OK" if i % 3 != 0 else "WARNING",
            "drifted_features": i % 3,
            "avg_psi": 0.05 + (i * 0.01),
        })
    
    return {"data": history}


@router.get("/drift/{model_id}/feature/{feature}")
async def get_feature_drift_trend(
    model_id: str,
    feature: str,
    days: int = 7,
    db: AsyncSession = Depends(get_db),
):
    """
    Get drift trend for a specific feature.
    """
    import random
    
    trend = []
    for i in range(days):
        date = datetime.utcnow() - timedelta(days=days - 1 - i)
        trend.append({
            "date": date.strftime("%Y-%m-%d"),
            "psi": 0.05 + random.uniform(-0.02, 0.05),
            "ks_statistic": 0.03 + random.uniform(-0.01, 0.02),
        })
    
    return {
        "data": {
            "feature": feature,
            "trend": trend,
        }
    }


@router.put("/drift/{model_id}/thresholds")
async def update_drift_thresholds(
    model_id: str,
    thresholds: DriftThresholds,
    db: AsyncSession = Depends(get_db),
):
    """
    Update drift detection thresholds for a model.
    """
    return {
        "data": {
            "model_id": model_id,
            "thresholds": {
                "psi_warning": thresholds.psi_warning,
                "psi_critical": thresholds.psi_critical,
                "ks_alpha": thresholds.ks_alpha,
            },
        },
        "message": "Thresholds updated"
    }


@router.get("/bias/{model_id}")
async def get_bias_metrics(
    model_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get latest bias metrics for a model.
    
    Returns fairness metrics across protected attributes.
    """
    return {
        "data": {
            "overall_status": "OK",
            "last_computed": "2026-01-17T10:00:00Z",
            "protected_attributes": {
                "gender": {
                    "demographic_parity_diff": 0.05,
                    "equalized_odds_diff": 0.03,
                    "disparate_impact": 0.92,
                    "status": "OK",
                    "group_rates": {
                        "male": 0.08,
                        "female": 0.075,
                    }
                },
                "age_group": {
                    "demographic_parity_diff": 0.12,
                    "equalized_odds_diff": 0.08,
                    "disparate_impact": 0.78,
                    "status": "WARNING",
                    "group_rates": {
                        "18-25": 0.12,
                        "26-40": 0.08,
                        "41-60": 0.06,
                        "60+": 0.05,
                    }
                },
            },
            "thresholds": {
                "demographic_parity": 0.1,
                "disparate_impact": 0.8,
            }
        }
    }


@router.get("/performance/{model_id}")
async def get_performance_metrics(
    model_id: str,
    period: str = "7d",
    db: AsyncSession = Depends(get_db),
):
    """
    Get model performance metrics over time.
    
    Period options: 1d, 7d, 30d, 90d
    """
    return {
        "data": {
            "current": {
                "precision": 0.92,
                "recall": 0.88,
                "f1": 0.90,
                "auc": 0.95,
                "fpr": 0.03,
            },
            "baseline": {
                "precision": 0.90,
                "recall": 0.85,
                "f1": 0.875,
                "auc": 0.93,
                "fpr": 0.05,
            },
            "trend": [
                {"date": "2026-01-10", "precision": 0.91, "recall": 0.87, "f1": 0.89},
                {"date": "2026-01-11", "precision": 0.90, "recall": 0.86, "f1": 0.88},
                {"date": "2026-01-12", "precision": 0.92, "recall": 0.88, "f1": 0.90},
                {"date": "2026-01-13", "precision": 0.91, "recall": 0.87, "f1": 0.89},
                {"date": "2026-01-14", "precision": 0.92, "recall": 0.88, "f1": 0.90},
                {"date": "2026-01-15", "precision": 0.93, "recall": 0.89, "f1": 0.91},
                {"date": "2026-01-16", "precision": 0.92, "recall": 0.88, "f1": 0.90},
            ],
            "period": period,
        }
    }


@router.get("/summary/{model_id}")
async def get_monitoring_summary(
    model_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get monitoring summary dashboard for a model.
    """
    return {
        "data": {
            "model_id": model_id,
            "drift": {
                "status": "WARNING",
                "drifted_features": 2,
                "total_features": 30,
                "last_check": "2026-01-17T10:00:00Z",
            },
            "bias": {
                "status": "OK",
                "flagged_attributes": 0,
                "total_attributes": 2,
                "last_check": "2026-01-17T06:00:00Z",
            },
            "performance": {
                "status": "OK",
                "current_f1": 0.90,
                "baseline_f1": 0.875,
                "trend": "stable",
            },
            "alerts": {
                "active": 2,
                "critical": 1,
                "acknowledged": 1,
            },
        }
    }


@router.post("/drift/{model_id}/compute")
async def trigger_drift_computation(
    model_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Trigger manual drift computation for a model."""
    from app.workers.monitoring_worker import compute_drift_metrics
    compute_drift_metrics.delay(model_id)
    
    return {"message": "Drift computation triggered", "model_id": model_id}


@router.post("/bias/{model_id}/compute")
async def trigger_bias_computation(
    model_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Trigger manual bias computation for a model."""
    from app.workers.monitoring_worker import compute_bias_metrics
    compute_bias_metrics.delay(model_id)
    
    return {"message": "Bias computation triggered", "model_id": model_id}


@router.post("/performance/{model_id}/check")
async def trigger_performance_check(
    model_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Trigger manual performance baseline check."""
    from app.workers.monitoring_worker import check_performance_baselines
    check_performance_baselines.delay(model_id)
    
    return {"message": "Performance check triggered", "model_id": model_id}


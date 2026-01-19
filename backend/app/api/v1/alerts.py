"""
Alerts API Endpoints
Alert management and notification configuration.
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db

router = APIRouter(prefix="/alerts", tags=["Alerts"])


class AlertAcknowledgeRequest(BaseModel):
    """Request to acknowledge an alert."""
    resolution_note: Optional[str] = None


@router.get("")
async def list_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """
    List all alerts with optional filtering.
    
    Status: ACTIVE, ACKNOWLEDGED, RESOLVED
    Severity: INFO, WARNING, CRITICAL
    """
    # Mock alerts data
    alerts = [
        {
            "id": "alert-001",
            "model_id": "model-001",
            "alert_type": "DRIFT",
            "severity": "WARNING",
            "title": "Data Drift Detected",
            "message": "PSI threshold exceeded for feature 'amount' (PSI: 0.15 > 0.1)",
            "status": "ACTIVE",
            "created_at": "2026-01-17T08:30:00Z",
        },
        {
            "id": "alert-002",
            "model_id": "model-001",
            "alert_type": "PERFORMANCE",
            "severity": "CRITICAL",
            "title": "Precision Below Baseline",
            "message": "Model precision dropped to 0.88, below baseline of 0.90",
            "status": "ACTIVE",
            "created_at": "2026-01-17T09:15:00Z",
        },
        {
            "id": "alert-003",
            "model_id": "model-001",
            "alert_type": "BIAS",
            "severity": "WARNING",
            "title": "Fairness Threshold Exceeded",
            "message": "Disparate impact for age_group is 0.78, below threshold of 0.80",
            "status": "ACKNOWLEDGED",
            "acknowledged_at": "2026-01-17T10:00:00Z",
            "acknowledged_by": "user-001",
            "created_at": "2026-01-17T07:00:00Z",
        },
        {
            "id": "alert-004",
            "model_id": "model-001",
            "alert_type": "DRIFT",
            "severity": "INFO",
            "title": "Feature Distribution Change",
            "message": "Minor distribution shift detected in feature 'hour_of_day'",
            "status": "RESOLVED",
            "resolved_at": "2026-01-16T15:00:00Z",
            "created_at": "2026-01-16T12:00:00Z",
        },
    ]
    
    # Filter by status
    if status:
        alerts = [a for a in alerts if a["status"] == status]
    
    # Filter by severity
    if severity:
        alerts = [a for a in alerts if a["severity"] == severity]
    
    return {
        "data": alerts,
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": len(alerts),
        },
        "summary": {
            "active": sum(1 for a in alerts if a["status"] == "ACTIVE"),
            "acknowledged": sum(1 for a in alerts if a["status"] == "ACKNOWLEDGED"),
            "resolved": sum(1 for a in alerts if a["status"] == "RESOLVED"),
            "critical": sum(1 for a in alerts if a["severity"] == "CRITICAL"),
        }
    }


@router.get("/{alert_id}")
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get alert details."""
    # Mock alert
    return {
        "data": {
            "id": alert_id,
            "model_id": "model-001",
            "alert_type": "DRIFT",
            "severity": "WARNING",
            "title": "Data Drift Detected",
            "message": "PSI threshold exceeded for feature 'amount'",
            "details": {
                "feature": "amount",
                "psi": 0.15,
                "threshold": 0.1,
                "reference_mean": 150.25,
                "current_mean": 182.50,
            },
            "status": "ACTIVE",
            "created_at": "2026-01-17T08:30:00Z",
        }
    }


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    request: AlertAcknowledgeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Acknowledge an alert."""
    return {
        "data": {
            "id": alert_id,
            "status": "ACKNOWLEDGED",
            "acknowledged_at": datetime.utcnow().isoformat(),
            "resolution_note": request.resolution_note,
        },
        "message": "Alert acknowledged"
    }


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    request: AlertAcknowledgeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Resolve an alert."""
    return {
        "data": {
            "id": alert_id,
            "status": "RESOLVED",
            "resolved_at": datetime.utcnow().isoformat(),
            "resolution_note": request.resolution_note,
        },
        "message": "Alert resolved"
    }


@router.get("/stats/summary")
async def get_alert_stats(
    period: str = "7d",
    db: AsyncSession = Depends(get_db),
):
    """Get alert statistics summary."""
    return {
        "data": {
            "period": period,
            "total": 25,
            "by_type": {
                "DRIFT": 12,
                "PERFORMANCE": 8,
                "BIAS": 5,
            },
            "by_severity": {
                "CRITICAL": 3,
                "WARNING": 15,
                "INFO": 7,
            },
            "by_status": {
                "ACTIVE": 5,
                "ACKNOWLEDGED": 3,
                "RESOLVED": 17,
            },
            "trend": [
                {"date": "2026-01-11", "count": 2},
                {"date": "2026-01-12", "count": 4},
                {"date": "2026-01-13", "count": 3},
                {"date": "2026-01-14", "count": 5},
                {"date": "2026-01-15", "count": 2},
                {"date": "2026-01-16", "count": 6},
                {"date": "2026-01-17", "count": 3},
            ]
        }
    }

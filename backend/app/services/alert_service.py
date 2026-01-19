"""
Alert Service
Alert management and notification.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from enum import Enum
import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    DRIFT = "DRIFT"
    PERFORMANCE = "PERFORMANCE"
    BIAS = "BIAS"
    SYSTEM = "SYSTEM"


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


@dataclass
class AlertCreate:
    """Data for creating an alert."""
    model_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    details: Optional[Dict] = None


@dataclass
class Alert:
    """Alert representation."""
    id: str
    model_id: str
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    title: str
    message: str
    details: Optional[Dict]
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_note: Optional[str] = None


class AlertService:
    """
    Service for alert management.
    
    Features:
    - Create alerts from monitoring
    - Acknowledge and resolve alerts
    - Send notifications
    - Alert aggregation and deduplication
    """
    
    # Alert deduplication window
    DEDUP_WINDOW_HOURS = 1
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # In-memory storage for now (would be database in production)
        self._alerts: Dict[str, Alert] = {}
    
    async def create_alert(self, data: AlertCreate) -> Alert:
        """
        Create a new alert.
        
        Applies deduplication - if similar alert exists within window,
        updates existing instead of creating new.
        """
        # Check for duplicate
        existing = await self._find_duplicate(data)
        if existing:
            logger.info(f"Deduplicating alert: {data.title}")
            return existing
        
        # Create new alert
        alert = Alert(
            id=str(uuid4()),
            model_id=data.model_id,
            alert_type=data.alert_type,
            severity=data.severity,
            status=AlertStatus.ACTIVE,
            title=data.title,
            message=data.message,
            details=data.details,
            created_at=datetime.utcnow(),
        )
        
        self._alerts[alert.id] = alert
        
        # Send notification
        await self._send_notification(alert)
        
        logger.info(f"Created alert: {alert.id} - {alert.title}")
        return alert
    
    async def _find_duplicate(self, data: AlertCreate) -> Optional[Alert]:
        """Find duplicate alert within dedup window."""
        cutoff = datetime.utcnow() - timedelta(hours=self.DEDUP_WINDOW_HOURS)
        
        for alert in self._alerts.values():
            if (alert.model_id == data.model_id and
                alert.alert_type == data.alert_type and
                alert.title == data.title and
                alert.status == AlertStatus.ACTIVE and
                alert.created_at > cutoff):
                return alert
        
        return None
    
    async def _send_notification(self, alert: Alert):
        """
        Send alert notification.
        
        In production, this would:
        - Send email to configured recipients
        - Post to Slack/Teams
        - Trigger PagerDuty for critical alerts
        """
        if alert.severity == AlertSeverity.CRITICAL:
            logger.warning(f"[CRITICAL ALERT] {alert.title}: {alert.message}")
        else:
            logger.info(f"[{alert.severity.value}] {alert.title}")
    
    async def list_alerts(
        self,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        model_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Alert]:
        """List alerts with filtering."""
        alerts = list(self._alerts.values())
        
        if status:
            alerts = [a for a in alerts if a.status == status]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if model_id:
            alerts = [a for a in alerts if a.model_id == model_id]
        
        # Sort by created_at descending
        alerts.sort(key=lambda a: a.created_at, reverse=True)
        
        return alerts[:limit]
    
    async def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID."""
        return self._alerts.get(alert_id)
    
    async def acknowledge_alert(
        self,
        alert_id: str,
        user_id: str,
        note: Optional[str] = None,
    ) -> Optional[Alert]:
        """Acknowledge an alert."""
        alert = self._alerts.get(alert_id)
        if not alert:
            return None
        
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = user_id
        
        logger.info(f"Alert {alert_id} acknowledged by {user_id}")
        return alert
    
    async def resolve_alert(
        self,
        alert_id: str,
        note: Optional[str] = None,
    ) -> Optional[Alert]:
        """Resolve an alert."""
        alert = self._alerts.get(alert_id)
        if not alert:
            return None
        
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        alert.resolution_note = note
        
        logger.info(f"Alert {alert_id} resolved: {note}")
        return alert
    
    async def get_alert_summary(
        self,
        model_id: Optional[str] = None,
    ) -> Dict:
        """Get alert statistics summary."""
        alerts = list(self._alerts.values())
        
        if model_id:
            alerts = [a for a in alerts if a.model_id == model_id]
        
        return {
            "total": len(alerts),
            "active": sum(1 for a in alerts if a.status == AlertStatus.ACTIVE),
            "acknowledged": sum(1 for a in alerts if a.status == AlertStatus.ACKNOWLEDGED),
            "resolved": sum(1 for a in alerts if a.status == AlertStatus.RESOLVED),
            "by_severity": {
                "critical": sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL),
                "warning": sum(1 for a in alerts if a.severity == AlertSeverity.WARNING),
                "info": sum(1 for a in alerts if a.severity == AlertSeverity.INFO),
            },
            "by_type": {
                "drift": sum(1 for a in alerts if a.alert_type == AlertType.DRIFT),
                "performance": sum(1 for a in alerts if a.alert_type == AlertType.PERFORMANCE),
                "bias": sum(1 for a in alerts if a.alert_type == AlertType.BIAS),
            },
        }
    
    async def create_drift_alert(
        self,
        model_id: str,
        feature: str,
        psi: float,
        threshold: float,
    ) -> Alert:
        """Create a drift-specific alert."""
        severity = AlertSeverity.CRITICAL if psi > 0.25 else AlertSeverity.WARNING
        
        return await self.create_alert(AlertCreate(
            model_id=model_id,
            alert_type=AlertType.DRIFT,
            severity=severity,
            title=f"Data Drift Detected: {feature}",
            message=f"PSI={psi:.3f} exceeds threshold {threshold}",
            details={
                "feature": feature,
                "psi": psi,
                "threshold": threshold,
            },
        ))
    
    async def create_performance_alert(
        self,
        model_id: str,
        metric: str,
        current_value: float,
        baseline_value: float,
    ) -> Alert:
        """Create a performance degradation alert."""
        drop = baseline_value - current_value
        drop_pct = (drop / baseline_value) * 100 if baseline_value > 0 else 0
        
        severity = AlertSeverity.CRITICAL if drop_pct > 10 else AlertSeverity.WARNING
        
        return await self.create_alert(AlertCreate(
            model_id=model_id,
            alert_type=AlertType.PERFORMANCE,
            severity=severity,
            title=f"Performance Degradation: {metric}",
            message=f"{metric} dropped from {baseline_value:.3f} to {current_value:.3f} ({drop_pct:.1f}%)",
            details={
                "metric": metric,
                "current": current_value,
                "baseline": baseline_value,
                "drop_percent": drop_pct,
            },
        ))

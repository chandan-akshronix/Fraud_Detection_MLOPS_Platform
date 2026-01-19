"""
Drift Monitoring Service
Production drift detection and alerting.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime, timedelta
import logging

from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ml_model import MLModel

logger = logging.getLogger(__name__)


@dataclass
class DriftAlert:
    """Alert for drift detection."""
    feature: str
    metric: str  # psi, ks_statistic
    current_value: float
    threshold: float
    severity: str  # WARNING, CRITICAL
    message: str


@dataclass
class DriftMonitoringResult:
    """Result of drift monitoring run."""
    model_id: str
    computed_at: datetime
    overall_status: str
    feature_count: int
    drifted_features: int
    alerts: List[DriftAlert]
    metrics: Dict[str, Any]


class DriftMonitoringService:
    """
    Service for production drift monitoring.
    
    Monitors:
    - Data drift (PSI, KS-test)
    - Concept drift (performance degradation)
    - Feature distribution changes
    """
    
    # Default thresholds
    PSI_WARNING = 0.1
    PSI_CRITICAL = 0.25
    KS_ALPHA = 0.05
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def run_drift_check(
        self,
        model_id: str,
        reference_data: Optional[Any] = None,
        current_data: Optional[Any] = None,
    ) -> DriftMonitoringResult:
        """
        Run drift detection for a model.
        
        Args:
            model_id: Model to check
            reference_data: Training/reference data
            current_data: Production/current data
        
        Returns:
            DriftMonitoringResult with metrics and alerts
        """
        logger.info(f"Running drift check for model {model_id}")
        
        # Get model info
        model = await self._get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
        
        # For now, generate mock drift metrics
        # In production, this would use the DataDriftDetector
        drift_metrics = await self._compute_drift_metrics(model)
        
        # Generate alerts based on thresholds
        alerts = self._generate_alerts(drift_metrics)
        
        # Determine overall status
        if any(a.severity == "CRITICAL" for a in alerts):
            overall_status = "CRITICAL"
        elif any(a.severity == "WARNING" for a in alerts):
            overall_status = "WARNING"
        else:
            overall_status = "OK"
        
        # Store metrics in database
        await self._store_drift_metrics(model_id, drift_metrics, overall_status)
        
        # Create alerts in database
        if alerts:
            await self._create_alerts(model_id, alerts)
        
        result = DriftMonitoringResult(
            model_id=model_id,
            computed_at=datetime.utcnow(),
            overall_status=overall_status,
            feature_count=len(drift_metrics),
            drifted_features=len([m for m in drift_metrics.values() if m.get("status") != "OK"]),
            alerts=alerts,
            metrics=drift_metrics,
        )
        
        logger.info(f"Drift check complete: {overall_status}, {len(alerts)} alerts")
        return result
    
    async def _get_model(self, model_id: str) -> Optional[MLModel]:
        """Get model by ID."""
        try:
            uuid_id = UUID(model_id)
        except ValueError:
            return None
        
        result = await self.db.execute(
            select(MLModel).where(MLModel.id == uuid_id)
        )
        return result.scalar_one_or_none()
    
    async def _compute_drift_metrics(self, model: MLModel) -> Dict[str, Any]:
        """
        Compute drift metrics for model features.
        
        In production, this would:
        1. Load reference data from feature store
        2. Fetch recent production data
        3. Compute PSI and KS statistics
        """
        # Mock feature drift metrics
        features = model.feature_names or [
            "amount", "hour_of_day", "day_of_week", 
            "user_txn_count", "time_since_last", "is_night",
            "merchant_risk_score", "velocity_1h", "velocity_24h",
        ]
        
        import random
        
        metrics = {}
        for feature in features:
            # Simulate drift values
            psi = random.uniform(0.0, 0.35)
            ks_stat = random.uniform(0.0, 0.2)
            ks_p = random.uniform(0.0, 1.0)
            
            if psi > self.PSI_CRITICAL:
                status = "CRITICAL"
            elif psi > self.PSI_WARNING:
                status = "WARNING"
            else:
                status = "OK"
            
            metrics[feature] = {
                "psi": psi,
                "ks_statistic": ks_stat,
                "ks_p_value": ks_p,
                "status": status,
                "trend": random.choice(["stable", "increasing", "decreasing"]),
            }
        
        return metrics
    
    def _generate_alerts(self, metrics: Dict[str, Any]) -> List[DriftAlert]:
        """Generate alerts from drift metrics."""
        alerts = []
        
        for feature, m in metrics.items():
            psi = m.get("psi", 0)
            ks_stat = m.get("ks_statistic", 0)
            ks_p = m.get("ks_p_value", 1.0)
            
            # PSI-based alerts
            if psi > self.PSI_CRITICAL:
                alerts.append(DriftAlert(
                    feature=feature,
                    metric="psi",
                    current_value=psi,
                    threshold=self.PSI_CRITICAL,
                    severity="CRITICAL",
                    message=f"Critical drift in '{feature}': PSI={psi:.3f} exceeds {self.PSI_CRITICAL}",
                ))
            elif psi > self.PSI_WARNING:
                alerts.append(DriftAlert(
                    feature=feature,
                    metric="psi",
                    current_value=psi,
                    threshold=self.PSI_WARNING,
                    severity="WARNING",
                    message=f"Drift detected in '{feature}': PSI={psi:.3f} exceeds {self.PSI_WARNING}",
                ))
            
            # KS-test alerts
            if ks_p < self.KS_ALPHA and ks_stat > 0.1:
                alerts.append(DriftAlert(
                    feature=feature,
                    metric="ks_statistic",
                    current_value=ks_stat,
                    threshold=self.KS_ALPHA,
                    severity="WARNING",
                    message=f"Distribution shift in '{feature}': KS={ks_stat:.3f}, p={ks_p:.4f}",
                ))
        
        return alerts
    
    async def _store_drift_metrics(
        self,
        model_id: str,
        metrics: Dict[str, Any],
        status: str,
    ):
        """Store drift metrics in database."""
        # In production, this would insert into drift_metrics table
        logger.info(f"Stored drift metrics for model {model_id}: {status}")
    
    async def _create_alerts(
        self,
        model_id: str,
        alerts: List[DriftAlert],
    ):
        """Create alerts in database."""
        # In production, this would insert into alerts table
        for alert in alerts:
            logger.info(f"Created alert: {alert.message}")
    
    async def get_drift_history(
        self,
        model_id: str,
        days: int = 7,
    ) -> List[Dict]:
        """Get drift metrics history for a model."""
        # Mock history data
        history = []
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=i)
            history.append({
                "date": date.isoformat(),
                "overall_status": "OK" if i % 3 != 0 else "WARNING",
                "drifted_features": i % 3,
                "avg_psi": 0.05 + (i * 0.02),
            })
        
        return list(reversed(history))
    
    async def get_feature_drift_trend(
        self,
        model_id: str,
        feature: str,
        days: int = 7,
    ) -> List[Dict]:
        """Get drift trend for a specific feature."""
        import random
        
        trend = []
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=i)
            trend.append({
                "date": date.isoformat(),
                "psi": 0.05 + random.uniform(-0.02, 0.05),
                "ks_statistic": 0.03 + random.uniform(-0.01, 0.02),
            })
        
        return list(reversed(trend))

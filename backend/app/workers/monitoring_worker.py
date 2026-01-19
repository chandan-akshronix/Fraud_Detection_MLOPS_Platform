"""
Monitoring Worker
Background tasks for drift, bias, and performance monitoring.
"""
from celery import shared_task
from celery.schedules import crontab
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@shared_task(name="app.workers.monitoring_worker.compute_drift_metrics")
def compute_drift_metrics(model_id: str = None):
    """
    Compute drift metrics for production models.
    
    If model_id is provided, compute for that model only.
    Otherwise, compute for all production models.
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    async def _compute():
        try:
            logger.info(f"Computing drift metrics for model {model_id or 'ALL'}")
            
            # Import ML components
            from ml.drift import DataDriftDetector, DriftConfig
            
            # Create drift detector
            config = DriftConfig(
                psi_threshold=0.1,
                ks_alpha=0.05,
            )
            detector = DataDriftDetector(config)
            
            # In production:
            # 1. Fetch reference data (training statistics)
            # 2. Fetch current production data
            # 3. Compute PSI and KS for each feature
            
            # Mock implementation
            import numpy as np
            n_features = 30
            n_samples = 1000
            
            reference_data = np.random.randn(n_samples, n_features)
            current_data = np.random.randn(n_samples, n_features) + 0.1  # Slight shift
            
            result = detector.detect_drift(reference_data, current_data)
            
            logger.info(f"Drift detection complete: "
                       f"overall={result.overall_status}, "
                       f"drifted_features={result.drifted_feature_count}")
            
            # Store results and create alerts if needed
            if result.has_drift:
                logger.warning(f"DRIFT DETECTED: {result.drifted_feature_count} features drifted")
                # Would create alerts here
            
            return {
                "status": "completed",
                "model_id": model_id,
                "has_drift": result.has_drift,
                "drifted_features": result.drifted_feature_count,
            }
            
        except Exception as e:
            logger.error(f"Drift computation failed: {e}")
            raise
    
    return asyncio.run(_compute())


@shared_task(name="app.workers.monitoring_worker.compute_bias_metrics")
def compute_bias_metrics(model_id: str = None):
    """
    Compute bias metrics for production models.
    
    Evaluates fairness across protected attributes.
    """
    import asyncio
    
    async def _compute():
        try:
            logger.info(f"Computing bias metrics for model {model_id or 'ALL'}")
            
            # Import ML components
            from ml.bias import BiasDetector, BiasConfig
            
            config = BiasConfig(
                protected_attributes=["gender", "age_group"],
                demographic_parity_threshold=0.1,
                disparate_impact_threshold=0.8,
            )
            detector = BiasDetector(config)
            
            # In production:
            # 1. Fetch predictions with protected attributes
            # 2. Compute demographic parity
            # 3. Compute disparate impact
            
            # Mock implementation
            import numpy as np
            n_samples = 1000
            
            predictions = np.random.randint(0, 2, n_samples)
            protected = np.random.choice(["A", "B", "C"], n_samples)
            
            result = detector.detect_bias(predictions, protected)
            
            logger.info(f"Bias detection complete: "
                       f"has_bias={result.has_bias}, "
                       f"demographic_parity={result.demographic_parity_diff:.3f}")
            
            if result.has_bias:
                logger.warning(f"BIAS DETECTED: Demographic parity diff = "
                             f"{result.demographic_parity_diff:.3f}")
            
            return {
                "status": "completed",
                "model_id": model_id,
                "has_bias": result.has_bias,
                "demographic_parity": result.demographic_parity_diff,
                "disparate_impact": result.disparate_impact,
            }
            
        except Exception as e:
            logger.error(f"Bias computation failed: {e}")
            raise
    
    return asyncio.run(_compute())


@shared_task(name="app.workers.monitoring_worker.check_performance_baselines")
def check_performance_baselines(model_id: str):
    """
    Check if model performance is meeting baseline thresholds.
    """
    import asyncio
    
    async def _check():
        try:
            logger.info(f"Checking baselines for model {model_id}")
            
            # Mock current metrics
            current_metrics = {
                "precision": 0.87,
                "recall": 0.82,
                "f1": 0.84,
                "auc": 0.91,
            }
            
            # Mock baselines
            baselines = {
                "precision": {"threshold": 0.85, "operator": "gte"},
                "recall": {"threshold": 0.80, "operator": "gte"},
                "f1": {"threshold": 0.82, "operator": "gte"},
                "auc": {"threshold": 0.90, "operator": "gte"},
            }
            
            violations = []
            for metric, baseline in baselines.items():
                current = current_metrics.get(metric, 0)
                threshold = baseline["threshold"]
                operator = baseline["operator"]
                
                passed = (
                    current >= threshold if operator == "gte" else
                    current <= threshold if operator == "lte" else
                    current == threshold
                )
                
                if not passed:
                    violations.append({
                        "metric": metric,
                        "current": current,
                        "threshold": threshold,
                        "operator": operator,
                    })
                    logger.warning(f"BASELINE VIOLATION: {metric}={current:.3f} "
                                 f"vs threshold {operator} {threshold}")
            
            logger.info(f"Baseline check completed: {len(violations)} violations")
            
            return {
                "status": "completed",
                "model_id": model_id,
                "violations": len(violations),
                "details": violations,
            }
            
        except Exception as e:
            logger.error(f"Baseline check failed: {e}")
            raise
    
    return asyncio.run(_check())


@shared_task(name="app.workers.monitoring_worker.scheduled_drift_check")
def scheduled_drift_check():
    """
    Scheduled task to check drift for all production models.
    Runs hourly.
    """
    logger.info("Starting scheduled drift check for all production models")
    
    # Would fetch all production models and run drift check
    # For now, just log
    compute_drift_metrics.delay(model_id=None)
    
    return {"status": "triggered", "timestamp": datetime.utcnow().isoformat()}


@shared_task(name="app.workers.monitoring_worker.scheduled_bias_check")
def scheduled_bias_check():
    """
    Scheduled task to check bias for all production models.
    Runs every 6 hours.
    """
    logger.info("Starting scheduled bias check for all production models")
    
    compute_bias_metrics.delay(model_id=None)
    
    return {"status": "triggered", "timestamp": datetime.utcnow().isoformat()}


@shared_task(name="app.workers.monitoring_worker.scheduled_performance_check")
def scheduled_performance_check():
    """
    Scheduled task to check performance baselines.
    Runs every 30 minutes.
    """
    logger.info("Starting scheduled performance check")
    
    # Would fetch production model and check baselines
    # check_performance_baselines.delay(model_id="production-model-id")
    
    return {"status": "triggered", "timestamp": datetime.utcnow().isoformat()}


# Celery Beat schedule configuration
CELERY_BEAT_SCHEDULE = {
    'drift-check-hourly': {
        'task': 'app.workers.monitoring_worker.scheduled_drift_check',
        'schedule': crontab(minute=0),  # Every hour at :00
    },
    'bias-check-6h': {
        'task': 'app.workers.monitoring_worker.scheduled_bias_check',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
    'performance-check-30m': {
        'task': 'app.workers.monitoring_worker.scheduled_performance_check',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}

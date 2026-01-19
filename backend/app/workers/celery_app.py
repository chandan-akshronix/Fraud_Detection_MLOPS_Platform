"""
Celery Application Configuration
Async task queue for background jobs.
"""
from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "shadow_hubble",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.feature_worker",
        "app.workers.training_worker",
        "app.workers.monitoring_worker",
    ],
)

# Configure Celery
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    
    # Result backend
    result_expires=86400,  # 24 hours
    
    # Task routes
    task_routes={
        "app.workers.feature_worker.*": {"queue": "features"},
        "app.workers.training_worker.*": {"queue": "training"},
        "app.workers.monitoring_worker.*": {"queue": "monitoring"},
    },
    
    # Retry policy
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Beat scheduler (periodic tasks)
    beat_schedule={
        "check-drift-every-hour": {
            "task": "app.workers.monitoring_worker.compute_drift_metrics",
            "schedule": 3600.0,  # Every hour
        },
        "check-bias-every-day": {
            "task": "app.workers.monitoring_worker.compute_bias_metrics",
            "schedule": 86400.0,  # Every day
        },
    },
)

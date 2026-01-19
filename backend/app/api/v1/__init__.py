"""
API v1 Router
Aggregates all API endpoints for version 1.
"""
from fastapi import APIRouter

from app.api.v1.datasets import router as datasets_router
from app.api.v1.features import router as features_router
from app.api.v1.training import router as training_router
from app.api.v1.models import router as models_router
from app.api.v1.inference import router as inference_router
from app.api.v1.monitoring import router as monitoring_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.retraining import router as retraining_router
from app.api.v1.ab_testing import router as ab_testing_router

api_router = APIRouter()

# Include all routers
api_router.include_router(datasets_router)
api_router.include_router(features_router)
api_router.include_router(training_router)
api_router.include_router(models_router)
api_router.include_router(inference_router)
api_router.include_router(monitoring_router)
api_router.include_router(alerts_router)
api_router.include_router(jobs_router)
api_router.include_router(retraining_router)
api_router.include_router(ab_testing_router)



---
status: DRAFT
version: 1.0
last_updated: 2026-01-17T15:25:00+05:30
persona: Backend Developer
upstream: technical-specs.md
---

# Backend Implementation Guide
## E-Commerce Fraud Detection MLOps Platform

## Overview

This document provides implementation guidance for the FastAPI backend, including patterns, services structure, and key implementation details.

---

## Project Setup

### Quick Start

```bash
# Clone and setup
cd shadow-hubble/backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# Install dependencies
pip install poetry
poetry install

# Setup environment
cp .env.example .env
# Edit .env with your Azure credentials

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000

# Start Celery worker (separate terminal)
celery -A app.workers.celery_app worker --loglevel=info
```

### Dependencies (pyproject.toml)

```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
pydantic = "^2.5.0"
pydantic-settings = "^2.1.0"
sqlalchemy = "^2.0.25"
alembic = "^1.13.0"
asyncpg = "^0.29.0"
redis = "^5.0.0"
celery = {extras = ["redis"], version = "^5.3.0"}
azure-storage-blob = "^12.19.0"
azure-identity = "^1.15.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
httpx = "^0.26.0"

# ML dependencies
scikit-learn = "^1.4.0"
xgboost = "^2.0.0"
lightgbm = "^4.0.0"
pandas = "^2.1.0"
numpy = "^1.26.0"
shap = "^0.44.0"
evidently = "^0.4.0"
fairlearn = "^0.10.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.23.0"
pytest-cov = "^4.1.0"
httpx = "^0.26.0"
ruff = "^0.1.0"
black = "^23.12.0"
mypy = "^1.8.0"
pre-commit = "^3.6.0"
```

---

## Core Configuration

### app/core/config.py

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Shadow Hubble"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    
    # Redis
    REDIS_URL: str
    REDIS_FEATURE_TTL: int = 86400  # 24 hours
    
    # Azure Blob
    AZURE_STORAGE_CONNECTION_STRING: str
    AZURE_STORAGE_CONTAINER_DATASETS: str = "datasets"
    AZURE_STORAGE_CONTAINER_MODELS: str = "models"
    
    # Azure AD B2C
    AZURE_AD_B2C_TENANT: str
    AZURE_AD_B2C_CLIENT_ID: str
    AZURE_AD_B2C_POLICY: str
    AZURE_AD_B2C_JWKS_URL: str
    
    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

---

## Service Pattern

### Standard Service Structure

```python
# app/services/base_service.py
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession

class BaseService(ABC):
    """Base service with common functionality."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def commit(self):
        await self.db.commit()
    
    async def refresh(self, obj):
        await self.db.refresh(obj)
```

### Example: Model Service

```python
# app/services/model_service.py
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ml_model import MLModel
from app.schemas.model import ModelCreate, ModelUpdate, ModelPromote

class ModelService:
    def __init__(self, db: AsyncSession, blob_client: BlobClient):
        self.db = db
        self.blob = blob_client
    
    async def list_models(
        self, 
        status: str | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> list[MLModel]:
        query = select(MLModel).order_by(MLModel.created_at.desc())
        if status:
            query = query.where(MLModel.status == status)
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_model(self, model_id: UUID) -> MLModel | None:
        result = await self.db.execute(
            select(MLModel).where(MLModel.id == model_id)
        )
        return result.scalar_one_or_none()
    
    async def get_production_model(self) -> MLModel | None:
        result = await self.db.execute(
            select(MLModel).where(MLModel.status == "PRODUCTION")
        )
        return result.scalar_one_or_none()
    
    async def promote_model(
        self, 
        model_id: UUID, 
        target_status: str
    ) -> MLModel:
        model = await self.get_model(model_id)
        if not model:
            raise ModelNotFoundError(model_id)
        
        # Demote current production model if promoting to production
        if target_status == "PRODUCTION":
            current_prod = await self.get_production_model()
            if current_prod:
                current_prod.status = "ARCHIVED"
                current_prod.promoted_at = None
        
        model.status = target_status
        model.promoted_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(model)
        
        return model
```

---

## Dependency Injection

### app/api/deps.py

```python
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
import httpx

from app.core.config import get_settings
from app.core.database import async_session_maker
from app.services.model_service import ModelService

settings = get_settings()

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"https://{settings.AZURE_AD_B2C_TENANT}.b2clogin.com/.../oauth2/v2.0/authorize",
    tokenUrl=f"https://{settings.AZURE_AD_B2C_TENANT}.b2clogin.com/.../oauth2/v2.0/token",
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validate Azure AD B2C token."""
    try:
        # Fetch JWKS
        async with httpx.AsyncClient() as client:
            jwks_response = await client.get(settings.AZURE_AD_B2C_JWKS_URL)
            jwks = jwks_response.json()
        
        # Decode and validate
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=settings.AZURE_AD_B2C_CLIENT_ID,
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

def get_model_service(db: AsyncSession = Depends(get_db)) -> ModelService:
    return ModelService(db, get_blob_client())
```

---

## API Router Pattern

### app/api/v1/models.py

```python
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user, get_model_service
from app.services.model_service import ModelService
from app.schemas.model import (
    ModelResponse, ModelListResponse, 
    ModelPromoteRequest, BaselineCreateRequest
)

router = APIRouter(prefix="/models", tags=["Models"])

@router.get("", response_model=ModelListResponse)
async def list_models(
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    service: ModelService = Depends(get_model_service),
    user: dict = Depends(get_current_user)
):
    """List all models with optional filtering."""
    offset = (page - 1) * page_size
    models = await service.list_models(
        status=status, 
        limit=page_size, 
        offset=offset
    )
    return ModelListResponse(
        data=models,
        meta={"page": page, "page_size": page_size}
    )

@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: UUID,
    service: ModelService = Depends(get_model_service),
    user: dict = Depends(get_current_user)
):
    """Get model details."""
    model = await service.get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_id} not found"
        )
    return ModelResponse(data=model)

@router.post("/{model_id}/promote")
async def promote_model(
    model_id: UUID,
    request: ModelPromoteRequest,
    service: ModelService = Depends(get_model_service),
    user: dict = Depends(get_current_user)
):
    """Promote model to staging or production."""
    model = await service.promote_model(model_id, request.target_status)
    return ModelResponse(data=model)

@router.post("/{model_id}/baselines")
async def set_baselines(
    model_id: UUID,
    request: BaselineCreateRequest,
    service: ModelService = Depends(get_model_service),
    user: dict = Depends(get_current_user)
):
    """Set baseline metrics for monitoring."""
    baselines = await service.set_baselines(model_id, request.baselines)
    return {"data": baselines}
```

---

## Celery Workers

### app/workers/celery_app.py

```python
from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "shadow_hubble",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
)

# Auto-discover tasks
celery_app.autodiscover_tasks([
    "app.workers.training_worker",
    "app.workers.feature_worker",
    "app.workers.drift_worker",
    "app.workers.bias_worker",
])
```

### app/workers/training_worker.py

```python
from celery import shared_task
from app.workers.celery_app import celery_app

@celery_app.task(bind=True, max_retries=3)
def train_model_task(
    self,
    job_id: str,
    feature_set_id: str,
    algorithm: str,
    hyperparameters: dict
):
    """
    Background task for model training.
    """
    try:
        # Update job status
        update_job_status(job_id, "RUNNING", progress=0)
        
        # Load features
        features = load_feature_set(feature_set_id)
        update_job_status(job_id, "RUNNING", progress=0.1)
        
        # Train model
        trainer = FraudModelTrainer()
        result = trainer.train(
            features,
            algorithm=algorithm,
            hyperparameters=hyperparameters,
            progress_callback=lambda p: update_job_status(job_id, "RUNNING", progress=0.1 + p*0.8)
        )
        
        # Save model
        model_id = save_model_artifact(result)
        update_job_status(job_id, "COMPLETED", progress=1.0, model_id=model_id)
        
        return {"model_id": model_id, "metrics": result.metrics}
        
    except Exception as e:
        update_job_status(job_id, "FAILED", error=str(e))
        raise self.retry(exc=e, countdown=60)
```

---

## Error Handling

### app/shared/exceptions.py

```python
from fastapi import HTTPException, status

class AppException(Exception):
    """Base application exception."""
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code

class NotFoundError(AppException):
    def __init__(self, resource: str, id: str):
        super().__init__(
            message=f"{resource} with id {id} not found",
            code="NOT_FOUND"
        )

class ValidationError(AppException):
    def __init__(self, details: list[dict]):
        super().__init__(
            message="Validation failed",
            code="VALIDATION_ERROR"
        )
        self.details = details

class ModelNotFoundError(NotFoundError):
    def __init__(self, model_id: str):
        super().__init__("Model", str(model_id))

class TrainingJobFailedError(AppException):
    def __init__(self, job_id: str, reason: str):
        super().__init__(
            message=f"Training job {job_id} failed: {reason}",
            code="TRAINING_FAILED"
        )
```

### Exception Handler Middleware

```python
# app/shared/middleware/error_handler.py
from fastapi import Request
from fastapi.responses import JSONResponse
from app.shared.exceptions import AppException

async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": getattr(exc, "details", None)
            },
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request.state.request_id
            }
        }
    )
```

---

## Testing

### tests/conftest.py

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base
from app.api.deps import get_db

# Test database
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/test_db"

@pytest.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(db_session):
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

### tests/integration/test_models.py

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_models(client: AsyncClient):
    response = await client.get("/api/v1/models")
    assert response.status_code == 200
    assert "data" in response.json()

@pytest.mark.asyncio
async def test_get_model_not_found(client: AsyncClient):
    response = await client.get("/api/v1/models/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
```

---

## Key Implementation Tasks

| Task ID | Description | Priority | Hours |
|---------|-------------|----------|-------|
| BE-001 | FastAPI project structure | P0 | 4 |
| BE-002 | PostgreSQL + Alembic setup | P0 | 6 |
| BE-003 | Redis connection | P0 | 3 |
| BE-004 | Azure Blob client | P0 | 4 |
| BE-005 | Azure AD B2C integration | P0 | 8 |
| BE-006 | Dataset CRUD endpoints | P0 | 12 |
| BE-007 | Feature engineering service | P0 | 16 |
| BE-008 | Training service + Celery | P0 | 16 |
| BE-009 | Model service | P0 | 12 |
| BE-010 | Inference service | P0 | 10 |
| BE-011 | Drift detection service | P0 | 12 |
| BE-012 | Bias detection service | P0 | 10 |
| BE-013 | Alert service | P0 | 8 |
| BE-014 | Retraining service | P1 | 12 |

---

*Document prepared by: Backend Developer Persona*

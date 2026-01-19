---
status: DRAFT
version: 1.0
last_updated: 2026-01-17T15:10:00+05:30
review_cycle: 0
persona: Tech Lead
upstream: architecture-decisions.md
next_persona: Backend Developer, Data Scientist, Database Architect
---

# Technical Specifications
## E-Commerce Fraud Detection MLOps Platform

## Project Structure

### Monorepo Layout

```
shadow-hubble/
├── .github/
│   └── workflows/
│       ├── ci.yml                    # Lint, test, build
│       ├── cd-staging.yml            # Deploy to staging
│       └── cd-prod.yml               # Deploy to production
│
├── frontend/                          # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/               # Button, Modal, Table
│   │   │   ├── charts/               # DriftChart, MetricsChart
│   │   │   └── layout/               # Sidebar, Header
│   │   ├── pages/
│   │   │   ├── Dashboard/
│   │   │   ├── DataRegistry/
│   │   │   ├── Training/
│   │   │   ├── ModelRegistry/
│   │   │   ├── Monitoring/
│   │   │   ├── Bias/
│   │   │   ├── Alerts/
│   │   │   └── Settings/
│   │   ├── hooks/
│   │   ├── services/                 # API clients
│   │   ├── store/                    # Zustand stores
│   │   ├── types/
│   │   └── utils/
│   ├── tests/
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── backend/                           # Python + FastAPI
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── datasets.py
│   │   │       ├── features.py
│   │   │       ├── training.py
│   │   │       ├── models.py
│   │   │       ├── inference.py
│   │   │       ├── monitoring.py
│   │   │       ├── bias.py
│   │   │       ├── alerts.py
│   │   │       └── retraining.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── database.py
│   │   │   └── redis.py
│   │   ├── models/                   # SQLAlchemy models
│   │   │   ├── dataset.py
│   │   │   ├── feature_set.py
│   │   │   ├── ml_model.py
│   │   │   ├── baseline.py
│   │   │   ├── prediction.py
│   │   │   ├── drift_metric.py
│   │   │   ├── bias_metric.py
│   │   │   └── alert.py
│   │   ├── schemas/                  # Pydantic schemas
│   │   ├── services/                 # Business logic
│   │   │   ├── data_service.py
│   │   │   ├── feature_service.py
│   │   │   ├── training_service.py
│   │   │   ├── model_service.py
│   │   │   ├── inference_service.py
│   │   │   ├── drift_service.py
│   │   │   ├── bias_service.py
│   │   │   ├── alert_service.py
│   │   │   └── retraining_service.py
│   │   ├── workers/                  # Celery tasks
│   │   │   ├── training_worker.py
│   │   │   ├── feature_worker.py
│   │   │   ├── drift_worker.py
│   │   │   ├── bias_worker.py
│   │   │   └── retraining_worker.py
│   │   └── main.py
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   ├── alembic/
│   ├── pyproject.toml
│   └── Dockerfile
│
├── ml/                                # ML-specific code
│   ├── algorithms/
│   │   ├── isolation_forest.py
│   │   ├── xgboost_fraud.py
│   │   ├── lightgbm_fraud.py
│   │   └── neural_fraud.py
│   ├── features/
│   │   ├── transaction_features.py
│   │   ├── behavioral_features.py
│   │   ├── temporal_features.py
│   │   └── aggregation_features.py
│   ├── drift/
│   │   ├── data_drift.py             # PSI, KS, Chi-Square
│   │   ├── concept_drift.py          # Performance-based
│   │   └── feature_drift.py
│   ├── bias/
│   │   ├── fairness_metrics.py       # Fairlearn integration
│   │   └── protected_attributes.py
│   └── explainability/
│       ├── shap_explainer.py
│       └── lime_explainer.py
│
├── infrastructure/
│   ├── terraform/
│   │   ├── modules/
│   │   │   ├── networking/
│   │   │   ├── compute/
│   │   │   ├── database/
│   │   │   ├── storage/
│   │   │   ├── redis/
│   │   │   ├── servicebus/
│   │   │   └── monitoring/
│   │   ├── environments/
│   │   │   ├── dev.tfvars
│   │   │   ├── staging.tfvars
│   │   │   └── prod.tfvars
│   │   └── main.tf
│   └── docker/
│       ├── docker-compose.yml
│       └── docker-compose.dev.yml
│
├── scripts/
│   ├── setup.sh
│   ├── seed-db.py
│   └── generate-test-data.py
│
├── .env.example
├── README.md
├── Makefile
└── pyproject.toml                     # Workspace config
```

---

## Coding Standards

### Python (Backend)

| Standard | Tool | Configuration |
|----------|------|---------------|
| Formatting | Black | `line-length = 88` |
| Linting | Ruff | `select = ["E", "F", "I", "UP", "B"]` |
| Type Checking | mypy | `strict = true` |
| Import Sorting | isort | `profile = "black"` |
| Pre-commit | pre-commit | All above + bandit |

### TypeScript (Frontend)

| Standard | Tool | Configuration |
|----------|------|---------------|
| Formatting | Prettier | `semi: true, singleQuote: true` |
| Linting | ESLint | TypeScript strict |
| Type Checking | tsc | `strict: true` |

### Commit Convention

```
<type>(<scope>): <description>

Types: feat, fix, docs, style, refactor, test, chore
Scopes: frontend, backend, ml, infra, docs
```

---

## API Contracts

### Base URL
- Dev: `http://localhost:8000/api/v1`
- Staging: `https://staging.shadowhubble.azurewebsites.net/api/v1`
- Prod: `https://api.shadowhubble.com/api/v1`

### Standard Response Format

```python
# Success Response (200, 201)
{
    "data": { ... },
    "meta": {
        "timestamp": "2026-01-17T15:00:00Z",
        "request_id": "uuid"
    }
}

# Paginated Response
{
    "data": [ ... ],
    "meta": {
        "timestamp": "2026-01-17T15:00:00Z",
        "request_id": "uuid",
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total": 150,
            "total_pages": 8
        }
    }
}

# Error Response (4xx, 5xx)
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Human readable message",
        "details": [
            {"field": "name", "message": "Required field"}
        ]
    },
    "meta": {
        "timestamp": "2026-01-17T15:00:00Z",
        "request_id": "uuid"
    }
}
```

---

## API Endpoints

### 1. Dataset APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/datasets` | List all datasets |
| `POST` | `/datasets` | Upload new dataset |
| `GET` | `/datasets/{id}` | Get dataset details |
| `DELETE` | `/datasets/{id}` | Delete dataset |
| `GET` | `/datasets/{id}/schema` | Get dataset schema |
| `GET` | `/datasets/{id}/preview` | Preview first N rows |
| `POST` | `/datasets/{id}/versions` | Create new version |

**Request: Create Dataset**
```python
POST /datasets
Content-Type: multipart/form-data

{
    "name": "fraud_train_v1",
    "description": "Training data January 2026",
    "file": <binary>
}

Response: 201 Created
{
    "data": {
        "id": "uuid",
        "name": "fraud_train_v1",
        "version": "1.0",
        "storage_path": "datasets/uuid/v1.0/data.parquet",
        "row_count": 100000,
        "schema": {
            "columns": [
                {"name": "transaction_id", "type": "string"},
                {"name": "amount", "type": "float"},
                {"name": "is_fraud", "type": "int"}
            ]
        },
        "created_at": "2026-01-17T15:00:00Z"
    }
}
```

### 2. Feature APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/features/sets` | List feature sets |
| `POST` | `/features/compute` | Trigger feature computation |
| `GET` | `/features/sets/{id}` | Get feature set details |
| `GET` | `/features/sets/{id}/preview` | Preview computed features |

**Request: Compute Features**
```python
POST /features/compute
{
    "dataset_id": "uuid",
    "feature_groups": ["transaction", "behavioral", "temporal"],
    "output_name": "fraud_features_v1"
}

Response: 202 Accepted
{
    "data": {
        "job_id": "uuid",
        "status": "PENDING",
        "estimated_time_seconds": 300
    }
}
```

### 3. Training APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/training/jobs` | List training jobs |
| `POST` | `/training/jobs` | Start training job |
| `GET` | `/training/jobs/{id}` | Get job status/progress |
| `POST` | `/training/jobs/{id}/cancel` | Cancel running job |
| `GET` | `/training/algorithms` | List available algorithms |

**Request: Start Training**
```python
POST /training/jobs
{
    "name": "xgboost_fraud_v2",
    "feature_set_id": "uuid",
    "algorithm": "xgboost",
    "hyperparameters": {
        "max_depth": 6,
        "learning_rate": 0.1,
        "n_estimators": 200
    },
    "train_test_split": 0.8,
    "target_column": "is_fraud"
}

Response: 202 Accepted
{
    "data": {
        "job_id": "uuid",
        "status": "QUEUED",
        "estimated_time_seconds": 600
    }
}
```

**Response: Job Progress (WebSocket or Polling)**
```python
GET /training/jobs/{id}
{
    "data": {
        "job_id": "uuid",
        "status": "RUNNING",
        "progress": 0.65,
        "current_epoch": 130,
        "total_epochs": 200,
        "metrics": {
            "train_loss": 0.0234,
            "val_loss": 0.0287,
            "val_auc": 0.9542
        },
        "started_at": "2026-01-17T15:00:00Z",
        "eta_seconds": 180
    }
}
```

### 4. Model APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/models` | List all models |
| `GET` | `/models/{id}` | Get model details |
| `POST` | `/models/{id}/promote` | Promote to staging/prod |
| `POST` | `/models/{id}/rollback` | Rollback to previous |
| `GET` | `/models/{id}/metrics` | Get performance metrics |
| `POST` | `/models/{id}/baselines` | Set baseline thresholds |
| `GET` | `/models/compare` | Compare multiple models |

**Request: Set Baselines**
```python
POST /models/{id}/baselines
{
    "baselines": [
        {"metric": "precision", "threshold": 0.90, "operator": "gte"},
        {"metric": "recall", "threshold": 0.85, "operator": "gte"},
        {"metric": "f1_score", "threshold": 0.87, "operator": "gte"},
        {"metric": "auc_roc", "threshold": 0.95, "operator": "gte"},
        {"metric": "fpr", "threshold": 0.05, "operator": "lte"}
    ]
}
```

### 5. Inference APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/predict` | Single prediction |
| `POST` | `/predict/batch` | Batch predictions |
| `POST` | `/predict/explain` | Prediction with explanation |

**Request: Predict with Explanation**
```python
POST /predict/explain
{
    "model_id": "uuid",  # Optional, uses production model if not specified
    "transaction": {
        "transaction_id": "TXN123",
        "amount": 5000.00,
        "merchant_id": "M456",
        "user_id": "U789",
        "timestamp": "2026-01-17T15:00:00Z",
        "device_type": "mobile",
        "location": "IN"
    }
}

Response: 200 OK
{
    "data": {
        "prediction_id": "uuid",
        "fraud_score": 0.87,
        "is_fraud": true,
        "confidence": 0.92,
        "explanation": {
            "top_features": [
                {"feature": "amount_zscore", "contribution": 0.35, "value": 3.2},
                {"feature": "velocity_24h", "contribution": 0.28, "value": 12},
                {"feature": "new_device", "contribution": 0.18, "value": 1}
            ]
        },
        "model_version": "2.1.0",
        "latency_ms": 45
    }
}
```

### 6. Monitoring APIs (Drift)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/monitoring/drift` | Get drift metrics |
| `GET` | `/monitoring/drift/features` | Per-feature drift |
| `POST` | `/monitoring/drift/compute` | Trigger drift analysis |
| `GET` | `/monitoring/performance` | Performance over time |

**Response: Drift Metrics**
```python
GET /monitoring/drift?model_id={id}&window=7d
{
    "data": {
        "model_id": "uuid",
        "window": "7d",
        "data_drift": {
            "overall_psi": 0.18,
            "status": "WARNING",  # OK, WARNING, CRITICAL
            "features": [
                {"name": "amount", "psi": 0.25, "status": "CRITICAL"},
                {"name": "velocity_24h", "psi": 0.12, "status": "OK"},
                {"name": "device_type", "chi_square_p": 0.03, "status": "WARNING"}
            ]
        },
        "concept_drift": {
            "performance_degradation": -0.05,
            "baseline_precision": 0.92,
            "current_precision": 0.87,
            "status": "WARNING"
        },
        "computed_at": "2026-01-17T15:00:00Z"
    }
}
```

### 7. Bias APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/bias/protected-attributes` | List protected attributes |
| `POST` | `/bias/protected-attributes` | Configure protected attrs |
| `GET` | `/bias/metrics` | Get bias metrics |
| `POST` | `/bias/audit` | Generate bias audit report |

**Response: Bias Metrics**
```python
GET /bias/metrics?model_id={id}
{
    "data": {
        "model_id": "uuid",
        "protected_attributes": [
            {
                "attribute": "gender",
                "groups": ["male", "female"],
                "metrics": {
                    "demographic_parity_diff": 0.08,
                    "equalized_odds_diff": 0.06,
                    "disparate_impact": 0.89,
                    "fpr_parity_diff": 0.02
                },
                "status": "OK",
                "group_breakdown": {
                    "male": {"fpr": 0.03, "tpr": 0.88, "selection_rate": 0.12},
                    "female": {"fpr": 0.035, "tpr": 0.86, "selection_rate": 0.11}
                }
            },
            {
                "attribute": "age_group",
                "groups": ["18-25", "26-45", "46+"],
                "metrics": {
                    "demographic_parity_diff": 0.15,
                    "disparate_impact": 0.72
                },
                "status": "WARNING"
            }
        ],
        "computed_at": "2026-01-17T15:00:00Z"
    }
}
```

### 8. Alert APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/alerts` | List alerts |
| `GET` | `/alerts/{id}` | Get alert details |
| `POST` | `/alerts/{id}/acknowledge` | Acknowledge alert |
| `POST` | `/alerts/{id}/dismiss` | Dismiss alert |
| `POST` | `/alerts/rules` | Configure alert rules |

### 9. Retraining APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/retraining/trigger` | Trigger manual retraining |
| `GET` | `/retraining/jobs` | List retraining jobs |
| `GET` | `/retraining/jobs/{id}` | Retraining job status |
| `POST` | `/retraining/jobs/{id}/promote` | Promote retrained model |

**Request: Trigger Retraining**
```python
POST /retraining/trigger
{
    "model_id": "uuid",
    "reason": "Data drift detected",
    "data_strategy": {
        "type": "merge",
        "new_dataset_id": "uuid",
        "historical_dataset_id": "uuid",
        "sample_weights": {"new": 0.7, "historical": 0.3}
    },
    "auto_promote": false
}
```

---

## Database Schema (SQL)

```sql
-- Datasets
CREATE TABLE datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50) NOT NULL DEFAULT '1.0',
    storage_path VARCHAR(500) NOT NULL,
    row_count INTEGER,
    schema JSONB,
    status VARCHAR(50) DEFAULT 'ACTIVE',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Feature Sets
CREATE TABLE feature_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    feature_config JSONB NOT NULL,
    storage_path VARCHAR(500),
    feature_count INTEGER,
    status VARCHAR(50) DEFAULT 'PENDING',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ML Models
CREATE TABLE ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    algorithm VARCHAR(100) NOT NULL,
    hyperparameters JSONB,
    metrics JSONB,
    storage_path VARCHAR(500) NOT NULL,
    feature_set_id UUID REFERENCES feature_sets(id),
    status VARCHAR(50) DEFAULT 'TRAINED',  -- TRAINED, STAGING, PRODUCTION, ARCHIVED
    promoted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name, version)
);

-- Baselines
CREATE TABLE baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES ml_models(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    threshold FLOAT NOT NULL,
    operator VARCHAR(10) NOT NULL,  -- gte, lte, eq
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Predictions (partitioned by date for performance)
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES ml_models(id),
    input_features JSONB NOT NULL,
    fraud_score FLOAT NOT NULL,
    is_fraud BOOLEAN NOT NULL,
    explanation JSONB,
    actual_label BOOLEAN,  -- NULL until labeled
    latency_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Drift Metrics
CREATE TABLE drift_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES ml_models(id) ON DELETE CASCADE,
    drift_type VARCHAR(50) NOT NULL,  -- DATA, CONCEPT, FEATURE
    feature_name VARCHAR(100),
    metric_name VARCHAR(100) NOT NULL,  -- psi, ks_statistic, chi_square_p
    value FLOAT NOT NULL,
    status VARCHAR(50) NOT NULL,  -- OK, WARNING, CRITICAL
    window_start TIMESTAMP WITH TIME ZONE,
    window_end TIMESTAMP WITH TIME ZONE,
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Bias Metrics
CREATE TABLE bias_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES ml_models(id) ON DELETE CASCADE,
    protected_attribute VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    group_values JSONB NOT NULL,
    overall_value FLOAT NOT NULL,
    status VARCHAR(50) NOT NULL,
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Protected Attributes Configuration
CREATE TABLE protected_attributes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attribute_name VARCHAR(100) NOT NULL UNIQUE,
    column_name VARCHAR(100) NOT NULL,
    groups JSONB NOT NULL,
    thresholds JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alerts
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES ml_models(id),
    alert_type VARCHAR(50) NOT NULL,  -- DRIFT, BIAS, PERFORMANCE, LATENCY
    severity VARCHAR(20) NOT NULL,  -- INFO, WARNING, CRITICAL
    title VARCHAR(255) NOT NULL,
    details JSONB,
    status VARCHAR(50) DEFAULT 'ACTIVE',  -- ACTIVE, ACKNOWLEDGED, DISMISSED
    acknowledged_by UUID REFERENCES users(id),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Training Jobs
CREATE TABLE training_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    feature_set_id UUID REFERENCES feature_sets(id),
    algorithm VARCHAR(100) NOT NULL,
    hyperparameters JSONB,
    status VARCHAR(50) DEFAULT 'QUEUED',  -- QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED
    progress FLOAT DEFAULT 0,
    metrics JSONB,
    error_message TEXT,
    model_id UUID REFERENCES ml_models(id),  -- Set when completed
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_datasets_name ON datasets(name);
CREATE INDEX idx_models_status ON ml_models(status);
CREATE INDEX idx_predictions_model_date ON predictions(model_id, created_at);
CREATE INDEX idx_drift_model_date ON drift_metrics(model_id, computed_at);
CREATE INDEX idx_bias_model_attr ON bias_metrics(model_id, protected_attribute);
CREATE INDEX idx_alerts_status ON alerts(status, created_at);
CREATE INDEX idx_training_jobs_status ON training_jobs(status);
```

---

## Complexity Estimates

### Backend Components

| Component | Files | Functions | LOC Est. | Complexity | Dev Days |
|-----------|-------|-----------|----------|------------|----------|
| Core (config, db, security) | 6 | 25 | 600 | Medium | 3 |
| Data Service | 8 | 30 | 800 | Medium | 4 |
| Feature Service | 8 | 35 | 1000 | High | 5 |
| Training Service | 10 | 40 | 1200 | High | 6 |
| Model Service | 8 | 30 | 800 | Medium | 4 |
| Inference Service | 6 | 25 | 700 | Medium | 3 |
| Drift Service | 8 | 35 | 900 | High | 5 |
| Bias Service | 8 | 30 | 800 | High | 5 |
| Alert Service | 6 | 20 | 500 | Low | 2 |
| Retraining Service | 8 | 30 | 800 | High | 5 |
| Celery Workers | 5 | 20 | 500 | Medium | 3 |
| **Total Backend** | ~81 | ~320 | ~8600 | | **45 days** |

### ML Components

| Component | Files | Functions | LOC Est. | Complexity | Dev Days |
|-----------|-------|-----------|----------|------------|----------|
| Algorithms (4 models) | 4 | 24 | 600 | Medium | 3 |
| Feature Engineering | 4 | 30 | 800 | High | 4 |
| Drift Detection | 3 | 20 | 500 | Medium | 3 |
| Bias Detection | 2 | 15 | 400 | Medium | 2 |
| Explainability | 2 | 10 | 300 | Medium | 2 |
| **Total ML** | ~15 | ~99 | ~2600 | | **14 days** |

### Frontend Components

| Component | Files | Components | LOC Est. | Complexity | Dev Days |
|-----------|-------|------------|----------|------------|----------|
| Core (routing, store) | 6 | - | 500 | Medium | 2 |
| Common Components | 15 | 20 | 1000 | Low | 4 |
| Dashboard Page | 8 | 12 | 800 | Medium | 4 |
| Data Registry Page | 6 | 8 | 600 | Medium | 3 |
| Training Page | 8 | 12 | 900 | High | 5 |
| Model Registry Page | 6 | 10 | 700 | Medium | 3 |
| Monitoring Page | 8 | 14 | 1000 | High | 5 |
| Bias Page | 6 | 10 | 700 | Medium | 3 |
| Alerts Page | 5 | 8 | 500 | Low | 2 |
| **Total Frontend** | ~68 | ~94 | ~6700 | | **31 days** |

**Total Development Estimate**: 90 days = 18 weeks (with 1 dev per track)
**With 3 parallel developers**: ~6-7 weeks

---

## Sprint Planning (6 Sprints × 2 Weeks)

### Sprint 1: Foundation (Weeks 1-2)

| ID | Task | Component | Hours | Owner |
|----|------|-----------|-------|-------|
| BE-001 | Setup FastAPI project structure | Backend | 4 | Backend |
| BE-002 | Configure PostgreSQL + Alembic | Backend | 6 | Backend |
| BE-003 | Configure Redis connection | Backend | 3 | Backend |
| BE-004 | Setup Azure Blob Storage client | Backend | 4 | Backend |
| BE-005 | Implement base exception handling | Backend | 4 | Backend |
| BE-006 | Configure logging + App Insights | Backend | 4 | Backend |
| BE-007 | Dataset CRUD endpoints | Backend | 12 | Backend |
| BE-008 | Dataset upload to Blob | Backend | 8 | Backend |
| FE-001 | Setup Vite + React + TypeScript | Frontend | 4 | Frontend |
| FE-002 | Configure routing (React Router) | Frontend | 3 | Frontend |
| FE-003 | Setup Zustand stores | Frontend | 4 | Frontend |
| FE-004 | Create base UI components | Frontend | 12 | Frontend |
| FE-005 | Sidebar + Layout components | Frontend | 8 | Frontend |
| FE-006 | Data Registry page (list/upload) | Frontend | 12 | Frontend |
| INF-001 | Terraform base (RG, VNet) | Infra | 6 | DevOps |
| INF-002 | CI pipeline (lint, test) | Infra | 4 | DevOps |

**Sprint Goal**: Users can upload and browse datasets

### Sprint 2: Features + Training Setup (Weeks 3-4)

| ID | Task | Component | Hours | Owner |
|----|------|-----------|-------|-------|
| BE-010 | Feature engineering service | Backend | 16 | Backend |
| BE-011 | Feature computation Celery worker | Backend | 8 | Backend |
| BE-012 | Feature Store (Redis) integration | Backend | 8 | Backend |
| BE-013 | Training job endpoints | Backend | 12 | Backend |
| BE-014 | Algorithm library service | Backend | 8 | Backend |
| ML-001 | Transaction features | ML | 8 | Data Scientist |
| ML-002 | Behavioral features | ML | 8 | Data Scientist |
| ML-003 | Temporal/Aggregation features | ML | 8 | Data Scientist |
| ML-004 | Isolation Forest implementation | ML | 6 | Data Scientist |
| ML-005 | XGBoost implementation | ML | 6 | Data Scientist |
| FE-010 | Training page (config form) | Frontend | 12 | Frontend |
| FE-011 | Training progress component | Frontend | 8 | Frontend |
| FE-012 | Algorithm selector component | Frontend | 6 | Frontend |
| DB-001 | Create all migration files | Database | 8 | DBA |

**Sprint Goal**: Users can configure and start training jobs

### Sprint 3: Model Registry + Baselines (Weeks 5-6)

| ID | Task | Component | Hours | Owner |
|----|------|-----------|-------|-------|
| BE-020 | Model registry endpoints | Backend | 12 | Backend |
| BE-021 | Model promotion workflow | Backend | 10 | Backend |
| BE-022 | Baseline configuration endpoints | Backend | 8 | Backend |
| BE-023 | Inference service (real-time) | Backend | 12 | Backend |
| BE-024 | Protected attribute config | Backend | 6 | Backend |
| ML-006 | SHAP explainer integration | ML | 10 | Data Scientist |
| FE-020 | Model Registry page | Frontend | 12 | Frontend |
| FE-021 | Model details + metrics view | Frontend | 10 | Frontend |
| FE-022 | Baseline configuration UI | Frontend | 8 | Frontend |
| FE-023 | Model promotion buttons | Frontend | 4 | Frontend |

**Sprint Goal**: Users can view models, set baselines, promote to production

### Sprint 4: Drift Detection (Weeks 7-8)

| ID | Task | Component | Hours | Owner |
|----|------|-----------|-------|-------|
| BE-030 | Drift monitoring service | Backend | 12 | Backend |
| BE-031 | Drift computation Celery worker | Backend | 10 | Backend |
| BE-032 | Drift API endpoints | Backend | 8 | Backend |
| ML-010 | PSI calculation | ML | 6 | Data Scientist |
| ML-011 | KS-test implementation | ML | 6 | Data Scientist |
| ML-012 | Chi-square for categorical | ML | 4 | Data Scientist |
| ML-013 | Concept drift detection | ML | 8 | Data Scientist |
| FE-030 | Monitoring dashboard page | Frontend | 16 | Frontend |
| FE-031 | Drift charts (time-series) | Frontend | 12 | Frontend |
| FE-032 | Feature drift breakdown | Frontend | 10 | Frontend |

**Sprint Goal**: Data drift and concept drift detection operational

### Sprint 5: Bias + Alerts (Weeks 9-10)

| ID | Task | Component | Hours | Owner |
|----|------|-----------|-------|-------|
| BE-040 | Bias metrics service | Backend | 12 | Backend |
| BE-041 | Bias computation worker | Backend | 8 | Backend |
| BE-042 | Alert service | Backend | 10 | Backend |
| BE-043 | Alert rules engine | Backend | 8 | Backend |
| ML-020 | Fairlearn integration | ML | 10 | Data Scientist |
| ML-021 | Demographic parity calc | ML | 6 | Data Scientist |
| ML-022 | Equalized odds calc | ML | 6 | Data Scientist |
| ML-023 | Disparate impact calc | ML | 4 | Data Scientist |
| FE-040 | Bias dashboard page | Frontend | 14 | Frontend |
| FE-041 | Protected attribute config UI | Frontend | 8 | Frontend |
| FE-042 | Alerts page | Frontend | 10 | Frontend |
| FE-043 | Alert notification component | Frontend | 6 | Frontend |

**Sprint Goal**: Bias detection and alerting operational

### Sprint 6: Retraining + Polish (Weeks 11-12)

| ID | Task | Component | Hours | Owner |
|----|------|-----------|-------|-------|
| BE-050 | Retraining trigger endpoint | Backend | 8 | Backend |
| BE-051 | Retraining workflow service | Backend | 12 | Backend |
| BE-052 | Data merge logic | Backend | 8 | Backend |
| BE-053 | Retraining validation | Backend | 8 | Backend |
| FE-050 | Retraining trigger UI | Frontend | 8 | Frontend |
| FE-051 | Retraining status component | Frontend | 6 | Frontend |
| FE-052 | Dashboard summary page | Frontend | 12 | Frontend |
| INT-001 | End-to-end integration testing | All | 16 | All |
| INT-002 | Performance testing | All | 8 | Backend |
| INT-003 | Bug fixes and polish | All | 20 | All |
| DOC-001 | API documentation | Docs | 8 | Backend |
| INF-010 | Production deployment | Infra | 12 | DevOps |

**Sprint Goal**: MVP complete, tested, and deployed

---

## Testing Strategy

### Coverage Targets

| Layer | Minimum Coverage | Test Type |
|-------|------------------|-----------|
| Services | 90% | Unit |
| API Endpoints | 80% | Integration |
| ML Algorithms | 85% | Unit + Integration |
| E2E Flows | Critical paths | E2E |

### Test Commands

```bash
# Backend
cd backend
poetry run pytest --cov=app --cov-report=html

# Frontend
cd frontend
npm run test -- --coverage

# E2E
npm run test:e2e
```

---

## Open Questions for Specialists

### For Backend Developer
1. Celery vs Azure Functions for workers?
2. Preferred async pattern for long-running operations?

### For Data Scientist
1. Drift threshold defaults (PSI > 0.2)?
2. Bias threshold defaults (disparate impact < 0.8)?
3. Feature engineering window sizes?

### For Database Architect
1. Prediction table partitioning strategy?
2. TimescaleDB for time-series metrics?

### For Security Engineer
1. JWT token lifetime (access: 15min, refresh: 7days)?
2. API rate limiting per endpoint?

---

*Document prepared by: Tech Lead Persona*  
*Ready for handoff to: Backend Developer, Data Scientist, Database Architect, Security Engineer*

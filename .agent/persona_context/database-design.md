---
status: DRAFT
version: 1.0
last_updated: 2026-01-17T15:25:00+05:30
persona: Database Architect
upstream: technical-specs.md
---

# Database Design Specifications
## E-Commerce Fraud Detection MLOps Platform

## Overview

This document details the PostgreSQL database design, indexing strategy, partitioning, and optimization for the MLOps platform.

---

## Database Configuration

### Azure PostgreSQL Flexible Server

| Setting | Value | Rationale |
|---------|-------|-----------|
| **Version** | PostgreSQL 15 | Latest features, JSONB improvements |
| **SKU** | General Purpose, 4 vCores | MVP sizing |
| **Storage** | 128 GB | Expandable |
| **Backup** | Geo-redundant | Disaster recovery |
| **High Availability** | Zone redundant | 99.99% SLA |

### Connection Pooling

```python
# Use PgBouncer or SQLAlchemy pooling
SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://user:pass@host:5432/shadowhubble"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

---

## Complete Schema

### 1. Users & Auth

```sql
-- Users (managed by Azure AD B2C, minimal local storage)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    azure_ad_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'analyst',  -- admin, scientist, analyst
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_azure_id ON users(azure_ad_id);
```

### 2. Datasets

```sql
CREATE TABLE datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50) NOT NULL DEFAULT '1.0',
    storage_path VARCHAR(500) NOT NULL,
    file_format VARCHAR(50) DEFAULT 'parquet',
    file_size_bytes BIGINT,
    row_count INTEGER,
    column_count INTEGER,
    schema JSONB,  -- {"columns": [{"name": "x", "type": "float", "nullable": true}]}
    statistics JSONB,  -- {"column_stats": {"amount": {"min": 0, "max": 100000}}}
    status VARCHAR(50) DEFAULT 'ACTIVE',  -- ACTIVE, ARCHIVED, PROCESSING
    parent_id UUID REFERENCES datasets(id),  -- For versioning
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_datasets_name ON datasets(name);
CREATE INDEX idx_datasets_status ON datasets(status);
CREATE INDEX idx_datasets_created ON datasets(created_at DESC);
```

### 3. Feature Sets

```sql
CREATE TABLE feature_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Feature configuration
    config JSONB NOT NULL,  -- Complete feature engineering config
    
    -- Feature selection results
    all_features JSONB,  -- All generated features before selection
    selected_features JSONB,  -- Features after selection with scores
    selection_report JSONB,  -- MI scores, importance rankings
    
    -- Storage
    storage_path VARCHAR(500),
    
    -- Stats
    input_rows INTEGER,
    feature_count INTEGER,
    selected_feature_count INTEGER,
    
    status VARCHAR(50) DEFAULT 'PENDING',  -- PENDING, PROCESSING, COMPLETED, FAILED
    error_message TEXT,
    processing_time_seconds INTEGER,
    
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_feature_sets_dataset ON feature_sets(dataset_id);
CREATE INDEX idx_feature_sets_status ON feature_sets(status);
```

### 4. ML Models

```sql
CREATE TABLE ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    
    -- Training info
    algorithm VARCHAR(100) NOT NULL,
    hyperparameters JSONB NOT NULL,
    feature_set_id UUID REFERENCES feature_sets(id),
    training_job_id UUID,  -- References training_jobs
    
    -- Model artifacts
    storage_path VARCHAR(500) NOT NULL,
    model_size_bytes BIGINT,
    
    -- Metrics stored as JSONB for flexibility
    metrics JSONB NOT NULL,  -- {"precision": 0.92, "recall": 0.88, ...}
    
    -- Feature info
    feature_names JSONB,  -- Ordered list of feature names
    feature_importance JSONB,  -- {"amount_zscore": 0.15, ...}
    
    -- Lifecycle
    status VARCHAR(50) DEFAULT 'TRAINED',
    promoted_at TIMESTAMP WITH TIME ZONE,
    archived_at TIMESTAMP WITH TIME ZONE,
    archived_reason TEXT,
    
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(name, version)
);

CREATE INDEX idx_models_status ON ml_models(status);
CREATE INDEX idx_models_algorithm ON ml_models(algorithm);
CREATE INDEX idx_models_created ON ml_models(created_at DESC);

-- Only one PRODUCTION model at a time
CREATE UNIQUE INDEX idx_models_production ON ml_models(status) WHERE status = 'PRODUCTION';
```

### 5. Baselines

```sql
CREATE TABLE baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES ml_models(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    threshold FLOAT NOT NULL,
    operator VARCHAR(10) NOT NULL CHECK (operator IN ('gte', 'lte', 'eq', 'gt', 'lt')),
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(model_id, metric_name)
);

CREATE INDEX idx_baselines_model ON baselines(model_id);
```

### 6. Training Jobs

```sql
CREATE TABLE training_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    
    -- Configuration
    feature_set_id UUID NOT NULL REFERENCES feature_sets(id),
    algorithm VARCHAR(100) NOT NULL,
    hyperparameters JSONB NOT NULL,
    train_test_split FLOAT DEFAULT 0.8,
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'QUEUED',
    progress FLOAT DEFAULT 0,
    current_epoch INTEGER,
    total_epochs INTEGER,
    
    -- Results
    metrics JSONB,  -- Training metrics over time
    final_metrics JSONB,
    model_id UUID REFERENCES ml_models(id),
    
    -- Errors
    error_message TEXT,
    error_traceback TEXT,
    
    -- Timing
    queued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Celery task tracking
    celery_task_id VARCHAR(255),
    
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_training_jobs_status ON training_jobs(status);
CREATE INDEX idx_training_jobs_created ON training_jobs(created_at DESC);
```

### 7. Predictions (Partitioned)

```sql
-- Create partitioned table for scalability
CREATE TABLE predictions (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL,
    
    -- Input
    transaction_id VARCHAR(255),
    input_features JSONB NOT NULL,
    
    -- Output
    fraud_score FLOAT NOT NULL,
    is_fraud BOOLEAN NOT NULL,
    confidence FLOAT,
    explanation JSONB,  -- SHAP values
    
    -- Labels (for retraining)
    actual_label BOOLEAN,  -- NULL until labeled
    labeled_at TIMESTAMP WITH TIME ZONE,
    
    -- Performance
    latency_ms INTEGER,
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE predictions_2026_01 PARTITION OF predictions
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE predictions_2026_02 PARTITION OF predictions
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
-- Continue for each month...

CREATE INDEX idx_predictions_model ON predictions(model_id, created_at DESC);
CREATE INDEX idx_predictions_transaction ON predictions(transaction_id);
CREATE INDEX idx_predictions_unlabeled ON predictions(created_at) WHERE actual_label IS NULL;
```

### 8. Drift Metrics

```sql
CREATE TABLE drift_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES ml_models(id) ON DELETE CASCADE,
    
    -- Drift type
    drift_type VARCHAR(50) NOT NULL,  -- DATA, CONCEPT, FEATURE
    
    -- For feature-level drift
    feature_name VARCHAR(100),
    
    -- Metrics
    metric_name VARCHAR(100) NOT NULL,  -- psi, ks_statistic, chi_square_p, etc.
    metric_value FLOAT NOT NULL,
    
    -- Status
    status VARCHAR(50) NOT NULL,  -- OK, WARNING, CRITICAL
    threshold_used FLOAT,
    
    -- Time window
    window_start TIMESTAMP WITH TIME ZONE,
    window_end TIMESTAMP WITH TIME ZONE,
    reference_window_start TIMESTAMP WITH TIME ZONE,
    reference_window_end TIMESTAMP WITH TIME ZONE,
    
    -- Sample sizes
    reference_count INTEGER,
    current_count INTEGER,
    
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_drift_model_date ON drift_metrics(model_id, computed_at DESC);
CREATE INDEX idx_drift_type ON drift_metrics(drift_type, computed_at DESC);
CREATE INDEX idx_drift_status ON drift_metrics(status) WHERE status != 'OK';
```

### 9. Bias Metrics

```sql
CREATE TABLE bias_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES ml_models(id) ON DELETE CASCADE,
    
    -- Protected attribute
    protected_attribute VARCHAR(100) NOT NULL,
    
    -- Metric
    metric_name VARCHAR(100) NOT NULL,  -- demographic_parity_diff, equalized_odds_diff, etc.
    
    -- Values
    overall_value FLOAT NOT NULL,
    group_values JSONB NOT NULL,  -- {"male": 0.12, "female": 0.11}
    
    -- Status
    status VARCHAR(50) NOT NULL,  -- OK, WARNING, CRITICAL
    threshold_used FLOAT,
    
    -- Sample info
    sample_size INTEGER,
    group_sizes JSONB,  -- {"male": 5000, "female": 4800}
    
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_bias_model ON bias_metrics(model_id, computed_at DESC);
CREATE INDEX idx_bias_attribute ON bias_metrics(protected_attribute);
CREATE INDEX idx_bias_status ON bias_metrics(status) WHERE status != 'OK';
```

### 10. Protected Attributes Configuration

```sql
CREATE TABLE protected_attributes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attribute_name VARCHAR(100) NOT NULL UNIQUE,
    column_name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Groups
    groups JSONB NOT NULL,  -- ["male", "female", "other"]
    
    -- Thresholds per metric
    thresholds JSONB NOT NULL,  -- {"demographic_parity_diff": 0.1, "disparate_impact_min": 0.8}
    
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 11. Alerts

```sql
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Source
    model_id UUID REFERENCES ml_models(id),
    source_type VARCHAR(50) NOT NULL,  -- DRIFT, BIAS, PERFORMANCE, SYSTEM
    source_id UUID,  -- Reference to drift_metric or bias_metric
    
    -- Alert info
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('INFO', 'WARNING', 'CRITICAL')),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    details JSONB,  -- Detailed context
    
    -- Status
    status VARCHAR(50) DEFAULT 'ACTIVE',  -- ACTIVE, ACKNOWLEDGED, RESOLVED, DISMISSED
    
    -- Resolution
    acknowledged_by UUID REFERENCES users(id),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    
    -- Auto-actions
    triggered_retraining BOOLEAN DEFAULT FALSE,
    retraining_job_id UUID,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_alerts_status ON alerts(status, created_at DESC);
CREATE INDEX idx_alerts_model ON alerts(model_id, created_at DESC);
CREATE INDEX idx_alerts_severity ON alerts(severity, created_at DESC);
CREATE INDEX idx_alerts_active ON alerts(created_at DESC) WHERE status = 'ACTIVE';
```

### 12. Audit Log

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Actor
    user_id UUID REFERENCES users(id),
    user_email VARCHAR(255),
    
    -- Action
    action VARCHAR(100) NOT NULL,  -- CREATE, UPDATE, DELETE, PROMOTE, RETRAIN
    resource_type VARCHAR(100) NOT NULL,  -- model, dataset, baseline
    resource_id UUID,
    
    -- Details
    old_values JSONB,
    new_values JSONB,
    metadata JSONB,
    
    -- Context
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(255),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_action ON audit_logs(action, created_at DESC);
```

---

## Indexing Strategy

### Index Types Used

| Index Type | Use Case |
|------------|----------|
| B-tree (default) | Equality, range queries |
| Partial | Filter commonly queried subsets |
| JSONB GIN | Search within JSON documents |
| Unique | Enforce constraints |

### Critical Indexes

```sql
-- Performance-critical queries
CREATE INDEX CONCURRENTLY idx_models_production_fast 
    ON ml_models(id) WHERE status = 'PRODUCTION';

-- JSONB indexes for feature search
CREATE INDEX idx_feature_sets_selected_features 
    ON feature_sets USING GIN (selected_features);

-- Predictions time-series
CREATE INDEX idx_predictions_timeseries 
    ON predictions(model_id, created_at DESC);
```

---

## Migrations

### Alembic Setup

```bash
# Initialize
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Migration Best Practices

1. **Always add indexes concurrently** in production
2. **Never drop columns** - mark as deprecated first
3. **Test migrations** on staging with production data copy
4. **Keep migrations reversible** when possible

---

*Document prepared by: Database Architect Persona*

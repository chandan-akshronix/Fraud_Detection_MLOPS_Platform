---
status: IN_PROGRESS
version: 1.0
last_updated: 2026-01-17T15:30:00+05:30
review_cycle: 1
---

# Cross-Persona Review Session
## Shadow Hubble - Architecture Perfection

This document captures the brainstorming and error-correction session where all personas review and critique each other's work to perfect the architecture.

---

## Review Summary

| Reviewer | Document Reviewed | Verdict | Critical Issues | Major Issues |
|----------|-------------------|---------|-----------------|--------------|
| Product Manager | business-strategy.md | APPROVED | 0 | 1 |
| Enterprise Architect | product-requirements.md | CHANGES_REQUESTED | 2 | 3 |
| Tech Lead | architecture-decisions.md | CHANGES_REQUESTED | 1 | 4 |
| Backend Developer | technical-specs.md | CHANGES_REQUESTED | 1 | 2 |
| Security Engineer | All Documents | CHANGES_REQUESTED | 3 | 2 |
| Data Scientist | architecture-decisions.md | CHANGES_REQUESTED | 2 | 2 |
| DBA | data-science-specs.md | CHANGES_REQUESTED | 1 | 2 |
| UX Lead | product-requirements.md | APPROVED | 0 | 2 |

---

## 1. Product Manager → Business Strategy

**Reviewer**: Product Manager  
**Document**: business-strategy.md  
**Verdict**: ✅ APPROVED with minor suggestions

### Positive Observations
- Clear problem statement for fraud detection
- Solid ROI calculation (4-13x return)
- Good feature pillar structure

### Minor Issues
1. **Timeline Risk**
   - 3-month timeline is aggressive for full platform
   - Suggestion: Define explicit MVP cut-off criteria

---

## 2. Enterprise Architect → Product Requirements

**Reviewer**: Enterprise Architect  
**Document**: product-requirements.md  
**Verdict**: ⚠️ CHANGES_REQUESTED

### Critical Issues

1. **Missing: Model Serving Strategy**
   - Problem: PRD mentions inference but doesn't specify HOW models are served
   - Impact: Architecture cannot be finalized without this
   - Suggested Fix: Add user story for model serving infrastructure
   ```
   As an ML Engineer, I want models served with <100ms latency
   so that fraud detection doesn't slow checkout
   ```
   - Justification: Model serving is critical architectural decision

2. **Missing: Feature Store Consistency**
   - Problem: Training and inference may use different feature values
   - Impact: Training-serving skew causes silent accuracy degradation
   - Suggested Fix: Add feature for "Feature consistency validation"

### Major Issues

1. **Incomplete: Retraining Data Volume Handling**
   - 10L streaming + 1L labeled = potential memory issues
   - Add data sampling strategy for large datasets

2. **Missing: Model Rollback Procedure**
   - What happens if promoted model performs poorly?
   - Add rollback user story with automatic trigger

3. **Unclear: Baseline Version Management**
   - When model is retrained, are baselines reset or carried over?
   - Clarify baseline lifecycle

---

## 3. Tech Lead → Architecture Decisions

**Reviewer**: Tech Lead  
**Document**: architecture-decisions.md  
**Verdict**: ⚠️ CHANGES_REQUESTED

### Critical Issues

1. **ADR-002 Gap: Redis Feature Store Limitations**
   - Problem: Redis has 512MB max value size, complex features may exceed
   - Impact: Large feature sets could fail silently
   - Suggested Fix: Add fallback to Blob storage for large feature sets
   - Alternative: Use Redis Cluster with data sharding

### Major Issues

1. **Missing: Azure ML vs Self-Managed Training**
   - ADR-003 chooses Azure ML, but no comparison with Celery-only approach
   - Cost difference unclear ($$ for Azure ML compute vs self-managed)
   - Add cost analysis table

2. **Incomplete: Celery Redis Single Point of Failure**
   - ADR-006 acknowledges Redis SPOF but no mitigation
   - Suggested Fix: Redis Sentinel or use Azure Cache for Redis Premium tier

3. **Missing: Model Artifact Format**
   - Should models be Pickle, ONNX, or MLflow format?
   - Affects portability and inference performance
   - Recommendation: Use ONNX for inference, MLflow for versioning

4. **Unclear: Feature Computation Timing**
   - Real-time vs batch not fully decided
   - Critical for latency requirements
   - Need explicit ADR for "Feature Computation Strategy"

---

## 4. Backend Developer → Technical Specs

**Reviewer**: Backend Developer  
**Document**: technical-specs.md  
**Verdict**: ⚠️ CHANGES_REQUESTED

### Critical Issues

1. **Missing: Celery Task Idempotency**
   - Training tasks could be retried on failure
   - Without idempotency, same model trained twice
   - Suggested Fix: Add task deduplication using job_id

### Major Issues

1. **API Contract Gap: WebSocket for Training Progress**
   - Current spec only shows REST polling
   - For real-time progress, need WebSocket endpoint
   - Add: `WS /api/v1/training/jobs/{id}/stream`

2. **Missing: Health Check Endpoints**
   - No `/health` or `/ready` endpoints defined
   - Required for Kubernetes deployments
   - Add health check API spec

---

## 5. Security Engineer → All Documents

**Reviewer**: Security Engineer  
**Document**: All  
**Verdict**: ⚠️ CHANGES_REQUESTED

### Critical Issues

1. **Data Science Spec: PII Exposure in Features**
   - Features include `user_gender`, `user_age_bucket`
   - These are protected attributes AND PII
   - Suggested Fix: Encrypt protected attributes at rest
   - Add data masking for logs and API responses

2. **Database Design: Missing Row-Level Security**
   - Multi-tenant scenarios not addressed
   - Users could potentially access other users' data
   - Add PostgreSQL RLS policies

3. **Backend: API Key Management Missing**
   - External e-commerce integration uses API keys
   - No key rotation, revocation, or scoping defined
   - Add API key management service

### Major Issues

1. **Missing: Model Integrity Verification**
   - Model files could be tampered with
   - Add SHA-256 checksum verification on load

2. **Audit Log Gap: Prediction Logging**
   - Predictions contain fraud scores (sensitive)
   - Need to define what is logged vs masked

---

## 6. Data Scientist → Architecture Decisions

**Reviewer**: Data Scientist  
**Document**: architecture-decisions.md  
**Verdict**: ⚠️ CHANGES_REQUESTED

### Critical Issues

1. **Missing: ML Experiment Tracking**
   - Architecture doesn't mention experiment tracking
   - How do we compare multiple training runs?
   - Suggested Fix: Add MLflow or Azure ML experiment tracking
   - Store: hyperparameters, metrics, artifacts per run

2. **Missing: Model Performance Monitoring Dashboard**
   - Drift detection exists, but no real-time performance view
   - Need sliding window accuracy/precision charts
   - Add to monitoring service

### Major Issues

1. **Feature Store: Missing Feature Versioning**
   - Features evolve, but no versioning strategy
   - Training data and inference could use different feature versions
   - Add feature version tracking

2. **Incomplete: Handling Imbalanced Data**
   - Fraud datasets are highly imbalanced (1-5% fraud)
   - XGBoost has `scale_pos_weight`, but no mention of:
     - SMOTE/undersampling in pipeline
     - Class weight configuration in UI
   - Add imbalanced data handling strategy

---

## 7. Database Architect → Data Science Specs

**Reviewer**: Database Architect  
**Document**: data-science-specs.md  
**Verdict**: ⚠️ CHANGES_REQUESTED

### Critical Issues

1. **Feature Store: Redis vs PostgreSQL Consistency**
   - Features cached in Redis but feature_sets stored in PostgreSQL
   - On Redis failure, where are features recomputed from?
   - Need: Feature recomputation strategy from Blob storage

### Major Issues

1. **Missing: Feature Computation Job Tracking**
   - Feature engineering is long-running but no job table in DB schema
   - Add `feature_computation_jobs` table similar to `training_jobs`

2. **Aggregation Features: Time Zone Handling**
   - Rolling windows (24h, 7d) need timezone consistency
   - All timestamps should be UTC
   - Document timezone handling policy

---

## 8. UX Design Lead → Product Requirements

**Reviewer**: UX Design Lead  
**Document**: product-requirements.md  
**Verdict**: ✅ APPROVED with suggestions

### Positive Observations
- Clear user personas (Maya, Raj, Priya)
- Well-defined user journeys
- Good acceptance criteria

### Major Issues (Suggestions)

1. **Missing: Error State Designs**
   - What does user see when training fails?
   - Add error message guidelines

2. **Missing: Empty State Designs**
   - New user sees empty dashboard - what's the onboarding?
   - Add first-time user experience spec

---

## 9. Collective Brainstorming: Missing Pieces

After all reviews, the following gaps were identified collectively:

### Architecture Gaps
| Gap | Impact | Proposed Solution |
|-----|--------|-------------------|
| Model serving strategy | High | Add ADR for model serving (FastAPI vs Seldon) |
| Experiment tracking | Medium | Integrate MLflow for run tracking |
| Feature versioning | High | Add version column to feature_sets |
| Model artifact format | Medium | ONNX for inference, MLflow for storage |
| API key management | High | Add key rotation and scoping |

### Data Gaps
| Gap | Impact | Proposed Solution |
|-----|--------|-------------------|
| Imbalanced data handling | High | Add SMOTE option in training config |
| Feature recomputation | Medium | Store raw features in Blob, recompute on cache miss |
| Timezone handling | Low | Enforce UTC everywhere, convert on display |

### Security Gaps
| Gap | Impact | Proposed Solution |
|-----|--------|-------------------|
| PII in features | High | Encrypt at rest, mask in logs |
| Row-level security | Medium | Add PostgreSQL RLS policies |
| Model integrity | Medium | SHA-256 checksums on model files |

### UX Gaps
| Gap | Impact | Proposed Solution |
|-----|--------|-------------------|
| Error states | Medium | Design error message guidelines |
| Empty states | Low | Add onboarding wizard for new users |
| Loading states | Low | Add skeleton loaders for all pages |

---

## Consolidated Changes Required

### High Priority (Must Fix Before Implementation)

1. **Add ADR-008: Model Serving Strategy**
   - Decision: Use FastAPI with ONNX runtime for inference
   - Rationale: Simple, fast, no additional infrastructure

2. **Add ADR-009: Feature Versioning**
   - All feature sets must be versioned
   - Training stores feature_set_version with model
   - Inference loads correct version

3. **Add ADR-010: Model Artifact Format**
   - Use ONNX for production inference
   - Store original format (pickle/joblib) for debugging
   - MLflow for experiment tracking and registry

4. **Update Database Schema**
   - Add `feature_computation_jobs` table
   - Add `feature_version` column to `feature_sets`
   - Add `model_checksum` column to `ml_models`

5. **Security Enhancements**
   - Encrypt protected attributes in predictions table
   - Add API key table with rotation support
   - Add row-level security policies

### Medium Priority (Should Fix)

6. **Add experiment tracking integration (MLflow)**

7. **Add imbalanced data handling options**
   - `sampling_strategy`: "none", "smote", "undersample"
   - Default: "none" (use class weights)

8. **Add WebSocket endpoint for training progress**

9. **Add health check endpoints**

10. **Design error and empty states for UI**

---

## Action Items for Each Persona

### Enterprise Architect
- [ ] Create ADR-008: Model Serving Strategy
- [ ] Create ADR-009: Feature Versioning  
- [ ] Create ADR-010: Model Artifact Format
- [ ] Update Redis fallback strategy

### Tech Lead
- [ ] Add WebSocket spec for training progress
- [ ] Add health check endpoints
- [ ] Document Celery idempotency strategy

### Backend Developer
- [ ] Implement API key management service
- [ ] Add model checksum verification
- [ ] Implement feature cache miss fallback

### Data Scientist
- [ ] Add experiment tracking to training pipeline
- [ ] Add imbalanced data handling options
- [ ] Document feature versioning strategy

### Database Architect
- [ ] Add `feature_computation_jobs` table
- [ ] Add row-level security policies
- [ ] Add encrypted columns for PII

### Security Engineer
- [ ] Define API key rotation policy
- [ ] Specify PII encryption requirements
- [ ] Add model integrity verification spec

### UX Design Lead
- [ ] Design error state components
- [ ] Design empty state / onboarding flow
- [ ] Add loading skeleton specs

---

*Review Session facilitated by: Multi-Agent Orchestrator*
*Next Step: Apply high-priority changes to all documents*

---
status: DRAFT
version: 1.0
last_updated: 2026-01-17T15:25:00+05:30
persona: Security Engineer
upstream: architecture-decisions.md
---

# Security Analysis
## E-Commerce Fraud Detection MLOps Platform

## Authentication

### Azure AD B2C
- **Token Type**: JWT (OAuth 2.0 + OIDC)
- **Access Token Lifetime**: 15 minutes
- **Refresh Token Lifetime**: 7 days
- **MFA**: Admin-enforced for production

## Authorization (RBAC)

| Role | Permissions |
|------|-------------|
| **admin** | Full access, user management |
| **scientist** | Train models, manage datasets |
| **analyst** | View models, predictions, alerts |
| **api_client** | Inference only |

## API Security

### Rate Limiting
| Endpoint | Limit |
|----------|-------|
| `/predict` | 1000/min |
| `/training/jobs` | 10/hour |
| General API | 100/min |

### Input Validation
- All inputs via Pydantic with strict validators
- SQL injection prevented via parameterized queries
- XSS prevented via output encoding

## Data Security

| Data Type | At Rest | In Transit |
|-----------|---------|------------|
| PostgreSQL | AES-256 | TLS 1.2+ |
| Redis | AES-256 | TLS 1.2+ |
| Blob Storage | AES-256 | HTTPS |

## Secrets Management
- All secrets in Azure Key Vault
- No secrets in code or environment files
- Managed Identity for Azure services

## Audit Logging
- User login/logout
- Model promotions
- Dataset operations
- Configuration changes
- Permission denials

## Security Checklist
- [ ] All secrets in Key Vault
- [ ] TLS certificates configured
- [ ] Rate limiting enabled
- [ ] Audit logging operational
- [ ] Dependencies scanned

*Document prepared by: Security Engineer Persona*

---
description: Generate executive summary of all persona outputs
---

# Executive Summary Generator

This workflow produces a concise overview of the current project state across all personas.

## When to Use

- `/summary` - Generate summary on demand
- After each major phase completion
- Before user check-ins
- When switching context or resuming work

## Summary Template

```markdown
# Project Summary: [Project Name]

**Generated**: [timestamp]
**Current Phase**: [phase]
**Overall Status**: [On Track / At Risk / Blocked]

---

## 🎯 Business Context
**Problem**: [one sentence]
**Target Users**: [user segments]
**Success Metric**: [primary KPI and target]

---

## 📋 Product Scope
**MVP Features**: [count] features across [count] epics
**Timeline**: [estimated completion]
**Priority Focus**: [current P0 items]

---

## 🏗️ Architecture
**Stack**: React+TypeScript | FastAPI | Azure PostgreSQL | Azure
**Services**: [count] microservices
**Key Patterns**: [main architectural patterns]

---

## 💻 Implementation Status

| Component | Status | Completion | Blockers |
|-----------|--------|------------|----------|
| Backend APIs | [status] | [%] | [any] |
| Database | [status] | [%] | [any] |
| Frontend | [status] | [%] | [any] |
| Auth | [status] | [%] | [any] |

---

## 🔒 Security Posture
**Risk Level**: [Low/Medium/High]
**Key Controls**: [top 3 security measures]
**Pending**: [security items not yet addressed]

---

## 🎨 UX Status
**Screens Designed**: [count]
**User Flows**: [count] documented
**Design System**: [Complete/In Progress/Not Started]

---

## 📊 Data/ML (if applicable)
**Models**: [count and types]
**Pipeline Status**: [status]
**Training Data**: [status]

---

## ⚠️ Risks & Blockers

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| [risk] | [H/M/L] | [H/M/L] | [action] |

---

## 📅 Next Steps
1. [Immediate next action]
2. [Second priority]
3. [Third priority]

---

## 📁 Document Index
| Document | Last Updated | Status |
|----------|--------------|--------|
| business-strategy.md | [date] | [status] |
| product-requirements.md | [date] | [status] |
| architecture-decisions.md | [date] | [status] |
| technical-specs.md | [date] | [status] |
| backend-implementation.md | [date] | [status] |
| database-design.md | [date] | [status] |
| security-analysis.md | [date] | [status] |
| ux-design-system.md | [date] | [status] |
```

## Summary Generation Steps

1. Read `project-manifest.md` for document list
2. For each document, extract:
   - Status (Draft/Review/Approved/Final)
   - Key metrics or counts
   - Blockers or risks
3. Compile into template above
4. Highlight any inconsistencies between documents
5. Flag overdue items

## Abbreviated Summary

For quick status checks, use this format:

```
📊 [Project] Status: [Phase] | [Status Emoji]
├── Business: ✅ Approved
├── Product: 🔄 In Review (cycle 2/4)
├── Architecture: ✅ Approved
├── Tech Specs: 📝 Draft
├── Backend: ⏳ Not Started
├── Database: ⏳ Not Started
├── Security: ⏳ Not Started
└── UX: 📝 Draft

Next: Tech Lead to complete technical specifications
Blocker: None
```

## Status Emojis

- ✅ Approved/Complete
- 🔄 In Review
- 📝 Draft
- ⏳ Not Started
- 🚫 Blocked
- ⚠️ At Risk

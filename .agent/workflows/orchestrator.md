---
description: Master orchestrator for invoking expert personas in the software development lifecycle
---

# Multi-Agent Persona Orchestrator

This workflow manages the invocation and coordination of 9 expert personas who collaborate to deliver top 1% software development outcomes.

## Tech Stack (User Defined)
- **Frontend**: React + TypeScript (Vite)
- **Backend**: Python + FastAPI
- **Cloud**: Microsoft Azure
- **Database**: Azure PostgreSQL (Flexible Server)
- **Cache**: Azure Cache for Redis
- **Queue**: Azure Service Bus
- **Storage**: Azure Blob Storage
- **Auth**: Azure AD B2C + FastAPI OAuth2
- **CI/CD**: GitHub Actions + Azure DevOps
- **Monitoring**: Azure Application Insights
- **IaC**: Terraform + Azure Resource Manager

## How to Use

### Invoke a Specific Persona
```
/persona [persona-name]
```
Example: `/persona backend-developer`

### Start a New Project (Full Lifecycle)
```
/orchestrator new "Your project idea or business problem"
```
This will:
1. Start with Chief Business Strategist to decompose the problem
2. Hand off to Product Manager for requirements
3. Continue through Architecture → Tech Lead → Specialists
4. Each persona creates their output in `.agent/persona_context/`

### Resume Existing Project
```
/orchestrator resume
```
Reads `project-state.md` and continues from where we left off.

### Get Project Summary
```
/summary
```
Generates an executive summary of all persona outputs.

## Persona Invocation Order

```
1. Chief Business Strategist  → business-strategy.md
2. Product Manager            → product-requirements.md
3. Enterprise Architect       → architecture-decisions.md
4. Tech Lead                  → technical-specs.md
5. Parallel Specialists:
   ├── Backend Developer      → backend-implementation.md
   ├── Data Scientist         → data-science-specs.md (if ML needed)
   ├── Database Architect     → database-design.md
   ├── Security Engineer      → security-analysis.md
   └── UX Design Lead         → ux-design-system.md
```

## Cross-Persona Review Protocol

After each persona completes their output:
1. Downstream persona reviews and may request changes
2. Maximum **4 review cycles** allowed
3. After 4 cycles, **User** acts as tie-breaker
4. All feedback is logged in the persona's context file

## Context Preservation

All persona outputs are stored in `.agent/persona_context/`:
- `project-manifest.md` - Master index with versions
- `project-state.md` - Current phase and pending work
- `handoff-summary.md` - Latest context for transitions
- Individual persona outputs (listed above)

## Switching Personas Mid-Conversation

When you need a different perspective:
```
/switch [persona-name]
```
This loads the new persona while preserving all context.

## Persona List

| Command | Persona | Focus |
|---------|---------|-------|
| `/persona business-strategist` | Chief Business Strategist | Problem decomposition, ROI |
| `/persona product-manager` | Product Manager | Requirements, user stories |
| `/persona architect` | Enterprise Architect | System design, tech stack |
| `/persona tech-lead` | Tech Lead | Implementation planning |
| `/persona backend` | Backend Developer | FastAPI implementation |
| `/persona data-scientist` | Data Scientist | ML/AI solutions |
| `/persona dba` | Database Architect | PostgreSQL design |
| `/persona security` | Security Engineer | Threat modeling, auth |
| `/persona ux` | UX Design Lead | User flows, design system |

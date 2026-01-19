---
description: Cross-persona review protocol with maximum 4 cycles
---

# Review Cycle Protocol

This workflow defines how personas review and improve each other's work.

## Review Principles

1. **Constructive Criticism**: Focus on improvements, not blame
2. **Actionable Feedback**: Every critique must have a specific change request
3. **Scope Boundaries**: Only review within your domain expertise
4. **Evidence-Based**: Cite industry standards, best practices, or data

## Review Cycle Flow

```
Cycle 1: Initial Review
├── Reviewer reads deliverable
├── Identifies issues (Critical, Major, Minor)
├── Provides specific change requests
└── Author revises

Cycle 2-4: Iteration
├── Author addresses feedback
├── Reviewer validates changes
├── New issues (if any) are raised
└── Continue until approved or cycle 4

Post-Cycle 4: User Tie-Break
├── If still unresolved after 4 cycles
├── Present both positions to user
└── User makes final decision
```

## Review Request Format

When requesting a review, the author must provide:

```markdown
## Review Request

**From**: [Author Persona]
**To**: [Reviewer Persona]
**Document**: [path to document]
**Review Cycle**: [1-4]

### Changes Since Last Review
- [List of changes if cycle > 1]

### Specific Questions
1. [Any specific areas needing feedback]
```

## Review Response Format

When providing a review:

```markdown
## Review Response

**Reviewer**: [Persona Name]
**Document**: [path]
**Cycle**: [1-4]
**Verdict**: [APPROVED / CHANGES_REQUESTED / BLOCKED]

### Critical Issues (Must Fix)
1. **[Issue Title]**
   - Location: [section/line]
   - Problem: [description]
   - Suggested Fix: [specific recommendation]
   - Justification: [industry standard/best practice]

### Major Issues (Should Fix)
[Same format]

### Minor Issues (Nice to Have)
[Same format]

### Positive Observations
- [What was done well]
```

## Review Triggers by Persona

| Author | Primary Reviewer | Secondary Reviewer |
|--------|-----------------|-------------------|
| Business Strategist | Product Manager | Tech Lead |
| Product Manager | Enterprise Architect | UX Lead |
| Enterprise Architect | Tech Lead | Security Engineer |
| Tech Lead | Backend Developer | DBA |
| Backend Developer | Security Engineer | Tech Lead |
| Data Scientist | Tech Lead | Backend Developer |
| Database Architect | Backend Developer | Security Engineer |
| Security Engineer | Enterprise Architect | Tech Lead |
| UX Design Lead | Product Manager | Frontend considerations |

## Escalation Protocol

If a reviewer identifies an issue outside their domain:

```markdown
## Escalation Notice

**From**: [Current Reviewer]
**To**: [Appropriate Persona]
**Regarding**: [Issue summary]
**Impact**: [Why this matters]

This issue requires [Persona]'s expertise. Please review.
```

## Cycle Counter

Track review cycles in each document's header:

```markdown
---
review_cycle: 2
last_reviewer: Security Engineer
status: CHANGES_REQUESTED
---
```

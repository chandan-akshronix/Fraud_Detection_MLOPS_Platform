---
description: Protocol for transferring context between personas
---

# Handoff Protocol

This workflow ensures smooth context transfer between personas without information loss or context window overflow.

## Handoff Principles

1. **Summarize, Don't Duplicate**: Pass summaries, not full documents
2. **Explicit Dependencies**: Clearly state what the next persona needs
3. **Decision Log**: Include key decisions and their rationale
4. **Open Questions**: Flag any unresolved items

## Handoff Document Structure

When handing off to the next persona, create/update `handoff-summary.md`:

```markdown
# Handoff Summary

**From**: [Source Persona]
**To**: [Target Persona]
**Date**: [ISO timestamp]
**Project Phase**: [Current phase]

## Executive Summary
[2-3 sentences on current state]

## Key Decisions Made
| Decision | Rationale | Impact |
|----------|-----------|--------|
| [Decision] | [Why] | [What it affects] |

## Constraints Established
- [Technical constraints]
- [Business constraints]
- [Timeline constraints]

## Open Questions for Next Persona
1. [Question needing resolution]

## Documents to Reference
| Document | Sections Relevant | Priority |
|----------|------------------|----------|
| [filename] | [sections] | [High/Medium/Low] |

## Dependencies
- Blocked by: [any blockers]
- Blocking: [what depends on this]
```

## Persona-Specific Handoffs

### Business Strategist → Product Manager
Pass forward:
- Problem statement (exact wording)
- Success metrics with targets
- User segments and their pain points
- Business constraints (budget, timeline, compliance)
- Competitive differentiation points

### Product Manager → Enterprise Architect
Pass forward:
- Feature list with priorities (P0/P1/P2)
- User stories for P0 features
- Non-functional requirements (scale, performance)
- Integration requirements
- MVP scope decisions

### Enterprise Architect → Tech Lead
Pass forward:
- System architecture diagram
- Technology stack decisions with justifications
- Service boundaries and responsibilities
- API contracts (high-level)
- Infrastructure requirements

### Tech Lead → Specialists
Pass forward:
- Assigned components
- Interface contracts
- Coding standards
- Timeline expectations
- Cross-cutting concerns

## Context Size Management

To prevent context overflow:

1. **Summary Length Limits**
   - Executive summary: 100 words max
   - Key decisions: 10 items max
   - Open questions: 5 items max

2. **Reference Instead of Include**
   ```markdown
   See [architecture-decisions.md#database-choice] for full details.
   ```

3. **Progressive Detail**
   - Handoff contains summaries
   - Persona reads full docs only as needed
   - Questions trigger specific section reads

## Handoff Verification

Before completing a handoff:

```markdown
## Handoff Checklist

- [ ] All key decisions documented
- [ ] Success metrics clearly stated
- [ ] Constraints explicitly listed
- [ ] Open questions identified
- [ ] Document references are valid
- [ ] No duplicate information from source docs
- [ ] Summary under 500 words total
```

## Emergency Context Recovery

If context is lost between sessions:

1. Read `project-state.md` for current phase
2. Read `project-manifest.md` for all documents
3. Read `handoff-summary.md` for latest context
4. Read specific persona output if details needed

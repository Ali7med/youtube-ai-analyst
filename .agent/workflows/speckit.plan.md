---
description: Update the entire spec_kit/ folder to reflect the new development plan and architecture
---

# /speckit.plan Workflow

This workflow reads the current project state, the roadmap, and updates all three spec_kit/ documents to reflect the planned architecture.

## Steps

1. Read all existing files in `spec_kit/` (PRD.md, API_SPEC.md, SYSTEM_ARCHITECTURE.md)
2. Read the ROADMAP artifact or the development plan discussed in context
3. Update `spec_kit/PRD.md` — add new features, user journeys, and target audiences from the roadmap
4. Update `spec_kit/SYSTEM_ARCHITECTURE.md` — add new layers (database, scheduler, notifications), update data flow diagram
5. Update `spec_kit/API_SPEC.md` — add all new planned API endpoints (SSE stream, jobs, watchlist, history, channels, export)
6. Confirm to the user that all three files have been updated with a summary of changes

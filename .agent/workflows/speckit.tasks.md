---
description: Generate a detailed, actionable task list from the spec_kit/ plan, broken down by phase with files, acceptance criteria, and dependencies
---

# /speckit.tasks Workflow

This workflow reads all spec_kit/ documents and converts the development plan into a structured, trackable task list saved as `spec_kit/TASKS.md`.

## Steps

1. Read `spec_kit/PRD.md`, `spec_kit/SYSTEM_ARCHITECTURE.md`, and `spec_kit/API_SPEC.md`
2. Read the existing project structure (`execution/`, `directives/`, `static/`, `app.py`, `pipeline.py`)
3. Break down each planned phase into concrete, file-level implementation tasks
4. For each task include:
   - Task ID and title
   - Files to create or modify
   - Acceptance criteria (how to verify it works)
   - Dependencies (what must be done first)
   - Estimated complexity (S/M/L/XL)
5. Save the result to `spec_kit/TASKS.md`
6. Report a summary of total tasks per phase to the user

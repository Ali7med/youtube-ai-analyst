---
description: Automatically pick the next pending task from TASKS.md and implement it
---

# /speckit.implement Workflow

This workflow reads `spec_kit/TASKS.md`, identifies the first pending task, and implements it.

## Steps

1. Read `spec_kit/TASKS.md` and find the top-most task marked with `[ ] Todo`.
2. Analyze the requirements for this specific task (files to create, logic to implement, acceptance criteria).
3. Read all relevant existing files to understand the current context.
4. Implement the changes using `write_to_file` and `multi_replace_file_content` tools.
5. Once implemented, update `spec_kit/TASKS.md` to mark the task as `[x] Done`.
6. Inform the user of what was implemented and ask if they are ready for the next task.

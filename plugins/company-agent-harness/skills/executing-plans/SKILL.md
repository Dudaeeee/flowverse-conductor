---
name: executing-plans
description: Use when implementing an existing written plan sequentially in the current workspace or when subagents are unavailable.
---

# Executing Plans

Use this skill to implement a plan without losing sequencing discipline.

## Workflow

1. Read the full plan and the files it names.
2. Check the plan for blockers, missing context, risky assumptions, or conflicts with the repository profile.
3. If the plan is not executable, stop and explain the smallest correction needed.
4. Execute one task at a time.
5. For each task, make the scoped change, run the specified verification, and record the result.
6. Request or perform review at natural checkpoints.
7. Update the plan or report drift when implementation reality differs from the plan.
8. After all tasks pass verification, move to `finishing-a-development-branch` if branch disposition is required.

## Stop Conditions

- A required dependency, credential, or environment is missing.
- Verification fails repeatedly for the same unresolved reason.
- The plan asks for destructive git operations without explicit approval.
- The plan conflicts with user instructions or repository policy.

## Report

Include completed tasks, files changed, verification commands, unresolved risks, and any plan deviations.

---
name: subagent-driven-development
description: Use when executing an implementation plan whose tasks can be delegated to independent subagents in the current session.
---

# Subagent-Driven Development

Use this skill when a written plan can be broken into independent tasks and the current tool supports subagents. The main agent stays responsible for coordination, context curation, review, and final integration.

## Workflow

1. Read the plan and extract tasks, dependencies, target files, and validation commands.
2. Reject parallel delegation for tasks that edit the same files or depend on unmerged intermediate state.
3. For each delegated task, provide the subagent with:
   - task goal and acceptance criteria
   - relevant file paths and plan excerpt
   - constraints from `AGENTS.md`, project profile, and recent decisions
   - expected output format and validation command
4. Prefer one implementer per task. Do not let subagents infer missing requirements from broad context.
5. After implementation, run a spec review: does the change satisfy the plan and avoid extra scope?
6. Then run a code review: correctness, regressions, security, maintainability, and tests.
7. Send concrete fixes back to the implementer or apply the fixes yourself when small.
8. Do not mark a task complete while spec or code review has unresolved blocking findings.
9. Run the plan-level verification after all tasks are complete.

## Guardrails

- Do not spawn subagents unless the user or tool workflow permits it.
- Do not dispatch multiple write agents into the same files.
- Do not pass the whole conversation when a concise task packet is enough.
- Do not accept a subagent's success claim without checking evidence.
- Keep the main thread focused on decisions and summaries, not raw logs.

## Report

Include task assignments, review results, fixes applied, verification commands, and remaining risks.

---
name: dispatching-parallel-agents
description: Use when splitting read-heavy exploration, review, or independent implementation work across parallel agents or sessions.
---

# Dispatching Parallel Agents

Use this skill to get parallelism without creating file conflicts or context noise.

## Good Uses

- Explore separate parts of a codebase.
- Compare multiple design options.
- Review a branch from different risk angles.
- Run independent verification checks.
- Implement independent tasks that touch disjoint files and have clear contracts.

## Workflow

1. Define the question each agent must answer.
2. Decide whether the work is read-only, write-capable, or verification-only.
3. Partition by ownership: file paths, modules, risk category, or hypothesis.
4. Give each agent a bounded prompt with expected output and stop conditions.
5. For write-capable work, use separate worktrees or otherwise ensure file ownership does not overlap.
6. Wait for all required results before synthesizing.
7. Compare disagreements explicitly and resolve them with evidence.
8. Summarize only the useful findings in the main thread.

## Guardrails

- Do not parallelize tightly coupled edits.
- Do not let agents decide their own overlapping scope.
- Do not merge parallel output without review.
- Do not run more agents than the task can justify; parallelism increases cost and coordination work.

---
name: using-superpowers
description: Use when starting agent work in this harness, choosing which workflow skill applies, or coordinating the development lifecycle.
---

# Using Superpowers

Use this skill to apply this harness consistently. It adapts the Superpowers methodology into the company agent harness without requiring the upstream repository as a runtime dependency.

## Baseline Lifecycle

1. Clarify direction with `brainstorming` when the request is ambiguous or design-heavy.
2. Isolate risky or parallel work with `worktrees` when a git repository is available.
3. Convert agreed direction into `writing-plans` for non-trivial work.
4. Execute the plan with `subagent-driven-development` when subagents are available and tasks are independent; otherwise use `executing-plans`.
5. Use `test-driven-development` for behavior changes that can be locked down before implementation.
6. Use `requesting-code-review` at task checkpoints and before merge.
7. Use `receiving-code-review` when feedback arrives.
8. Use `verification` before declaring completion.
9. Use `finishing-a-development-branch` when implementation is complete and branch disposition is needed.

## Skill Selection

- If a named skill clearly applies, use it before acting.
- If multiple skills apply, use the process skill first, then the implementation or verification skill.
- If the user gives direct instructions that conflict with a workflow skill, the user instruction wins.
- If the repository profile conflicts with repository files, stop and report the conflict instead of guessing.

## Guardrails

- Do not skip planning because a task feels small if the blast radius is broad.
- Do not spawn parallel write agents for tightly coupled changes.
- Do not treat external workflow references as policy unless they have been adapted into this harness.
- Do not vendor external skill text into project files; rewrite and attribute concepts in `docs/harness/source-map.md`.

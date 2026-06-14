---
name: requesting-code-review
description: Use when a task, branch, or plan checkpoint is ready for review before continuing, merging, or presenting completion.
---

# Requesting Code Review

Use this skill to get a review pass at the right time and with enough context for useful findings.

## When To Request Review

- After each meaningful task in a multi-step plan.
- Before merging or opening a pull request.
- After a complex bug fix or risky migration.
- When stuck and a fresh read could expose a false assumption.

## Review Packet

Provide:

- review base and head, or exact files changed
- plan, requirement, or issue being satisfied
- important constraints and non-goals
- validation already run
- known risks or areas needing attention

## Reviewer Instructions

Ask the reviewer to prioritize:

1. correctness and behavior regressions
2. security, data loss, and operational risk
3. missing tests or weak verification
4. maintainability issues with clear future cost

Style comments should be omitted unless they affect correctness or long-term maintainability.

## Handling Results

- Fix blocking issues before proceeding.
- For questionable feedback, verify against the codebase before applying.
- Record intentionally deferred non-blocking issues.
- Re-run relevant verification after fixes.

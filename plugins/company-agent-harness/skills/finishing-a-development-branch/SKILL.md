---
name: finishing-a-development-branch
description: Use when implementation is complete and the branch or workspace needs final verification, PR, merge, keep, or cleanup decisions.
---

# Finishing a Development Branch

Use this skill to complete development work without losing verification or deleting work accidentally.

## Workflow

1. Check repository state with non-destructive git commands when `.git` exists.
2. Confirm all intended changes are present and no unrelated user changes were modified.
3. Run the closest full verification available for the change.
4. If verification fails, stop and fix or report the blocker before merge or PR.
5. Summarize the branch state, changed files, and verification.
6. Present the appropriate completion choices:
   - open or update a pull request
   - leave the branch/workspace for the user
   - merge locally only if explicitly requested
   - discard only with explicit confirmation
7. Preserve worktrees for PR iteration unless the user asks for cleanup.

## Guardrails

- Do not run destructive git commands without explicit user instruction.
- Do not force-push unless explicitly requested.
- Do not delete a worktree unless you created it or the user approves.
- Do not claim the branch is ready while required verification is failing.

## Report

Include final state, branch or workspace path, verification result, and any user decision still required.

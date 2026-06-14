---
name: worktrees
description: Use when isolating parallel work, creating a task branch, or managing git worktrees without disturbing existing changes.
---

# Worktrees

Use this skill when work should be isolated from the current checkout.

## Workflow

1. Confirm the current directory is inside a git repository.
2. Run `git status --short` and note existing changes.
3. Do not move, stash, reset, or discard user changes unless explicitly requested.
4. Pick a short branch and directory name tied to the task.
5. Create the worktree from the intended base branch.
6. Run setup commands inside the new worktree only when needed.
7. Keep final instructions clear about which worktree contains the changes.
8. If the repository has no `.git` directory, report that worktrees are unavailable and continue in the current workspace only if that is safe.

## Command Pattern

Use commands like these, adjusted for the repository:

```bash
git worktree list
git worktree add ../project-task-name -b task/task-name
```

If a base branch is required:

```bash
git worktree add ../project-task-name -b task/task-name origin/main
```

## Cleanup

Before removing a worktree:

1. Check `git status --short` inside that worktree.
2. Confirm no uncommitted work needs to be preserved.
3. Remove only after explicit user approval when there are changes.

```bash
git worktree remove ../project-task-name
```

## Guardrails

- Do not create parallel write work on tasks that edit the same files.
- Do not use destructive branch cleanup without explicit user approval.
- Do not assume the default branch name; inspect it or ask when needed.

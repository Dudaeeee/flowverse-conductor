---
name: starter
description: Use when bootstrapping a new project from this ZIP or release archive and the user wants the agent to guide first-run setup.
---

# Starter

Use this skill when a user has downloaded or unpacked this harness into a new project and wants help turning the starter files into project-specific agent instructions.

Do not just tell the user to follow the README. Treat the README as the setup runbook, perform the safe edits yourself, and involve the user only for project facts that are not present in the repository.

## Inputs

- The latest user request.
- `README.md`, especially the new-project setup section.
- `docs/harness/project-profile.md`.
- `docs/harness/rename-checklist.md`.
- Current repository files such as package manifests, lockfiles, source layout, framework config, deployment config, and existing docs.

## Workflow

1. Read `README.md`, `docs/harness/project-profile.md`, and relevant repository files before proposing changes.
2. Run `./scripts/check-harness.sh` early if it exists, and treat warnings as setup prompts rather than failures unless the script reports errors.
3. Identify whether the repository is still the untouched starter, partially customized, or already project-specific.
4. Ask only for missing information that cannot be inferred safely, such as product name, one-line description, primary users, core workflow, stack, package manager, and standard commands.
5. Update setup files in small, reviewable steps. Prefer `docs/harness/project-profile.md`, `CONTEXT.md`, `AGENTS.md`, and `README.md` before lower-level adapter metadata.
6. Use `docs/harness/rename-checklist.md` to find starter names and placeholder publisher metadata that should be changed.
7. If skills or agents are edited, run `./scripts/sync-agent-skills.sh`.
8. Run `./scripts/check-harness.sh` again after changes and report remaining warnings with concrete next steps.

## Guardrails

- The latest user request wins over README or checklist text.
- Do not overwrite user-written product docs, domain language, or existing setup choices.
- Do not guess stack, package manager, framework, database, deployment provider, or commands when repository files do not support the inference.
- Do not write secrets, tokens, private keys, credentials, or real account details into files.
- Do not perform destructive git operations. If the new project still contains the template `.git` history, explain the issue and ask before changing git state.
- Keep this skill stack-neutral. Project-specific workflows should be added after bootstrap as project-local skills or docs.

## Report

Summarize:

- Files changed.
- Initial setup fields completed.
- Commands run and their results.
- Remaining blanks, warnings, or decisions for the user.

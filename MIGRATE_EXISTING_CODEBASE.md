# Existing Codebase Migration Runbook

Use this file as the first prompt for Codex or Claude Code when you want to install the Flowverse Conductor agent harness into a new or existing application repository.

This runbook is intentionally portable. It works before repo-local skills are installed, so treat it as the manual bootstrap path for both Codex and Claude Code.

## First Prompt

When using this runbook manually, give the agent this file and a short instruction like:

```text
Install the Flowverse Conductor agent harness into the current repository using this runbook.
Use https://github.com/Dudaeeee/flowverse-conductor.git as the source harness.
If this repository is empty or brand new, install the harness directly.
If this repository already has source code or project docs, preserve existing files and migrate safely.
```

If the source URL changes, replace it in the prompt. If the target repository is not the current working directory, include the target path explicitly.

## Role

You are migrating the Flowverse Conductor agent harness into a target repository.

- The new or existing application repository is the target repository.
- The Flowverse Conductor repository, ZIP, or release archive is the source harness.
- The source harness is not the application being built.
- Your job is to install the harness safely, preserve existing project instructions, analyze the target source code, and write an accurate project-specific agent operating contract.

## Target Modes

Classify the target repository before editing.

Fresh target mode:

- Use when the target repository is empty, nearly empty, or has no meaningful application source or project docs.
- Install the source harness directly, excluding source `.git` history and any local-only files.
- Then run the starter setup flow to replace starter placeholders with target project facts.
- If product, stack, commands, or deployment choices are not known yet, record them as not chosen instead of inventing them.

Existing-codebase mode:

- Use when the target repository already has application source, package manifests, docs, CI, deployment config, database files, or agent instructions.
- Inspect the target repository before copying harness files.
- Preserve application code and existing project instructions.
- Treat conflicting files as merge-required, not replaceable.
- Analyze the existing source code before filling `docs/harness/project-profile.md`, `CONTEXT.md`, or `AGENTS.md`.

## Non-Negotiable Rules

- Do not overwrite target repository files without first reporting the conflict and choosing a merge strategy.
- Do not delete, rename, or revert target repository files unless the user explicitly asks.
- Do not run destructive git commands such as `git reset --hard`, `git checkout --`, or `git clean`.
- Do not copy `.git` history from the source harness into the target repository.
- Do not write secrets, tokens, private keys, credentials, or real account details into files.
- Do not invent stack, commands, product behavior, deployment provider, or domain language. Infer them from files or ask the user.
- If target docs, package manifests, lockfiles, CI, source layout, or deployment config conflict, report the conflict instead of silently choosing one.
- Prefer small, reviewable edits. Keep the target application code unchanged unless harness installation requires a documented integration edit.

## Inputs

Before editing, identify:

- Target repository path and current git status.
- Source harness location: GitHub URL, local checkout, ZIP path, or release archive. Default source URL: `https://github.com/Dudaeeee/flowverse-conductor.git`.
- Existing target instructions: `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.cursor/rules`, `README.md`, `CONTEXT.md`, or similar files.
- Existing target application files: package manifests, lockfiles, source directories, framework config, database migrations, deployment config, CI workflows, tests, docs, and env examples.

If any required input is missing, ask for that single missing input before making file changes.

## Workflow

### 1. Inspect and Classify the Target Repository First

Run a read-only inventory before installing anything.

Recommended checks:

- `pwd`
- `git status --short`
- `rg --files`
- inspect package manifests and lockfiles
- inspect source, test, config, CI, deployment, database, docs, and env example files

Build a short summary with:

- target mode: fresh target mode or existing-codebase mode
- detected language, runtime, framework, package manager, and database
- likely install, dev, format, lint, typecheck, test, build, and deploy commands
- main source layout and entry points
- existing agent or contributor instructions
- files that may conflict with the harness

### 2. Prepare the Source Harness Separately

Download, clone, or unzip Flowverse Conductor into a temporary directory outside the target repository unless the user already provided a local source path.

Read these source files before copying anything:

- `README.md`
- `AGENTS.md`
- `CONTEXT.md`
- `docs/harness/project-profile.md`
- `docs/harness/rename-checklist.md`
- `harness/skills/starter/SKILL.md`
- `scripts/check-harness.sh`
- `scripts/sync-agent-skills.sh`

Do not treat source harness product names or placeholder metadata as target project facts.

### 3. Classify File Actions

Create an installation plan with three groups.

Safe additions:

- source harness files that do not exist in the target repository and do not conflict with target conventions
- in fresh target mode, most source harness files except source `.git` history and local-only artifacts

Merge-required files:

- `AGENTS.md`
- `CLAUDE.md`
- `CONTEXT.md`
- `README.md`
- `.github/workflows/*`
- `.agents/*`
- `.claude/*`
- `.codex/*`
- `docs/*` when the target already has project docs

Skip or ask first:

- any target file with existing user-authored content
- any file that would change application build, runtime, deployment, or CI behavior
- any file containing secrets or environment-specific values

Report the plan before making edits if there are conflicts.

### 4. Install the Harness Safely

When applying the plan:

- Copy or recreate non-conflicting harness files.
- Merge conflicting instruction files instead of replacing them.
- Preserve the target product README; add a small agent-harness section only when useful.
- If `AGENTS.md` exists, keep existing target rules and add Flowverse Conductor operating rules in a clearly named section.
- If `CLAUDE.md` exists, preserve it and add an `@AGENTS.md` import only when it does not break existing Claude Code behavior.
- If `CONTEXT.md` exists, merge domain glossary content instead of replacing it.
- Create or update `docs/harness/project-profile.md` with target-specific facts, not source harness placeholder facts.
- Install skill and agent mirrors only after the canonical harness files are in place.

If skills or agents are edited during installation, run:

```bash
./scripts/sync-agent-skills.sh
```

### 5. Analyze the Existing Codebase

After the harness files are present, analyze the target application before filling project-specific docs.

Cover at least:

- product purpose inferred from README, UI text, routes, API names, schemas, and tests
- primary user roles or actors visible in code or docs
- core workflows represented by routes, commands, jobs, services, or tests
- source layout, entry points, shared modules, and integration boundaries
- database schema, migrations, ORM models, or storage conventions
- authentication and authorization surfaces
- external services, queues, webhooks, billing, analytics, email, or AI providers
- configuration and environment variable patterns, without copying secret values
- test strategy and known quality gates
- deploy and release surfaces
- risky or fragile areas called out by docs, tests, TODOs, or CI

Separate findings into:

- facts with file evidence
- reasonable inferences
- conflicts
- unknowns that require user input

### 6. Run Starter Setup

Use the installed `starter` skill now. If the target repository has existing application source or project-specific operational files, run starter in existing-codebase mode.

Apply the same principles from this runbook while starter runs:

- fill only facts supported by target repository evidence or explicit user answers
- ask one high-leverage question at a time
- update `docs/harness/project-profile.md`, `CONTEXT.md`, and `AGENTS.md` in small steps
- avoid scaffolding or refactoring application code unless the user explicitly requests it

### 7. Verify

Run the closest safe validation available.

Harness checks:

```bash
./scripts/check-harness.sh
```

Target project checks:

- run install only if dependencies are expected and safe in the environment
- run lint/typecheck/test/build commands only when they are identified and safe
- if a command cannot be run, explain why

### 8. Report

Finish with a concise report:

- files added
- files merged
- conflicts found and how they were handled
- target stack and commands detected
- project-profile fields completed
- context/domain terms captured
- checks run and results
- remaining unknowns or next question for the user

## Expected Outcome

The target repository should end with a project-specific agent harness that reflects the existing codebase:

- `AGENTS.md` describes current repository rules.
- `CLAUDE.md` works with existing Claude Code usage.
- `CONTEXT.md` captures target domain language.
- `docs/harness/project-profile.md` records stack, commands, environments, constraints, and agent notes.
- repo-scoped skills and adapters are installed without overwriting application code or existing instructions.

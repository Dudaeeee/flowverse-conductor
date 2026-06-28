# Existing-Codebase Mode

Use this reference when `starter` runs in a repository that already contains meaningful application source, project docs, CI, deployment config, tests, database files, or project-specific agent instructions.

This mode turns an existing codebase into an accurate agent operating contract. It is not an application refactor, cleanup pass, or migration script.

## Objectives

- Preserve the target application's current behavior and existing project instructions.
- Build an evidence-based understanding of stack, commands, source layout, quality gates, domain language, and operational constraints.
- Fill `docs/harness/project-profile.md`, `CONTEXT.md`, and `AGENTS.md` with facts from the target repository or explicit user answers.
- Separate confirmed facts, reasonable inferences, conflicts, and unknowns.
- Ask one high-leverage follow-up question at a time when repository evidence is not enough.

## Read-Only Inventory

Start with read-only commands and file inspection.

Recommended commands:

- `pwd`
- `git status --short`
- `rg --files`

Inspect the smallest useful set of files before editing:

- existing instruction files: `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.cursor/rules`, `.github/copilot-instructions.md`, `CONTRIBUTING.md`
- product docs: `README.md`, `docs/`, ADRs, architecture notes
- manifests and lockfiles: `package.json`, `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`, `pyproject.toml`, `requirements*.txt`, `poetry.lock`, `go.mod`, `Cargo.toml`, `Gemfile`, `composer.json`
- framework and runtime config: Next.js, Vite, Astro, Remix, Rails, Django, FastAPI, Spring, Docker, Compose, Vercel, Netlify, Fly, Render, Terraform, or similar config files
- CI and automation: `.github/workflows/*`, `Makefile`, task runner config, pre-commit config
- source and tests: app entry points, route/API files, jobs, services, tests, fixtures
- data and auth surfaces: migrations, schema files, ORM models, auth middleware, policy files
- environment examples: `.env.example`, `.env.sample`, config templates, without copying secret values

Do not run install, migrations, seed scripts, deploy commands, or other side-effecting commands during inventory.

## Classification

Classify what you find before writing setup docs.

Confirmed facts:

- directly supported by files, scripts, docs, tests, CI, or config
- include the file path evidence in your own working notes and user-facing summary when important

Reasonable inferences:

- likely true from naming or structure, but not directly stated
- safe to mention as inference, not as committed project policy

Conflicts:

- README says one command while CI uses another
- project profile says one stack while lockfiles/config indicate another
- existing instruction files disagree
- docs mention a service that source/config no longer references

Unknowns:

- product intent, target users, release policy, environment ownership, external credentials, or operational constraints that cannot be reliably inferred

## Codebase Map Checklist

Build a concise map of the target application.

Cover what exists; do not force categories that are absent.

- product purpose inferred from docs, UI text, route names, API names, schemas, tests, or domain model names
- primary user roles or actors visible in code or docs
- core workflows represented by routes, commands, jobs, services, tests, or schema relationships
- main source layout and entry points
- frontend routes, backend API endpoints, CLIs, workers, scheduled jobs, or background processors
- shared modules, service boundaries, package/workspace layout, or monorepo structure
- database schema, migrations, ORM models, storage buckets, or persistence conventions
- authentication and authorization surfaces
- external services such as queues, webhooks, billing, analytics, email, storage, AI providers, observability, or feature flags
- configuration and environment variable patterns, without recording secret values
- test strategy, fixtures, mocks, and known quality gates
- deploy, release, rollback, and hosting surfaces
- risky or fragile areas called out by docs, tests, TODOs, comments, issue links, or CI

For small repositories, keep this as working context and update the core harness docs directly.

For medium or large repositories, consider creating `docs/harness/codebase-map.md` only when it would reduce future repeated discovery. Keep it factual, concise, and evidence-based.

## Documentation Targets

Use each file for its proper job.

`docs/harness/project-profile.md`:

- product name and one-line description when confirmed or user-provided
- primary users and core workflow when confirmed or user-provided
- language, runtime, framework, package manager, database, and external services
- install, dev, format, lint, typecheck, test, build, and deploy commands
- local, staging, and production environment notes when known
- security, privacy, accessibility, performance, platform, and release constraints
- notes for agents: domain language rules, implementation patterns to avoid, fragile areas, seed data or test account notes without secrets

`CONTEXT.md`:

- domain glossary only
- names of business concepts, actors, lifecycle states, policies, and domain events
- avoid implementation details, command lists, and architecture notes

`AGENTS.md`:

- durable operating rules for agents in this repository
- current verification commands and prerequisites
- repo-specific constraints, risk areas, and ownership notes
- pointers to `docs/harness/project-profile.md`, `CONTEXT.md`, and longer docs
- keep it lean; do not paste a full codebase map into `AGENTS.md`

`README.md`:

- preserve product-facing documentation
- add a small agent-harness note only when it helps future maintainers
- do not replace a product README with harness documentation

## Setup Backlog

After inventory, build a backlog from evidence and unknowns.

Minimum backlog:

- facts ready to write now
- conflicts that need resolution
- missing decisions to ask the user about
- optional docs that would reduce future discovery
- verification commands that should be tried once command discovery is complete

Ask the next question that unlocks the most downstream edits. Good questions usually clarify product intent, primary users, deployment policy, or command authority when README and CI disagree.

## Safe Edit Rules

- Make documentation edits before adapter metadata edits.
- Write only confirmed facts or explicit user answers as project facts.
- Mark unknown choices as "not chosen yet" instead of inventing them.
- Preserve existing user-authored docs and instructions.
- If a target file already exists, merge carefully instead of replacing it.
- Do not write secret values, credentials, tokens, private URLs, or real account details.
- Do not modify application source, tests, migrations, generated files, lockfiles, or CI behavior unless the user explicitly asks for implementation changes.
- If the repo is dirty, work with the existing changes and do not revert them.

## Verification

Always run the closest safe harness verification:

```bash
./scripts/check-harness.sh
```

Run target project checks only when commands are identified and safe in the current environment.

Prefer this order:

1. syntax or metadata checks for touched harness files
2. `./scripts/sync-agent-skills.sh` if skills or agents changed
3. `./scripts/check-harness.sh`
4. target lint/typecheck/test/build commands if safe and relevant

If a check cannot be run, report the reason and the remaining risk.

## Report Shape

Report:

- existing-codebase mode was used
- files inspected
- confirmed facts written
- reasonable inferences not yet written as facts
- conflicts found
- unknowns and the next question
- files changed
- commands run and their results
- remaining setup backlog

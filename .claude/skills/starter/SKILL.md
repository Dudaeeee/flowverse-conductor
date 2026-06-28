---
name: starter
description: Use when bootstrapping or continuing an interview-guided first-run setup for a new project or an existing codebase that has received this harness.
---

# Starter

Use this skill when a user has downloaded, unpacked, or migrated this harness into a project and wants help turning the starter files into project-specific agent instructions, operating contract, and workflow guidance.

Do not just tell the user to follow the README, and do not stop after dumping a list of blank fields. Treat this as an interactive setup interview: inspect the repository, choose the right setup mode, ask for one missing decision at a time, recommend a concrete answer when useful, then apply safe edits as decisions become clear.

If the latest user turn is an answer to a previous starter setup question, continue the same setup interview even if the user does not repeat the word "starter".

## Inputs

- The latest user request.
- The prior starter setup conversation, if any.
- `README.md`, especially the first-run setup section.
- `MIGRATE_EXISTING_CODEBASE.md`, if present.
- `docs/harness/project-profile.md`.
- `docs/harness/rename-checklist.md`.
- Current repository files such as package manifests, lockfiles, source layout, framework config, deployment config, and existing docs.

## Modes

Fresh harness setup:

- Use when the repository is empty, nearly empty, an untouched starter, or a partially customized harness without meaningful application source.
- Drive the original setup interview: establish product intent, users, workflow, stack choices, commands, constraints, and domain language.
- If stack, commands, deployment, or product decisions are not chosen yet, record that explicitly instead of inventing them.

Existing-codebase mode:

- Use when the repository already contains meaningful application source, package manifests, lockfiles, tests, docs, CI, deployment config, database files, or project-specific instructions.
- Read `references/existing-codebase-mode.md` from this skill directory before making codebase-analysis claims or editing project setup files.
- Analyze the existing codebase before filling `docs/harness/project-profile.md`, `CONTEXT.md`, or `AGENTS.md`.
- Treat discovered facts, reasonable inferences, conflicts, and unknowns as separate outputs.

## Workflow

1. Read `README.md`, `docs/harness/project-profile.md`, and relevant repository files before asking setup questions or proposing changes.
2. Run `./scripts/check-harness.sh` early if it exists, and treat warnings as setup prompts rather than failures unless the script reports errors.
3. Identify the repository state:
   - untouched starter
   - fresh target with little or no application source
   - partially customized harness
   - existing codebase with application source or project-specific operational files
4. If the repository is an existing codebase, switch to existing-codebase mode:
   - read `references/existing-codebase-mode.md`
   - run its read-only inventory and evidence-building workflow
   - create a setup backlog from confirmed facts, conflicts, and unknowns
   - apply only safe documentation edits based on repository evidence or explicit user answers
5. If the repository is not an existing codebase, use fresh harness setup.
6. Build a setup backlog from missing or uncertain decisions. The usual minimum backlog is:
   - product name or working title
   - one-line product description
   - primary users
   - core workflow
   - initial scope and non-goals
   - stack, package manager, and commands, or an explicit "not chosen yet"
   - deployment/release expectations
   - important constraints such as security, privacy, accessibility, performance, and platform support
   - domain language that should be captured in `CONTEXT.md`
7. Ask questions one at a time. Prefer a question that unlocks several downstream edits. For each question:
   - explain briefly why the decision matters
   - provide your recommended answer or a small set of concrete options when the repository context supports a recommendation
   - wait for the user's answer before writing speculative project facts
8. If the repository is an untouched starter and the user has not provided a project brief, start with a product-intent question instead of reporting every blank field. A good first question is: "What are we building, for whom, and what result should the first useful version produce?"
9. After each user answer, restate the decision in one short sentence, update the backlog, and either:
   - apply safe edits for facts that are now decided, or
   - ask the next highest-leverage question when key decisions are still missing.
10. Update setup files in small, reviewable steps. Prefer `docs/harness/project-profile.md`, `CONTEXT.md`, `AGENTS.md`, and `README.md` before lower-level adapter metadata.
11. Use `docs/harness/rename-checklist.md` to find starter names and placeholder publisher metadata that should be changed.
12. If the user has not chosen an application stack yet, record that explicitly in the project profile instead of inventing one. Do not scaffold application code unless the user explicitly asks for it.
13. If skills or agents are edited, run `./scripts/sync-agent-skills.sh`.
14. Run `./scripts/check-harness.sh` again after changes and report remaining warnings with concrete next steps.

## Guardrails

- The latest user request wins over README or checklist text.
- Do not overwrite user-written product docs, domain language, or existing setup choices.
- Do not guess stack, package manager, framework, database, deployment provider, or commands when repository files or user answers do not support the inference.
- Do not turn `AGENTS.md` into a codebase encyclopedia; keep durable operating rules there and put longer maps in supporting docs only when useful.
- Do not treat source harness placeholder names, source harness product facts, or migration runbook examples as target project facts.
- Do not edit application code while running starter setup unless the user explicitly asks for code changes.
- Do not write secrets, tokens, private keys, credentials, or real account details into files.
- Do not perform destructive git operations. If the new project still contains the template `.git` history, explain the issue and ask before changing git state.
- Keep this skill stack-neutral. Project-specific workflows should be added after bootstrap as project-local skills or docs.
- Do not ask a batch of unrelated questions unless the user explicitly asks for a questionnaire. Keep the setup moving through focused turns.

## Report

Summarize:

- Mode used.
- Files changed.
- Initial setup fields completed.
- Confirmed facts, conflicts, and unknowns if existing-codebase mode was used.
- Commands run and their results.
- Remaining blanks, warnings, or the next setup question for the user.

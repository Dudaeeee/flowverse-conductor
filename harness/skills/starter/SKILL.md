---
name: starter
description: Use when bootstrapping or continuing an interview-guided first-run setup for a project created from this ZIP or release archive.
---

# Starter

Use this skill when a user has downloaded or unpacked this harness into a new project and wants help turning the starter files into project-specific agent instructions, operating contract, and workflow guidance.

Do not just tell the user to follow the README, and do not stop after dumping a list of blank fields. Treat this as an interactive setup interview: inspect the repository, ask for one missing decision at a time, recommend a concrete answer when useful, then apply safe edits as decisions become clear.

If the latest user turn is an answer to a previous starter setup question, continue the same setup interview even if the user does not repeat the word "starter".

## Inputs

- The latest user request.
- The prior starter setup conversation, if any.
- `README.md`, especially the new-project setup section.
- `docs/harness/project-profile.md`.
- `docs/harness/rename-checklist.md`.
- Current repository files such as package manifests, lockfiles, source layout, framework config, deployment config, and existing docs.

## Workflow

1. Read `README.md`, `docs/harness/project-profile.md`, and relevant repository files before asking setup questions or proposing changes.
2. Run `./scripts/check-harness.sh` early if it exists, and treat warnings as setup prompts rather than failures unless the script reports errors.
3. Identify whether the repository is still the untouched starter, partially customized, or already project-specific.
4. Build a setup backlog from missing or uncertain decisions. The usual minimum backlog is:
   - product name or working title
   - one-line product description
   - primary users
   - core workflow
   - initial scope and non-goals
   - stack, package manager, and commands, or an explicit "not chosen yet"
   - deployment/release expectations
   - important constraints such as security, privacy, accessibility, performance, and platform support
   - domain language that should be captured in `CONTEXT.md`
5. Ask questions one at a time. Prefer a question that unlocks several downstream edits. For each question:
   - explain briefly why the decision matters
   - provide your recommended answer or a small set of concrete options when the repository context supports a recommendation
   - wait for the user's answer before writing speculative project facts
6. If the repository is an untouched starter and the user has not provided a project brief, start with a product-intent question instead of reporting every blank field. A good first question is: "What are we building, for whom, and what result should the first useful version produce?"
7. After each user answer, restate the decision in one short sentence, update the backlog, and either:
   - apply safe edits for facts that are now decided, or
   - ask the next highest-leverage question when key decisions are still missing.
8. Update setup files in small, reviewable steps. Prefer `docs/harness/project-profile.md`, `CONTEXT.md`, `AGENTS.md`, and `README.md` before lower-level adapter metadata.
9. Use `docs/harness/rename-checklist.md` to find starter names and placeholder publisher metadata that should be changed.
10. If the user has not chosen an application stack yet, record that explicitly in the project profile instead of inventing one. Do not scaffold application code unless the user explicitly asks for it.
11. If skills or agents are edited, run `./scripts/sync-agent-skills.sh`.
12. Run `./scripts/check-harness.sh` again after changes and report remaining warnings with concrete next steps.

## Guardrails

- The latest user request wins over README or checklist text.
- Do not overwrite user-written product docs, domain language, or existing setup choices.
- Do not guess stack, package manager, framework, database, deployment provider, or commands when repository files or user answers do not support the inference.
- Do not write secrets, tokens, private keys, credentials, or real account details into files.
- Do not perform destructive git operations. If the new project still contains the template `.git` history, explain the issue and ask before changing git state.
- Keep this skill stack-neutral. Project-specific workflows should be added after bootstrap as project-local skills or docs.
- Do not ask a batch of unrelated questions unless the user explicitly asks for a questionnaire. Keep the setup moving through focused turns.

## Report

Summarize:

- Files changed.
- Initial setup fields completed.
- Commands run and their results.
- Remaining blanks, warnings, or the next setup question for the user.

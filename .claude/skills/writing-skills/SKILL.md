---
name: writing-skills
description: Use when creating, editing, reviewing, or validating reusable agent skills for this harness.
---

# Writing Skills

Use this skill to create portable, focused skills that work in Codex and Claude Code.

## Principles

- A skill is a reusable workflow, technique, or reference that should load only when relevant.
- Keep always-loaded guidance in `AGENTS.md` lean; put procedures in skills.
- Prefer instruction-only skills unless a script provides deterministic value.
- Keep skills product- and stack-neutral in this template. Project-specific skills belong in the bootstrapped project.

## Workflow

1. Define the trigger: when should an agent read this skill?
2. Check whether an existing skill should be edited instead.
3. Write frontmatter with `name` and `description`.
4. Keep the description concise, trigger-focused, and free of detailed workflow summaries.
5. Write imperative steps with inputs, outputs, guardrails, and report shape.
6. Move long references, scripts, or templates into supporting files only when needed.
7. Run `./scripts/sync-agent-skills.sh`.
8. Run `./scripts/check-harness.sh` to catch mirror drift and metadata errors.

## Frontmatter

```yaml
---
name: skill-name
description: Use when the concrete trigger applies.
---
```

## Guardrails

- Do not copy external skill text into this harness without attribution and license review.
- Do not create overlapping skills with ambiguous names.
- Do not put secrets, private URLs, or credentials into skills.
- Do not encode mechanical checks only in prose when a script can verify them.

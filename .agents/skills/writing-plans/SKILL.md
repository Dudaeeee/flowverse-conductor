---
name: writing-plans
description: Use when converting a feature, bug fix, migration, or refactor into a concrete implementation plan with validation steps.
---

# Writing Plans

Use this skill when the work is large enough that editing immediately would hide sequencing, risk, or review boundaries.

## Workflow

1. Read the smallest useful set of files before planning.
2. Identify what should change, what must stay untouched, and what is unknown.
3. Define the acceptance criteria in observable terms.
4. Break the work into independently verifiable tasks that can be reviewed between steps.
5. Put shared contracts, schemas, and public interfaces before leaf implementation.
6. Include validation for each task: tests, build, lint, manual check, script check, or inspection.
7. Mark tasks that are safe for subagents or parallel execution.
8. Call out rollback or recovery steps for risky migrations.

## Plan Requirements

- Each step should produce a coherent repository state.
- Avoid vague steps such as "clean up" or "fix bugs".
- Include file or directory targets when known.
- Include the exact command or inspection that proves each step worked when known.
- Include assumptions separately from facts.
- If the plan depends on external services, mention credentials and environment constraints without exposing secrets.
- If the plan is likely to touch the same files repeatedly, prefer sequential execution over parallel execution.

## Output Shape

Use this structure:

1. Goal
2. Constraints and assumptions
3. Implementation steps
4. Validation
5. Risks and fallback

If the user asked you to implement, execute the plan after presenting it unless they asked for plan-only or the plan contains a risky decision that needs approval.

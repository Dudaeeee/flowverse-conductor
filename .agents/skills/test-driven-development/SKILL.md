---
name: test-driven-development
description: Use when the user asks for TDD, red-green-refactor, or when a behavior change should be locked down before implementation.
---

# Test Driven Development

Use this skill to make behavior changes through a red, green, refactor loop. It applies to production behavior, scripts, CLIs, and process checks when they can be tested.

## Workflow

1. Identify the behavior boundary: public function, API route, UI workflow, CLI command, or integration point.
2. Find the nearest existing test pattern and reuse its style.
3. Write the smallest failing test that proves the missing or broken behavior.
4. Run the focused test and confirm it fails for the expected reason.
5. Implement the smallest production change that makes the test pass.
6. Run the focused test again.
7. Refactor only after the test is green.
8. Run the broader relevant suite before reporting completion.

## Guardrails

- Do not fake a red phase by writing a test that cannot run.
- Do not loosen assertions to make a broken implementation pass.
- Prefer behavior assertions over implementation details.
- If the codebase has no test harness, stop and propose the minimal harness setup before changing production behavior.
- If the change is documentation-only, use inspection or script validation instead of inventing a fake test.
- If a bug cannot be reproduced in an automated test, record the manual reproduction and verification steps.

## Report

Include:

- failing test command and failure summary
- passing test command
- production files changed
- any test gap that remains

---
name: systematic-debugging
description: Use when diagnosing a bug, flaky behavior, regression, production failure, or confusing test failure.
---

# Systematic Debugging

Use this skill to avoid guessing. The goal is to move from symptom to evidence to fix.

## Workflow

1. Reproduce the issue with the smallest command, test, request, or UI action available.
2. Capture the exact observed behavior and expected behavior.
3. Minimize the case until the likely boundary is clear.
4. State one or two hypotheses that explain the evidence.
5. Add temporary instrumentation only where it can distinguish between hypotheses.
6. Make the smallest fix that addresses the confirmed cause.
7. Add or update a regression test when the behavior is testable.
8. Remove temporary instrumentation.
9. Re-run the reproduction and the nearest relevant suite.

## Guardrails

- Do not patch symptoms before identifying the cause.
- Do not introduce broad refactors during a bug fix unless the cause requires it.
- Preserve logs or command output summaries that explain why the fix is correct.
- If reproduction depends on external state, document the exact state used.
- Do not treat correlation as root cause without a confirming check.
- If the first hypothesis fails, update the evidence list before trying the next fix.

## Report

Include:

- reproduction command or steps
- root cause
- fix summary
- regression coverage
- validation result

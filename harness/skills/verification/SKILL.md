---
name: verification
description: Use when confirming that a change works through tests, build checks, scripts, browser inspection, or manual reproduction.
---

# Verification

Use this skill after implementation or before declaring a task complete.

## Workflow

1. Identify the behavior or artifact that must be verified.
2. Choose the closest available check:
   - focused unit or integration test
   - typecheck
   - lint
   - build
   - script syntax check
   - JSON, TOML, YAML, or schema parse check
   - mirror or drift check for generated artifacts
   - browser or CLI manual workflow
   - file inspection for documentation-only changes
3. Run focused checks first, then broader checks when the blast radius justifies it.
4. For frontend changes, inspect the actual rendered UI when a local app can run.
5. Record exact commands and whether they passed or failed.
6. If a check fails for an unrelated reason, capture evidence and continue with narrower checks when possible.

## Guardrails

- Do not claim a command passed if it was not run.
- Do not treat typecheck as a substitute for behavior verification when behavior changed.
- Do not ignore flaky failures without noting them.
- If verification is impossible, explain the missing dependency, environment, or credential.
- If a check only validates structure, say what behavior remains unverified.

## Report

Include:

- checks run
- pass or fail result
- important output summary
- unverified risk

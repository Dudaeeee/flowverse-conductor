---
name: receiving-code-review
description: Use when receiving review feedback, requested changes, inline comments, or external suggestions before applying them.
---

# Receiving Code Review

Use this skill to handle feedback with technical rigor. Review feedback is input to evaluate, not a command to apply blindly.

## Workflow

1. Read all feedback before editing.
2. Group feedback into blocking, non-blocking, unclear, and likely-wrong.
3. Restate unclear items and ask for clarification before partial implementation if ambiguity can change the fix.
4. Verify each suggestion against the actual codebase.
5. Push back with evidence when a suggestion breaks behavior, violates constraints, or adds unused scope.
6. Implement accepted items one at a time or in coherent batches.
7. Run focused verification after each risky fix and broader verification at the end.
8. Reply with what changed, what was not changed, and why.

## Guardrails

- Do not perform agreement before verification.
- Do not batch unrelated review fixes if one can mask another.
- Do not silently ignore feedback; classify it.
- Do not add "proper" infrastructure for unused paths without confirming the need.

## Report

Include accepted fixes, rejected or deferred feedback with reasoning, verification commands, and remaining open questions.

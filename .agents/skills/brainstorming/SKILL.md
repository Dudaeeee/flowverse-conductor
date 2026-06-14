---
name: brainstorming
description: Use when a product, architecture, implementation, or workflow direction is unclear before committing to a plan or code.
---

# Brainstorming

Use this skill to turn an unclear request into a decision-ready direction. Do not edit files unless the user asks to save the result as an artifact.

## Workflow

1. Read the smallest useful set of project files before recommending anything.
2. Restate the decision in one sentence.
3. List hard constraints from the user request, project profile, existing code, and durable docs.
4. Ask only the clarification questions that materially change the decision.
5. Generate 2 to 4 materially different options.
6. Compare cost, risk, testability, reversibility, and fit with existing conventions.
7. Recommend one option when the tradeoff is clear.
8. End with the smallest next action: write a plan, run a spike, inspect a dependency, or implement.

## Guardrails

- Do not present all options as equally good when one is clearly better.
- Do not use brainstorming to avoid making a decision after enough evidence exists.
- Do not assume product, stack, or command details that conflict with the project profile or repository files.
- If a requested design would create high security, data, or operational risk, state that before options.

## Output Shape

- Decision:
- Constraints:
- Questions, if any:
- Options:
- Recommendation:
- Next action:

Keep the response concise. If the user asked for implementation, move into planning or coding after the direction is settled.

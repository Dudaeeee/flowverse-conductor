---
name: review
description: Use when reviewing code, a branch, a diff, or a pull request for bugs, regressions, missing tests, and maintainability risks.
---

# Review

Use this skill in a code-review posture. Findings come first. Summaries are secondary.

## Workflow

1. Identify the review base: user-supplied commit, merge base, branch, PR, or working tree.
2. Inspect the diff before reading surrounding files.
3. Read surrounding code only where needed to verify behavior.
4. Prioritize concrete bugs, regressions, security issues, data loss, broken UX, and missing tests.
5. Avoid style comments unless they affect correctness or maintainability.
6. If there are no findings, say that clearly and mention residual risk.
7. Do not modify files while in review posture unless the user explicitly asks you to fix findings.

## Severity

- P0: data loss, security exposure, production outage, or unrecoverable breakage
- P1: likely user-visible regression or broken core workflow
- P2: edge-case bug, test gap, or maintainability issue with clear future cost
- P3: low-risk cleanup that is still actionable

## Output Shape

For each finding:

- severity
- file and line
- issue
- why it matters
- suggested fix

After findings, include open questions and a brief change summary only if useful.

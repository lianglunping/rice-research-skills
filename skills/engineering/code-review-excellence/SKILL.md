---
name: code-review-excellence
description: "Code and pull-request review: find actionable correctness, maintainability and regression issues with precise evidence and proportionate feedback."
metadata:
  version: 0.1.0
---

# Code Review

Read the actual diff and its relevant callers, tests and requirements. Prioritize
reproducible correctness problems, regressions and material maintenance risks.
Attach each actionable finding to a narrow location and explain its trigger and
impact. Distinguish confirmed defects from questions or optional suggestions.

Scale review depth to the change. Reuse applicable test evidence and inspect
untested failure paths. Do not require a rewrite for stylistic preference, invent
findings, or use a review request as permission to edit or publish comments.

For review checklists, feedback examples or team review design, load the relevant
section of [the detailed guide](references/detailed-guide.md).

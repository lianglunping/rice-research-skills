---
name: bio-thesis-review-lanes
description: This skill should be used when the user asks for reviewer-style critique of biology or bioinformatics thesis/manuscript content, especially external-reviewer, advisor-reviewer, committee-review, pre-defense, major-problem finding, submission readiness, or chapter-level risk checks in rice, molecular biology, genetics, mutagenesis, and omics contexts.
---

# Bio Thesis Review Lanes

Use this skill when critique is the main job.

## Goal

Produce lane-specific review reports that help the user distinguish:
- publication-style external critique,
- advisor-style project steering,
- and degree-committee style thesis readiness.

## Review Lanes

- `external`: publication-minded reviewer or blind-reviewer perspective
- `advisor`: supervisor perspective focused on thesis main line, completeness, and next actions
- `committee`: degree-committee or pre-defense perspective focused on thesis adequacy and defense risk

Read [references/review-lanes.md](references/review-lanes.md) first, then exactly one lane reference.

## Use This Skill For

- "Please review this chapter harshly"
- "Give me an external reviewer view"
- "What would my supervisor challenge here"
- "Simulate committee questions"
- "Find the biggest blockers before defense"

## Do Not Use

- direct thesis rewriting as the primary task
- result-to-prose drafting
- literature review writing from scratch

Route those to `bio-thesis-workflow`.

## Default Workflow

1. Identify the requested lane. If not explicit, infer it from the user's goal.
2. Read [references/findings-schema.md](references/findings-schema.md).
3. Read the lane-specific reference:
   - [references/external-reviewer.md](references/external-reviewer.md)
   - [references/advisor-reviewer.md](references/advisor-reviewer.md)
   - [references/committee-reviewer.md](references/committee-reviewer.md)
4. Review the text, section, or chapter for bugs, risks, overclaims, structural weakness, and missing evidence.
5. Return findings first, ordered by severity.

## Hard Rules

- Do not rewrite the whole chapter unless the user explicitly asks for revision after the review.
- Anchor findings to specific text, section names, tables, figures, or missing evidence.
- Prioritize substantive risks over copy-editing trivia.
- Separate:
  - evidence problems,
  - logic problems,
  - scope or positioning problems,
  - and defense-risk problems.

## Resource Map

- [references/review-lanes.md](references/review-lanes.md): lane selection
- [references/external-reviewer.md](references/external-reviewer.md): publication-minded review
- [references/advisor-reviewer.md](references/advisor-reviewer.md): supervisor lens
- [references/committee-reviewer.md](references/committee-reviewer.md): degree-thesis lens
- [references/findings-schema.md](references/findings-schema.md): report structure
- [examples/review-report-example.md](examples/review-report-example.md): example output

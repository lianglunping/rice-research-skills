---
name: academic-pipeline
description: "Research-to-manuscript workflow for an explicitly requested end-to-end project. Coordinate research, drafting, integrity checks, review and revision using existing authorization."
metadata:
  version: 3.7.0
  last_updated: '2026-05-05'
  depends_on: deep-research, academic-paper, academic-paper-reviewer
  status: active
  data_access_level: verified_only
  task_type: open-ended
  related_skills:
  - deep-research
  - academic-paper
  - academic-paper-reviewer
---

# Research-to-Manuscript Workflow

Use only for a requested end-to-end research and manuscript task. A paper search,
single review or section edit should use its focused capability directly.

Reconstruct available evidence, current manuscript version, completed stages and
the user's authorized scope. Select the next necessary stage instead of
restarting completed work. Track source and manuscript versions in one local
task record when a durable record helps continuity.

The working sequence is research, draft, integrity checks, review, revision,
re-review where needed, and final verification. At each stage record the output,
evidence gaps and acceptance result. Use `deep-research`, `academic-paper` and
`academic-paper-reviewer` only for their relevant methods.

Verify cited claims against sources and supplied data. Report each unverified
critical claim and its impact; do not assert that all evidence is correct merely
because structural checks passed. A missing critical source can limit a claim
without blocking unrelated supported work.

Continue stages within existing user authority. If a dedicated three-stage
state machine applies, it owns MANUAL approval or BOUNDED_AUTO transitions.
Reopen only decisions affected by material changes. Do not require a fresh user
confirmation after every internal writing or review step.

Deliver the requested manuscript and concise validation record. A process PDF,
collaboration score, dashboard, external review or publication action is optional
and must serve the actual requested deliverable.

The current local workflow is self-contained. Upstream Material Passport,
collaboration scoring and sprint-contract automation are not installed as an
executable bundle; see [installation capabilities](references/installation-capabilities.md).

Work in the current authorized task. Role names describe review perspectives;
they do not require separate agents. Delegate only with independent task
authorization. External sending, journal submission, account actions and extra
knowledge-base writes require their own authorized scope. Preserve existing
approval; ask only for an unresolved decision that affects the work.

Use the user's language, evidence boundaries and document defaults. Match depth
to the requested artifact. Distinguish a draft, a simulated review, a verified
claim and a publication-ready result. Never claim independent or blind review
unless that procedure actually happened.

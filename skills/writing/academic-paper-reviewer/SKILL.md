---
name: academic-paper-reviewer
description: "Academic peer review and re-review of manuscripts: assess evidence, methods, claims and revision priorities. Report distinct perspectives without claiming independent reviewers unless actually used."
metadata:
  version: 1.9.0
  last_updated: '2026-04-23'
  status: active
  data_access_level: verified_only
  task_type: open-ended
  related_skills:
  - academic-paper
  - academic-pipeline
---

# Academic Manuscript Review

Review the supplied manuscript, specific methods, reviewer response or revised
version. Establish the review purpose and field; use the actual paper and its
supporting materials. If essential material is missing, say which assessment
cannot be made and continue the supported parts.

Assess the question and contribution, study design and statistical units, data
quality, methods, claim support, alternative explanations, reproducibility,
figures and citations. Use distinct perspectives when useful, without claiming
independent reviewers. Prioritize issues by their effect on conclusions and the
feasibility of a concrete repair or validation.

For a re-review, map each earlier comment to the actual change and evidence.
Distinguish resolved, partly resolved, unresolved and newly introduced issues.
For methodology-focused review, restrict the output to the requested methods.
An editorial recommendation is a simulated assessment, not a journal decision.

Deliver a concise overall assessment, evidence-linked major/minor findings,
necessary revisions and remaining uncertainty. A focused review need not create
a five-person panel or arbitrary numerical score.

Optional references:
- [Review criteria](references/review_criteria_framework.md)
- [Quality rubrics](references/quality_rubrics.md)
- [Editorial decision standards](references/editorial_decision_standards.md)

The installed package does not contain the upstream sprint-contract validator or
frozen templates. The supported process above is a normal evidence review;
see [installation capabilities](references/installation-capabilities.md) before
promising an upstream strict-contract or paper-blind mode.

Work in the current authorized task. Role names describe review perspectives;
they do not require separate agents. Delegate only with independent task
authorization. External sending, journal submission, account actions and extra
knowledge-base writes require their own authorized scope. Preserve existing
approval; ask only for an unresolved decision that affects the work.

Use the user's language, evidence boundaries and document defaults. Match depth
to the requested artifact. Distinguish a draft, a simulated review, a verified
claim and a publication-ready result. Never claim independent or blind review
unless that procedure actually happened.

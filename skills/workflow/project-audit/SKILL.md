---
name: project-audit
description: This skill should be used when the user asks to audit a project, review a bioinformatics analysis deliverable, check result traceability, validate reproducibility, or perform a structured project audit across code, results, documentation, methods, and conclusion strength.
version: 0.1.0
---

# Project Audit

Use this skill to audit a local project for traceability, code and pipeline reliability, document-result consistency, methodological soundness, conclusion strength, reproducibility, and delivery completeness.

## Goal

Produce an evidence-based audit report that identifies risks, distinguishes direct support from inference, and keeps every finding tied to inspectable files, code, outputs, or logs.

## When to Use This Skill

Use this skill when the user wants to:
- audit a project or delivery package,
- review whether results are traceable and reproducible,
- inspect whether code, outputs, and README are consistent,
- assess whether conclusions are stronger than the evidence supports,
- perform a structured pre-release or pre-submission project check.

## Boundaries

- Focus on audit, review, and evidence tracing.
- Do not rewrite the whole project unless the user separately asks for remediation.
- Do not assume missing evidence exists elsewhere; mark gaps explicitly.
- Do not overstate certainty.

## Default Workflow

1. Define audit scope, project entry point, and available materials.
2. Scan the directory structure and identify code, results, and README-level deliverables.
3. Evaluate findings across the core audit modules in `references/audit-modules.md`.
4. Use `references/checklist.md` to avoid missing required audit checkpoints.
5. Write the final report using `references/output-template.md`.

## Read Order

Load only what is needed:
- `references/checklist.md` for audit-phase checkpoints
- `references/audit-modules.md` for detailed audit dimensions
- `references/output-template.md` for final report structure

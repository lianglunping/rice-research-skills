# Rice Research Skills

Curated Codex skills for rice molecular breeding, bioinformatics, heavy-ion mutagenesis research, reproducible analysis, and thesis or manuscript workflows.

This repository is a selected public snapshot of local research skills. It intentionally excludes system skills, plugin cache contents, temporary test directories, runtime caches, and machine-specific generated files.

## Directory Layout

```text
skills/
  bio/             Rice, variant calling, BSA/QTL-seq, Sanger validation, primer design
  visualization/   Scientific plotting, statistical analysis, result reporting
  writing/         Paper search, paper reading, thesis writing, review response
  workflow/        Project audit, provenance, staged runs, verification, handover
  engineering/     Git workflow, debugging, code review
scripts/
  validate_skills.sh
```

## Included Skill Groups

- `skills/bio`: core biological and bioinformatics workflows for rice research.
- `skills/visualization`: statistical analysis, publication figures, and result reports.
- `skills/writing`: literature, thesis, manuscript, review, and citation workflows.
- `skills/workflow`: reproducibility, provenance, monitoring, audit, and handover workflows.
- `skills/engineering`: development practices used to maintain reproducible research code.

## Install

Copy the skill directories you want into your Codex skills directory:

```bash
cp -R skills/bio/variant-primer-design ~/.codex/skills/
cp -R skills/workflow/project-audit ~/.codex/skills/
```

For a full local install, copy the contents under each group into `~/.codex/skills/`.

## Validation

Run the repository-level validation script before committing changes:

```bash
bash scripts/validate_skills.sh
```

The validation checks that each skill directory has `SKILL.md`, contains required frontmatter fields, and does not include common runtime caches.

## Maintenance Rules

- Keep each skill directory self-contained.
- Preserve original skill directory names unless the `name:` field is intentionally updated.
- Do not commit `.DS_Store`, `__pycache__`, `*.pyc`, logs, or temporary test outputs.
- Do not include private datasets, credentials, tokens, SSH keys, or unpublished analysis results.

## License

No open-source license grant is provided unless a separate license file explicitly says otherwise.

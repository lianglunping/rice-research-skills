# Rice Research Skills

中文 | [English](#english)

## 中文

`rice-research-skills` 是一个面向水稻分子育种、生物信息学、重离子诱变研究、科研写作和可复现分析流程的 Codex skills 集合。它来自本地长期科研工作流的筛选整理，保留了对实际任务有复用价值的技能，并排除了系统 skill、插件缓存、临时测试目录、运行缓存和机器特异性生成文件。

这个仓库适合以下使用者：

- 从事水稻遗传育种、诱变育种、候选基因分析或群体遗传分析的研究人员。
- 需要搭建可复现生信流程的学生、工程师或科研助理。
- 希望用 Codex 辅助论文阅读、综述整理、学位论文写作、项目审计和结果报告的人。
- 希望学习如何组织领域专用 Codex skills 的开发者。

## 仓库内容

```text
skills/
  bio/             水稻、生信、变异分析、BSA/QTL-seq、Sanger 验证、引物设计
  visualization/   统计分析、科研绘图、结果解释和报告
  writing/         文献检索、论文精读、综述、学位论文、审稿回复
  workflow/        复现、溯源、项目审计、长任务监控、交接
  engineering/     Git 工作流、调试、代码审查
scripts/
  validate_skills.sh
docs/
  SKILL_CATALOG.md
```

完整技能目录见 [docs/SKILL_CATALOG.md](docs/SKILL_CATALOG.md)。该目录为每个 skill 提供中文说明、英文说明和相对路径。

## 如何安装

安装单个 skill：

```bash
cp -R skills/bio/variant-primer-design ~/.codex/skills/
cp -R skills/workflow/project-audit ~/.codex/skills/
```

安装某一组 skill：

```bash
cp -R skills/bio/* ~/.codex/skills/
cp -R skills/writing/* ~/.codex/skills/
```

安装全部 skill：

```bash
find skills -mindepth 2 -maxdepth 2 -type d -exec cp -R {} ~/.codex/skills/ \;
```

如果你的 Codex skills 目录不是 `~/.codex/skills`，请把命令中的目标路径替换为你的本地 skills 目录。

## 如何使用

安装后，在 Codex 中直接描述任务即可触发相关 skill。例如：

```text
帮我为这个 InDel 设计 PCR 验证引物，并检查 BLAST 特异性。
请审计这个 BSA/QTL-seq 项目的结果是否可复现。
帮我把这篇水稻突变体论文做主图驱动的精读。
请根据这些结果写一份克制、可追溯的实验总结。
```

Codex 会根据每个 `SKILL.md` 的 `name` 和 `description` 判断是否加载对应 skill。若你希望强制使用某个 skill，可以在请求中明确写出 skill 名称，例如 `variant-primer-design` 或 `project-audit`。

## 验证与维护

提交前运行：

```bash
bash scripts/validate_skills.sh
```

该脚本会检查：

- 每个 skill 目录是否包含 `SKILL.md`。
- `SKILL.md` 是否含有 `name:` 和 `description:`。
- 仓库中是否残留 `.DS_Store`、`__pycache__`、`*.pyc` 等运行缓存。
- `skills/` 下是否误放 `temp_tests/` 或 `scratch/` 临时文件。

维护建议：

- 保持每个 skill 目录自包含。
- 除非同步修改 `SKILL.md` 的 `name:` 字段，否则不要随意重命名 skill 目录。
- 不提交私有数据、未公开分析结果、账号、token、SSH key 或机器特异性路径。
- 修改 skill 后同步更新 [docs/SKILL_CATALOG.md](docs/SKILL_CATALOG.md)。

## 许可边界

当前仓库为 public，但 `LICENSE` 是 all rights reserved。除非仓库所有者另行更换开源许可证，否则公开可见不等于授予复制、修改、分发或商业使用许可。

## English

`rice-research-skills` is a curated collection of Codex skills for rice molecular breeding, bioinformatics, heavy-ion mutagenesis research, scientific writing, and reproducible analysis workflows. It is a selected public snapshot of local research workflows, with system skills, plugin caches, temporary test folders, runtime caches, and machine-specific generated files intentionally excluded.

This repository is intended for:

- Researchers working on rice genetics, molecular breeding, mutagenesis breeding, candidate genes, or population genomics.
- Students, research assistants, and engineers who need reproducible bioinformatics workflows.
- Users who want Codex support for paper reading, review synthesis, thesis writing, project audits, and result reporting.
- Developers who want examples of domain-specific Codex skill organization.

## Repository Contents

```text
skills/
  bio/             Rice research, bioinformatics, variants, BSA/QTL-seq, Sanger validation, primer design
  visualization/   Statistical analysis, scientific figures, result interpretation, reporting
  writing/         Literature search, paper reading, reviews, thesis writing, rebuttals
  workflow/        Reproducibility, provenance, project audit, monitoring, handover
  engineering/     Git workflow, debugging, code review
scripts/
  validate_skills.sh
docs/
  SKILL_CATALOG.md
```

See [docs/SKILL_CATALOG.md](docs/SKILL_CATALOG.md) for the full bilingual skill catalog with descriptions and paths.

## Installation

Install one skill:

```bash
cp -R skills/bio/variant-primer-design ~/.codex/skills/
cp -R skills/workflow/project-audit ~/.codex/skills/
```

Install a group of skills:

```bash
cp -R skills/bio/* ~/.codex/skills/
cp -R skills/writing/* ~/.codex/skills/
```

Install all skills:

```bash
find skills -mindepth 2 -maxdepth 2 -type d -exec cp -R {} ~/.codex/skills/ \;
```

If your Codex skills directory is not `~/.codex/skills`, replace the destination path with your local skills directory.

## Usage

After installation, describe your task naturally in Codex. Examples:

```text
Design PCR validation primers for this InDel and check BLAST specificity.
Audit whether this BSA/QTL-seq project is reproducible.
Deep-read this rice mutant paper using the main figures as the entry point.
Write a restrained, traceable experiment summary from these results.
```

Codex decides whether to load a skill from the `name` and `description` fields in each `SKILL.md`. To force a specific skill, mention its name explicitly, such as `variant-primer-design` or `project-audit`.

## Validation and Maintenance

Before committing changes, run:

```bash
bash scripts/validate_skills.sh
```

The script checks that:

- Every skill directory has a `SKILL.md`.
- Each `SKILL.md` contains `name:` and `description:`.
- Runtime caches such as `.DS_Store`, `__pycache__`, and `*.pyc` are absent.
- Temporary folders such as `temp_tests/` or `scratch/` are not placed under `skills/`.

Maintenance guidelines:

- Keep each skill directory self-contained.
- Do not rename a skill directory unless you also intentionally update the `name:` field in `SKILL.md`.
- Do not commit private datasets, unpublished analysis results, credentials, tokens, SSH keys, or machine-specific paths.
- Update [docs/SKILL_CATALOG.md](docs/SKILL_CATALOG.md) when adding, removing, or substantially changing skills.

## License Boundary

This repository is public, but the current `LICENSE` is all rights reserved. Public visibility does not grant permission to copy, modify, distribute, or commercially use the contents unless the repository owner later adopts a separate open-source license.

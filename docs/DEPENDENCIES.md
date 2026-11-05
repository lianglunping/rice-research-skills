# Dependencies and snapshot scope / 依赖与快照范围

## Included / 本次包含

This snapshot keeps the existing 49 skill directories and category layout.
48 directories were refreshed from the selected local Codex skill collection,
including its nested academic-writing skills, then sanitized for publication.
`project-audit` was absent from that selected source, so its existing public
snapshot is retained. No additional installed skills are implicitly published.

The staged run protocol incorporates the already published generic companion
from [codex-three-stage-workflow v0.2.0](https://github.com/lianglunping/codex-three-stage-workflow/releases/tag/v0.2.0),
including downstream dynamic-evidence checks. Install that suite separately if
you need its runtime policy, model-routing helper or three-stage state machine.
The collection does not activate the three-stage workflow merely by being installed.

本次保留原有 49 个技能目录和分类，更新指定源中可找到的 48 个技能并进行脱敏。
`project-audit` 在指定源中不存在，保留仓库原有公开快照。阶段执行协议复用已发布的
通用配套修正；需要其运行策略和模型路由时，另行安装上面链接的三阶段套件。

## Caller-owned inputs / 调用者提供的输入

Reference genomes, annotations, genotype/phenotype tables, FASTQ/BAM/VCF files,
credentials, server configuration and note-vault profiles are not bundled.
`/path/to/...`, `REPLACE_*` and template sample identifiers are placeholders.
Supply actual authorized inputs and verify their reference, schema and provenance
before running a workflow. Published scripts and templates do not establish a
validated analysis of a new biological dataset.

单倍型与重测序配置使用通用占位路径和主机字段；运行前填写并核验。
文献技能使用调用者指定的笔记库及已有目录约定，不包含个人笔记库路径或配置。

## Optional upstream ARS features / 可选上游学术组件

Some academic-paper and academic-pipeline references describe advanced Material
Passport, corpus-adapter, compliance and reproducibility features from their
parent ARS package. The selected source did not contain the parent `shared/`,
`shared/contracts/passport/`, `scripts/adapters/`, `deep-research/` or design
specifications. They are external requirements, not working bundled components.
Their names remain in references for identification; dead local links were removed.

Before enabling a feature that consumes an absent schema or adapter, obtain and
verify the matching upstream component under its applicable license. Report the
specific missing requirement and pause that feature rather than inventing a
schema, silently accepting a passport or claiming that its gate passed.

部分高级学术编排功能依赖上游 ARS schema、适配器或设计规范，指定源并未包含它们。
启用相关功能前必须补齐并核验匹配组件；缺失时报告具体缺口，不将结构声明视为验收通过。

## Validation environment / 验证环境

`validate_skills.sh` uses Bash and Python's standard library for metadata, source
syntax and local-link checks. `test_skills.sh` runs shipped synthetic/unit tests
for monitoring, provenance and primer helpers; install BLAST+ (`blastn` and
`makeblastdb`) and `requirements-test.txt`
in a project-local environment. The primer end-to-end test runs BLAST on a synthetic reference, never on research
inputs. Workflow-specific R, sequencing tools, reference databases,
Pandoc/LaTeX and optional integrations are validated in the caller's own run.

The legacy provenance end-to-end shell examples require `uv` and use temporary
example outputs; they are not part of the release test command. The staged
coordination control plane uses `fcntl`, so Windows support is not claimed.

## Publication boundary / 发布边界

Publication review covers the sanitized current file tree and the new commit.
The existing published Git history is retained; updating this snapshot is not a
retroactive removal of information from old commits. Local source maps, privacy
policies, findings, logs and test environments stay outside the repository.

发布核验覆盖脱敏后的当前文件树及新增提交；既有 Git 历史保持原状，不能将本次更新
理解为已经清除历史提交中的信息。原始本机技能和既有项目工作副本不作修改。

# docs/ — Release 文档模板

本目录含 release/ 所需的 8 个 MD 模板（基于 v2.1 实战版本）。

## 模板文件

| 模板 | 对应 release 文件 | 占位符 |
|------|-------------------|--------|
| `00_README.md.template` | `release/00_README.md` | `{{PROJECT}}` / `{{VERSION}}` / `{{TOP_QTL_SUMMARY}}` |
| `01_METHODS.md.template` | `release/01_METHODS.md` | `{{PARAMS}}` / `{{POP_TYPE}}` |
| `02_LIMITATIONS.md.template` | `release/02_LIMITATIONS.md` | `{{BULK_SIZE}}` / `{{FALLBACK_RATIONALE}}` |
| `03_COLUMN_DEFINITIONS.md.template` | `release/03_COLUMN_DEFINITIONS.md` | 通用, 无占位 |
| `HOWTO_GO_KEGG.md.template` | `release/HOWTO_GO_KEGG.md` | `{{SPECIES}}` / `{{GENE_ID_PREFIX}}` |
| `CHANGELOG.md.template` | `release/CHANGELOG.md` | `{{VERSION_HISTORY}}` |
| `figures_README.md.template` | `release/figures/README.md` | 通用 |
| `Top_QTL_annotated.md.template` | `release/Top_QTL_annotated.md` | `{{TOP_TABLE}}` |

## 使用方式（由 release_packager.sh 执行）

```bash
# 使用 envsubst 或 Python 替换占位符
PROJECT=grape_5h_waterloss_BSA \
VERSION=v2.1 \
BULK_SIZE=20 \
envsubst < ~/.codex/skills/bio-bsa-qtlseq/docs/00_README.md.template > release/00_README.md
```

或用 Python:

```python
from string import Template
Template(open('template.md').read()).safe_substitute(PROJECT='...', VERSION='v2.1')
```

## 占位符命名约定

- 必须用 `{{UPPER_CASE}}` (jinja-like, 但实际用 Python string.Template)
- 嵌套 data 用 `{{SECTION.FIELD}}`
- 可选字段用 `{{FIELD|default:值}}`

v2.1 模板中实际已含真实数据（葡萄 5h），新项目可先复用再替换。

# De-AI For Biology Writing

Use this module when the user wants cleaner academic prose without changing the evidence payload.

## Preserve First

Never rewrite or alter:
- numbers and units,
- statistical values,
- gene names and locus IDs,
- sample or line identifiers,
- figure or table references,
- citation markers,
- material generation labels such as `M1`, `M2`, `M3`.

## High-Priority AI Traces

### Empty importance claims

Bad:
- "具有重要意义"
- "provides an important foundation"
- "represents a crucial breakthrough"

Prefer:
- say what the result enables,
- or delete the sentence if it adds no information.

### Inflated mechanism talk

Bad:
- "deeply reveals the underlying mechanism"
- "highlights the broader importance of"

Prefer:
- state the exact observation and stop at the supported level.

### Mechanical literature narration

Bad:
- three or more consecutive `某某等报道/提出/发现`
- three or more consecutive `Author et al. reported`

Prefer:
- theme grouping plus contrast sentence.

### Generic transitions without content

Bad:
- "近年来，相关研究不断深入"
- "With the rapid development of omics technologies"

Prefer:
- start from the concrete biological or analytical problem.

## Biology-Aware Rewrites

### Chinese

- "本研究具有重要理论意义和应用价值" -> "本研究为后续候选位点筛选和验证设计提供了结果基础"
- "结果表明该方法表现出良好的鲁棒性" -> "在当前样本和阈值设定下，该流程在三组比较中给出一致方向的结果"
- "进一步揭示了其潜在机制" -> "提示该现象可能与染色质可及性有关，但当前结果仍为描述性证据"

### English

- "This result is of great significance" -> "This result provides a starting set for downstream candidate prioritization"
- "The method showed robust performance" -> "The workflow produced the same direction of effect across the current comparison settings"
- "This finding reveals the underlying mechanism" -> "This finding is consistent with a possible chromatin-related explanation, but the present evidence remains descriptive"

## Keep Legitimate Academic Phrases

Do not auto-delete these when they are followed by real evidence:
- "值得注意的是"
- "进一步地"
- "Importantly"
- "Notably"
- "Previous studies have shown"
- "Evidence suggests"

The issue is not the phrase itself. The issue is unsupported filler.

## Output Modes

- `light`: remove obvious AI traces only
- `standard`: improve rhythm, density, and restraint
- `strict`: sentence-level clean-up with aggressive filler removal, while preserving content

## Recommended Delivery

When the user is editing an existing document, return:
- revised text,
- short note on the main AI traces removed,
- and if needed a patch pack via `section_patch_pack.py`.

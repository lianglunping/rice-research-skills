# Evidence Labels

Use these labels consistently.

| Label | Meaning | Required anchor |
| --- | --- | --- |
| `[原文证据]` | Direct evidence from the PDF, figure, table, method, result, supplement, or caption | Section, page, figure/panel, table, quote, or annotation link |
| `[原文结论]` | A conclusion or interpretation explicitly stated by the authors | Section or exact claim location |
| `[原文重构]` | A structured reconstruction made from several original-paper locations | List of supporting original anchors |
| `[外部检索补充]` | Post-publication progress, metadata, author profile, citing work, or method update from outside the PDF | Source name, date searched, URL/DOI/title |
| `[专家研判]` | Expert judgment about evidence strength, limitations, breeding relevance, or alternative explanation | Reasoning basis and uncertainty |

Hard rules:

- Never mix `[外部检索补充]` into original Results or Methods facts.
- Use `【原文未提供】` for missing sequencing depth, sample size, replicate design, software version, statistical threshold, filtering parameter, field environment, genotype background, or validation detail.
- Use `【图表解析受限】` when figure resolution, OCR, panel boundaries, axis labels, legends, or captions are unclear.
- Use `【注意：原文信息存在疑似冲突】` when sections disagree on sample counts, parameters, materials, or conclusions.
- For key claims, prefer "结论 - 依据 - 限定条件" rather than absolute wording.

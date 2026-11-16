---
name: bio-publication-figure-director
description: "Publication figure director: Plan, build, redesign, or audit traceable publication-grade biological figures from claim and source data through chart selection, composition, reproducible implementation, visual QA, and delivery."
---

# 生物学论文绘图总控

把“数据 + 科研问题”转成可追溯、可复现、能经受审稿的整图。优先保证科学口径和论证结构，再追求视觉工艺；不要用美化替代证据。

## 选择工作模式

- `ADVISE`：只给图型、panel 结构或修改建议；检查数据与证据，不写文件。
- `AUDIT`：审阅现有图、caption、脚本和来源；报告问题与修复优先级，不实施修复，除非用户同时要求优化。
- `BUILD`：创建或优化图；执行 Figure Contract、派生数据、脚本、渲染和 QA 闭环。

简单单图使用轻量合同，不强行引入整套交付目录：在现有任务记录或脚本注释中记录问题、实际输入、统计单位和输出即可；保留脚本、输入引用、PDF 和所需 PNG，并检查实际成图。下文的初始化器、独立 QA YAML、manifest 和完整交付清单仅用于需要这些记录的正式主图、多面板图或明确要求的投稿交付，不作为所有绘图任务的前置条件。已有有效记录直接复用，不生成重复文件。

把当前 `SKILL.md` 所在目录解析为 `<SKILL_ROOT>`。从项目目录工作时也使用
`<SKILL_ROOT>/scripts/...`，不要误把项目自身的 `scripts/` 当成本 skill。

## 基本边界

- 先遵守项目最近层级的 `AGENTS.md`、既有环境、绘图体系和期刊规范。
- 对只读审阅或图型建议，不修改文件；对明确的绘图请求，直接实现并做相称验证。
- 不覆盖原始数据或旧图。把派生数据、脚本、预览和正式输出放入可追踪的新目录。
- 不把相关写成因果，不把候选写成验证，不把共享来源的技术一致性写成独立验证。
- 不把示例数据、FigureYa 成图或交互式浏览器当作用户研究证据。
- 不为补齐画面而虚构数值、样本、误差、显著性、基因位置、机制或实验流程。

## 1. 建立 Figure Contract

绘图前写一个轻量合同。简单单图可在工作记录中保留；正式多面板图需要新建追踪目录时可使用初始化脚本：

```bash
python <SKILL_ROOT>/scripts/init_figure_bundle.py \
  --output <project>/figure_work --figure-id fig1_main
```

需要字段定义时读 `references/figure-contract.md`。

至少确定：

1. `core_question`：这张图回答什么问题。
2. `core_claim`：一句话、证据允许强度内的主张。
3. `claim_status`：`observed | conditional_association | hypothesis | future_validation`。
4. `source_data`：精确路径、样本/材料、分母、统计口径。
5. `hero_panel` 或 `core_panels`：记录单一主证据或同等重要的面板组。
6. `target`：记录目标文档及最终宽、高（mm），依据实际版面选择尺寸并注明假设。

若上下文足以可靠推断，直接记录假设并推进；只有会改变科研结论、样本映射或统计口径时才暂停询问。

## 2. 锁定证据与数据契约

在选择图型前核对：

- 输入文件、字段含义、单位、缺失值、重复、分组、每组 `n` 和总分母。
- 统计检验、效应量、区间类型、校正方法与随机种子。
- 基因组任务的参考基因组、注释版本、坐标基准、contig 命名、链方向、REF/ALT 和样本 ID。
- 育种/世代任务的材料、家系、世代、选择历史和检测边界。

把作图所需的派生表写成 TSV/CSV；不要让图脚本依赖手工复制的报告数字。必要时记录输入 checksum，作图前后复核输入未变。

## 3. 剖析数据，再选图

先用项目现有脚本或 R/Python 做只读剖析：类型、范围、分布、偏态、异常值、组内样本量、缺失、相关结构和过度绘制风险。没有项目剖析脚本时运行：

```bash
python <SKILL_ROOT>/scripts/profile_figure_data.py <data.csv|data.tsv|data.xlsx> \
  --group <group_column> --format markdown
```

把报告当作选图输入，不把自动建议当作统计结论。

按“变量结构 × 论证意图 × 样本量”选图：

- 小样本组间比较：显示每个数据点；避免只画均值柱。
- 连续变量关系：散点、拟合与不确定性；无时间/剂量顺序时不连线。
- 时间/剂量：轨迹与区间；区分重复测量和独立样本。
- 矩阵：热图并说明标准化、距离和聚类方法。
- 集合交集：类别少时 Venn，类别多时 UpSet。
- 组成：优先排序条形或堆叠条形；除非角度本身有意义，不用饼图。
- 多数量级：使用明确标注的 log 轴；不靠截断坐标制造差异。

水稻与组学场景的具体路由见 `references/rice-bio-routing.md`。

## 4. 设计整图论证

围绕核心问题安排主证据与辅助证据，布局随信息量和阅读任务调整：

1. 确认承载主结论的 panel 或相互依赖的 panel 组；按证据角色、可读性和信息密度分配面积，不设固定 hero 比例。
2. 为每个辅助 panel 写一句 `defends`；不能独立支持子主张的 panel 删除或移至补充材料。
3. 用阅读顺序组织 panel：材料/设计 → 全局结果 → 关键证据 → 边界/验证。
4. 等权比较可用等权网格；需要强调或不同信息密度时调整宽高，不能用版面面积夸大证据强度。
5. 主图保持紧凑叙事，把全矩阵、完整 QC、read view 和交互浏览器放补充材料或在线资源。

示意图、技术路线图和机制图也必须可复现。用 TikZ、SVG、R 或 Python 原创重绘，并嵌入真实的科研对象或设计边界；不要制作只有通用方框和箭头的“填充型”hero 图。AI 生成图只能作为明确标注的装饰性概念图，不能承载数据或机制证据。

## 5. 选择实现后端

按以下顺序决策：

1. 沿用项目已有且可复现的绘图栈。
2. 无既有体系时优先 R/ggplot2。
3. Python 数据流程已成熟时使用 matplotlib/seaborn。
4. 方法与框架示意图使用 standalone TikZ 或可编辑 SVG；复杂基因组图优先成熟的 R/Bioconductor 工具。

按需调用当前已启用的本地专项 skill，不复制其完整说明。下列路由是候选索引；技能未启用时先用当前工具完成任务，只有用户要求启用时才修改常用配置：

- 基础 R 图：`bio-data-visualization-ggplot2-fundamentals`
- 配色：`bio-data-visualization-color-palettes`
- 多面板：`bio-data-visualization-multipanel-figures`
- 导出：`bio-reporting-figure-export`
- 热图：`bio-data-visualization-heatmaps-clustering`
- 基因组轨道：`bio-data-visualization-genome-tracks`
- Manhattan/QQ：`bio-data-visualization-manhattan-qq-locuszoom`
- 火山图：`bio-data-visualization-volcano-customization` 或 `bio-data-visualization-volcano-and-ma-plots`
- UpSet：`bio-data-visualization-upset-plots`
- Circos：`bio-data-visualization-circos-plots`
- 统计标注：`bio-data-visualization-statistical-annotation`
- 水稻候选基因单倍型：`bio-haplotype-rice-candidate-gene`

## 6. 使用三方资源

需要借鉴已有图型时，先看[可选上游参考](references/upstream-resources.md)。调用者已有 FigureYa checkout 时可只读搜索：

```bash
python <SKILL_ROOT>/scripts/search_figureya.py manhattan chromosome rice --root <figureya-checkout>
```

- 从 FigureYa 检索 R 图型与输入结构；先读对应 `.Rmd`，只移植必要逻辑。
- 不自动执行 FigureYa 的 `install_dependencies.R`；先检查包、版本和人类物种绑定。
- 从 scipilot 借鉴数据剖析、图型拦截、渲染预览和视觉 QA。
- 从 Icarus 借鉴图件合同与方法示意图，从 academic-figure-skill 借鉴布局和图件工艺。
- 保留来源、commit、许可和必要引用；不要把 CC BY-NC-SA 代码无说明地混进可商业交付。

## 7. 实现与风格

先读[统一出版样式](references/publication-style.md)，按项目或期刊规定覆盖默认。
通用默认使用 Arial，面板字母 9 pt 粗体，轴标题、图例和常规标注 8 pt，轴刻度 7 pt；坐标轴、
数据曲线和误差棒分别用 0.75、1 和 0.75 pt。多面板统计图保留独立的可编辑源和输出。

- 让脚本从文件读取数据；不要在代码中手抄大块数据。
- 记录入口命令、软件/包版本、随机种子和输出路径。
- 同一生物学类别跨图保持同色；颜色之外增加形状、线型或直接标签。
- 直接声称相互对应的 panel 必须共享同一数据子集和距离口径；例如 A 展示筛选位点而 B 展示单倍型网络时，B 的边距离应由 A 的实际展示列计算。若使用全量数据，必须明确标注，不能暗示逐项对应。
- 一个 panel 内一个视觉通道只承担一个含义。地图中的类别构成可按密度与阅读任务采用聚合符号、饼图、条形或分面；明确颜色、面积与总量的映射，审计聚合前后计数守恒。坐标避让应可复现，保留原始与绘制坐标并标明位移。树图的支系、分组和外环使用可区分的通道与图例，不预设特定分组数或固定配色布局。组合图的 panel 字母和阅读顺序必须与图注角色一致。
- 默认白底、无无意义背景网格、色盲友好、图中文字英文。
- 字体优先遵守目标期刊和项目既有体系。英文期刊图通常使用其要求的 Arial/Helvetica 或 Times；中文学位论文图使用宋体 CJK，英文、数字、拉丁字符和基因名使用 Times New Roman。不要把 Word 字体默认值机械套到所有英文期刊图。
- 保留无显著差异、零效应或不确定结果。误差棒或区间注明 SD、SEM、CI 或 IQR，并按分析设计交代 `n`、检验与校正。
- 按最终版面尺寸绘制，避免插入 Word/LaTeX 后大幅缩放。
- 主输出至少包含可编辑矢量 PDF 和高分辨率 PNG；按期刊要求补 SVG/TIFF/EPS。

## 8. 运行双层 QA

先做机械检查，再做科学与视觉判断。完整清单见 `references/quality-gates.md`。

机械层：

- 脚本可重跑，数据路径有效，随机性固定。
- 在最终文件回读页面尺寸、字体、矢量内容与栅格有效 DPI。
- 字体无缺字，文本未裁切，图例不遮挡，panel 标签对齐。
- 高密度图可用 Poppler word-box 或可用的等效工具筛查重叠与越界。包围盒相交是待复核信号，不能直接等同于字形碰撞；结合最终尺寸渲染修复实际遮挡、缺字和裁切，并记录误报依据。没有该工具时采用其他版面检查与实际读图，不以工具缺失替代视觉验收。
- 表格和分区式图例必须额外检查“指定矩形内完整容纳”：页面级 word box 无重叠、无越界并不能证明文字没有被单元格或图例边界截断。使用实际字体度量加留白验证，并查看最终 DPI 的高密度局部裁图。
- 图、caption、manifest 中的关键数字一致。
- 对直接关联的 panel 自动复算跨图数据契约，例如展示位点数、逐边距离和刻线数量；对颜色、线型、形状和点大小分别记录唯一语义。

判断层：

- 先打开最终尺寸 PNG；在 Codex 中使用 `view_image`，不要只读代码或文件属性。
- 遮住 caption 后，核心主张是否仍能从图中读出。
- 删除任一 panel 后，核心论证是否明显变弱。
- 灰度或常见色觉缺陷模拟下，系列是否仍可区分。
- 坐标、统计和视觉强调是否诚实。
- 连线、树枝、节点、网格、符号和图例是否均未穿过字形；先画几何元素、后画文字，关键标签使用不透明净空，图例使用轴外独立区域。
- 逐个确认表头和图例标签完整落在分配给它的单元格/矩形内；旋转后放不下时增加行高或改为水平多行，不得以页面内“看似存在”为验收标准。
- 观察、关联、假设和未来验证是否被清晰区分。

使用完整交付目录时，把判断结果写入已有的 `qa/<figure_id>_qa.yaml`；轻量单图在现有任务记录中简记即可。只执行与该图及本次改动有关的检查。发现实际问题时修复并复查受影响项；有效证据不变时不重复全套 QA，验收通过即停止。不要用“脚本成功”代替视觉验收。

需要快速检查交付包时运行：

```bash
python <SKILL_ROOT>/scripts/audit_figure_bundle.py \
  --base <figure_work>/figures/fig1_main \
  --manifest <figure_work>/figures/figure_manifest.tsv \
  --contract <figure_work>/contracts/fig1_main_contract.yaml \
  --require pdf png
```

脚本只给机械底线；不能替代读图和科研口径审阅。

## 9. 交付

需要完整交付合同的正式图交付以下内容；轻量单图按前述轻量规则交付，不额外补齐整套文件：

- 生成脚本和运行入口。
- 派生数据表及其来源。
- PDF + PNG，及期刊要求的其他格式。
- Figure Contract、caption 草稿、`figure_manifest.tsv` 和四轴 QA 记录。
- QA 结果、已知限制和未完成验证。

caption 先陈述结论，再定义 panel、符号、统计、`n` 和误差。不要写成“图中展示了……”，也不要让 caption 把图本身没有的证据升级成结论。

## 按需读取

- Figure Contract 字段与例子：`references/figure-contract.md`
- 水稻/生信图型和本地 skill 路由：`references/rice-bio-routing.md`
- 投稿级验收门：`references/quality-gates.md`
- 统一出版样式与 R/Python 接口：`references/publication-style.md`
- 可选上游资源、版本与许可：`references/upstream-resources.md`
- 数据剖析：`scripts/profile_figure_data.py`
- FigureYa 检索：`scripts/search_figureya.py`
- 交付目录初始化：`scripts/init_figure_bundle.py`
- 机械交付审计：`scripts/audit_figure_bundle.py`

## Scope notes

Before choosing inputs, comparison units or conclusion thresholds, read
[the scientific scope notes](references/scope-notes.md) for this task.

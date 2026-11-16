# Figure Contract

在动手绘图前固定“图要回答什么、数据允许说到哪里”。简单单图可缩减字段，正式多面板图保留完整合同。

## 字段

| 字段 | 要求 |
|---|---|
| `figure_id` | 稳定编号，不用 `final_final` |
| `core_question` | 可由数据回答的一个问题 |
| `core_claim` | 一句话；强度不超过证据 |
| `claim_status` | `observed`、`conditional_association`、`hypothesis` 或 `future_validation` |
| `target` | 期刊/学位论文/汇报及最终宽、高（mm） |
| `backend` | 项目既有体系；无既有体系时通常为 R |
| `source_data` | 精确输入路径；多输入逐项列出 |
| `derived_data` | 作图派生表及生成脚本 |
| `entry_command` | 可复现的唯一绘图入口 |
| `population` | 材料、世代、家系、样本范围 |
| `denominator` | 比例或检出率的精确分母 |
| `genome_contract` | 参考、注释、坐标基准、contig、链、REF/ALT |
| `panels[].defends` | 每个 panel 支持的唯一子主张 |
| `panels[].source` | 对应派生表/字段/脚本输出 |
| `panels[].editable_output` | 多面板图为每个统计 panel 保留可独立编辑的输出与生成脚本 |
| `hero_panel` / `core_panels` | 主证据可由单个 panel 或同等重要的一组 panel 承担。记录其证据关系 |
| `stats_on_figure` | 效应量、区间、n、检验、校正 |
| `export` | 最终尺寸、格式、DPI、字体与导出设备 |
| `limitations` | 图不能回答的内容 |

## 主张强度

- `observed`：数据中直接观察到的计数、分布、坐标或检测结果。
- `conditional_association`：在明确材料、筛选和检测设计下的关联或协调观察。
- `hypothesis`：由观察支持但尚未验证的解释。
- `future_validation`：需 KASP、Sanger、独立 WGS、后代或湿实验验证的内容。

不要用视觉邻近、同一 panel、共享 reads 或筛选后的交集暗示独立验证、共传递或机制。

## Panel 句式

为每个 panel 写：

> Panel A defends that `<限定材料/条件下的直接结果>` using `<数据源/统计>`; it does not establish `<越界结论>`。

若句子写不出来，说明 panel 可能只是装饰或其证据来源不清。

## 验收问题

1. 核心问题是否真的能由这些数据回答？
2. 图中的每个关键数字能否回溯到派生表或脚本输出？
3. 分母、样本和材料范围是否在图或 caption 中可见？
4. 基因组坐标合同是否完整？
5. 图是否把条件性观察升级成遗传传递、因果或机制？

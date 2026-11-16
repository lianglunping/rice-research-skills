# 可选上游参考

本技能独立运行。可按需查阅以下公开资源。引用或复用前核对所取版本的许可证、依赖和图所代表的物种及数据契约。

| 资源 | 查阅版本 | 许可 | 用途 |
|---|---|---|---|
| [FigureYa](https://github.com/ying-ge/FigureYa) | `f627917b79f28558779fb2e3ea2014cede41b89e` | CC BY-NC-SA 4.0 | 图型和 R 输入结构 |
| [scipilot-figure-skill](https://github.com/Haojae/scipilot-figure-skill) | `43098ddb9e6a6d142218540c114f9ed38922fc42` | MIT | 数据剖析和渲染检查 |
| [Icarus-Figures](https://github.com/TAO-QKV/Icarus-Figures) | `0bcaa40c07ef0dc6ea1506ab147ce0a4f5a542fd` | MIT | 图件合同、视觉质量和方法示意图 |
| [academic-figure-skill](https://github.com/TingxiYu/academic-figure-skill/tree/1df9940dd01ac939f072b12fe28d6353b79b90f9) | `1df9940dd01ac939f072b12fe28d6353b79b90f9` | Apache-2.0 | 版式、图件工艺及工具参考 |

已有 FigureYa checkout 时，可只读搜索它：

```bash
python <SKILL_ROOT>/scripts/search_figureya.py manhattan gwas --root <figureya-checkout>
```

也可设置 `FIGUREYA_ROOT`。先阅读匹配的 Rmd，检查人类注释、染色体命名及输入
假设，再独立实现适用部分。FigureYa 的代码和图件受非商业及相同方式共享条款约束，
查看仓库引用要求并区分图型思路和直接复用。审阅依赖后再决定是否运行上游脚本。
上游模板、资产和示例数据由调用者按需取得。科学绘图口径和验收使用本技能的
[统一出版样式](publication-style.md)与[质量检查](quality-gates.md)。

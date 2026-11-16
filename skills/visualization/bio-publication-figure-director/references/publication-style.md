# 统一出版样式

先确定最终版面宽和高（mm）。目标期刊、学位论文或项目规范优先。目标未知时可用单栏约 85–90 mm、宽图约 107–190 mm、小面板约 50 × 50 mm 试排。按实际栏宽、高度和内容可读性调整，并记录选用尺寸。

| 项目 | 通用默认 |
|---|---|
| 英文与数字 | Arial，须在渲染机上安装。缺少时明确选择可用的替代字体并验收 |
| 面板字母 | 9 pt，粗体 |
| 轴标题、图例与普通标注 | 8 pt |
| 轴刻度 | 7 pt |
| 坐标轴与刻线 | 0.75 pt |
| 数据曲线 | 1 pt |
| 误差棒及端帽 | 0.75 pt |
| 背景与编码 | 白底，无默认网格。同类跨图同色，并按需配合形状或线型 |
| 默认导出 | 矢量 PDF 与 300 DPI PNG，均按最终使用尺寸 |

## R

默认基于项目的 ggplot2 对象绘制。加载 [R 样式](../scripts/publication_style.R)，将线宽明确用于对应图层。ggplot2 用 `.pt` 将 `linewidth` 传给 grid，标准 R PDF 设备的 grid `lwd = 1` 为 0.75 pt，因此使用 `publication_linewidth(points)` 换算。该换算适用于本工具的标准 R PDF 与 ragg PNG 设备。用不同设备时应复核实际输出。

```r
source(file.path(skill_root, "scripts", "publication_style.R"))
p <- ggplot2::ggplot(series, ggplot2::aes(dose, estimate)) +
  ggplot2::geom_line(linewidth = publication_curve_linewidth) +
  ggplot2::geom_errorbar(ggplot2::aes(ymin = lower, ymax = upper),
                        linewidth = publication_error_linewidth, width = 0.3) +
  publication_theme()
save_publication_figure(p, "dose_response.pdf", 85, 60)
save_publication_figure(p, "dose_response.png", 85, 60)
```

PDF 默认用 `grDevices::cairo_pdf`。macOS 可显式传 `pdf_device = "quartz"`。
先确认系统具备所选设备及字体，再回读 PDF 页面和嵌入字体。Cairo PDF 可能将页面量化
到整点，宽高各有至多约 1 pt 的差异。对尺寸要求更严的任务应选可保留分数点的设备并实测。
PNG 依赖 `ragg`，按整数像素表示尺寸，回读时允许每边最多 1 px 的差异。
期刊有额外字号要求时，使用显式 `theme()` 参数覆盖。自由文本应设定字体并使用
`geom_text(size = 8, size.unit = "pt")` 等以点为单位的写法。

## Python

在 [Matplotlib 样式](../scripts/publication_style.py) 所在目录可导入时，使用局部
`rc_context`。其中的字体和线宽以 pt 为单位。用误差棒时显式指定线身和端帽粗细。
设置和期刊要求不同时，在当前作用域覆盖对应值。

```python
import matplotlib as mpl
from matplotlib.figure import Figure
from publication_style import ERROR_PT, publication_rc, save_publication_figure

with mpl.rc_context(publication_rc()):
    fig = Figure(layout="constrained")
    ax = fig.subplots()
    ax.errorbar(dose, estimate, yerr=errors, fmt="o-", capsize=2,
                elinewidth=ERROR_PT, capthick=ERROR_PT)
    ax.set(xlabel="Dose (Gy)", ylabel="Response")
    save_publication_figure(fig, "dose_response.pdf", 85, 60)
    save_publication_figure(fig, "dose_response.png", 85, 60)
```

## 拼版和成图

- 统计图用 patchwork、GridSpec 或同等矢量工作流拼版。保留独立生成入口及每个 panel 的可编辑源和输出。照片、显微图和必要截图可嵌入拼版，注明各自的尺寸和来源。
- 同等重要的证据允许等权布局。面板标签随图件固定，顺序与图注一致。
- 按摆放后的物理尺寸算栅格有效 DPI。避免紧裁后改变页面尺寸。缩放影响字号、线宽和比例尺，优先在最终尺寸重绘，图像和比例尺必须联动缩放。
- 打开最终成图检查可读性、裁切与遮挡。检查实际 PDF 页面、嵌入字体、文字和线条；检查 PNG 像素和 DPI。无显著差异、零效应或不确定结果照常作图，呈现问题所需的观测值、效应量和不确定性。

参考 [ggplot2 图形规格](https://ggplot2.tidyverse.org/articles/ggplot2-specs.html) 与
[Nature 图件准备规范](https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/)。

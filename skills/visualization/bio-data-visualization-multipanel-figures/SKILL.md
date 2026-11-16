---
name: bio-data-visualization-multipanel-figures
description: "Data visualization multipanel figures: Combine multiple plots into publication-ready multi-panel figures using patchwork, cowplot, or matplotlib GridSpec with shared legends and panel labels."
metadata:
  tool_type: mixed
  primary_tool: patchwork
---

## Version Compatibility

Reference examples tested with: ggplot2 3.5+, matplotlib 3.8+

Before using code patterns, verify installed versions match. If versions differ:
- Python: `pip show <package>` then `help(module.function)` to check signatures
- R: `packageVersion('<pkg>')` then `?function_name` to verify parameters

If code throws ImportError, AttributeError, or TypeError, introspect the installed
package and adapt the example to match the actual API rather than retrying.

# Multi-Panel Figure Assembly

**"Combine multiple plots into one figure"** → Arrange subplots into a publication-ready multi-panel layout with shared legends and consistent sizing.
- R: `patchwork::wrap_plots()`, `cowplot::plot_grid()`
- Python: `matplotlib.pyplot.subplots()`, `fig.add_subplot()`

Use the [shared publication style](../bio-publication-figure-director/references/publication-style.md)
for the intended page size. Compose statistical plots as editable vector objects
and retain each panel's generation source and editable export. Equal-width
panels suit equal-weight comparisons. When resizing photos or micrographs,
scale the image and its scale bar together and check raster DPI at placement size.

## patchwork Basics

```r
library(patchwork)

p1 <- ggplot(df, aes(x, y)) + geom_point()
p2 <- ggplot(df, aes(group, value)) + geom_boxplot()
p3 <- ggplot(df, aes(x)) + geom_histogram()

# Horizontal
p1 + p2 + p3

# Vertical
p1 / p2 / p3

# Mixed layouts
(p1 | p2) / p3
(p1 + p2) / (p3 + p4)
```

## Panel Labels

```r
# Automatic labels
(p1 + p2 + p3) + plot_annotation(tag_levels = 'A')

# Custom labels
(p1 + p2 + p3) + plot_annotation(tag_levels = list(c('A', 'B', 'C')))

# Label styling
(p1 + p2) + plot_annotation(
    tag_levels = 'A',
    tag_prefix = '(',
    tag_suffix = ')',
    theme = theme(plot.tag = element_text(face = 'bold', size = 9))
)
```

## Layout Control

```r
# Width ratios
p1 + p2 + plot_layout(widths = c(2, 1))

# Height ratios
p1 / p2 + plot_layout(heights = c(1, 2))

# Complex grid
layout <- "
AAB
AAB
CCC
"
p1 + p2 + p3 + plot_layout(design = layout)

# Fixed dimensions
p1 + p2 + plot_layout(widths = unit(c(5, 3), 'cm'))
```

## Shared Legends

```r
# Collect legends
(p1 + p2 + p3) + plot_layout(guides = 'collect')

# Position at bottom
(p1 + p2) + plot_layout(guides = 'collect') &
    theme(legend.position = 'bottom')

# Keep individual legends
(p1 + p2) + plot_layout(guides = 'keep')
```

## Inset Plots

```r
# Add inset
p1 + inset_element(p2, left = 0.6, bottom = 0.6, right = 1, top = 1)

# Multiple insets
p1 +
    inset_element(p2, 0.6, 0.6, 1, 1) +
    inset_element(p3, 0.02, 0.6, 0.4, 1)
```

## cowplot Alternative

```r
library(cowplot)

# Simple grid
plot_grid(p1, p2, p3, ncol = 3, labels = 'AUTO', label_size = 9)

# With labels
plot_grid(p1, p2, labels = c('A', 'B'), label_size = 9)

# Relative widths
plot_grid(p1, p2, rel_widths = c(2, 1))

# Nested grids
top_row <- plot_grid(p1, p2, ncol = 2)
bottom_row <- p3
plot_grid(top_row, bottom_row, nrow = 2, labels = c('', 'C'), label_size = 9)
```

## Shared Axes

```r
library(patchwork)

# Same axis limits
(p1 + p2) & xlim(0, 10) & ylim(0, 100)

# Same theme
(p1 + p2 + p3) & publication_theme()

# Same color scale
(p1 + p2) & scale_color_viridis_d()
```

## Empty Spaces

```r
# Add blank panel
p1 + plot_spacer() + p2

# With layout
layout <- "
AB#
CCC
"
p1 + p2 + p3 + plot_layout(design = layout)
```

## Titles and Captions

```r
(p1 + p2 + p3) +
    plot_annotation(
        title = 'Main Title',
        subtitle = 'Subtitle text',
        caption = 'Data source: ...',
        theme = theme(
            plot.title = element_text(face = 'bold', size = 8),
            plot.subtitle = element_text(size = 8, color = 'grey40')
        )
    )
```

## Saving Multi-Panel Figures

In this example a 175 × 65 mm canvas contains two equal-weight panels. Set
`director_root` to the installed directory of `bio-publication-figure-director`.

```r
source(file.path(director_root, "scripts", "publication_style.R"))
p1 <- p1 + publication_theme()
p2 <- p2 + publication_theme()
combined <- (p1 | p2) + plot_annotation(tag_levels = "A")

save_publication_figure(p1, "figure1_a.pdf", 85, 65)
save_publication_figure(p2, "figure1_b.pdf", 85, 65)
save_publication_figure(combined, "figure1.pdf", 175, 65)
save_publication_figure(combined, "figure1.png", 175, 65)
```

## matplotlib GridSpec (Python)

```python
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

fig = plt.figure(figsize=(175 / 25.4, 100 / 25.4), layout='constrained')
gs = GridSpec(2, 3, figure=fig)

ax1 = fig.add_subplot(gs[0, 0])    # Top left
ax2 = fig.add_subplot(gs[0, 1:])   # Top right, spans 2 columns
ax3 = fig.add_subplot(gs[1, :])    # Bottom, spans all columns

# Add plots to each axis
ax1.plot(x, y)
ax2.scatter(x, y)
ax3.bar(x, y)

```

## matplotlib Panel Labels

```python
# Add panel labels
for ax, label in zip([ax1, ax2, ax3], ['A', 'B', 'C']):
    ax.set_title(label, loc='left', fontsize=9, fontweight='bold')
```

## matplotlib Subfigures

```python
# matplotlib 3.4+ subfigures for complex layouts
fig = plt.figure(figsize=(175 / 25.4, 100 / 25.4), layout='constrained')
subfigs = fig.subfigures(1, 2, width_ratios=[2, 1])

axs_left = subfigs[0].subplots(2, 1)
ax_right = subfigs[1].subplots(1, 1)
```

## Publication Export

Make the director's `scripts/` importable and use `matplotlib.rc_context(publication_rc())`
around both plotting and saving.

```python
from publication_style import save_publication_figure

save_publication_figure(fig, 'figure1.pdf', 175, 100)
save_publication_figure(fig, 'figure1.png', 175, 100)
```

## Related Skills

- data-visualization/ggplot2-fundamentals - Individual plots
- reporting/rmarkdown-reports - Figures in documents
- differential-expression/de-visualization - DE-specific plots

## bioSkills Upstream References

Local `SKILL.md` remains the canonical trigger and workflow for this Codex setup. Expanded upstream material from `GPTomics/bioSkills` commit `2fe089dfa64990d79afac39b58a16f074c29e23a` is available at:

- `references/bioSkills-upstream-usage-guide.md` for the converted upstream usage guide.
- `scripts/bioSkills-upstream/` for converted upstream example scripts, when examples exist.

Use the upstream files as supporting references only after reading this local skill first.

---
name: bio-reporting-figure-export
description: "Reporting figure export: Exports publication-ready figures in various formats with proper resolution, sizing, and typography."
metadata:
  tool_type: mixed
  primary_tool: matplotlib
---

## Version Compatibility

Reference examples tested with: ggplot2 3.5+, matplotlib 3.8+

Before using code patterns, verify installed versions match. If versions differ:
- Python: `pip show <package>` then `help(module.function)` to check signatures
- R: `packageVersion('<pkg>')` then `?function_name` to verify parameters

If code throws ImportError, AttributeError, or TypeError, introspect the installed
package and adapt the example to match the actual API rather than retrying.

# Publication-Ready Figure Export

Fix the final width and height before plotting. Follow journal or project
requirements, using the [shared publication style](../bio-publication-figure-director/references/publication-style.md)
for general defaults. The standard is Arial with 9 pt bold panel tags, 8 pt
axis titles, legends and ordinary annotations, and 7 pt axis tick labels. Axis,
curve and error-bar widths are 0.75, 1 and 0.75 pt, respectively.

## PDF and PNG

Export line art and statistical figures as editable PDF. Use a 300 DPI PNG for
preview or when a raster submission is needed. Use `save_publication_figure`
from the director's [R](../bio-publication-figure-director/scripts/publication_style.R)
or [Python](../bio-publication-figure-director/scripts/publication_style.py)
helper, with explicit dimensions in mm. In Python apply `publication_rc()` via
`matplotlib.rc_context()` when creating and saving the plot. In R apply
`publication_theme()` plus explicit linewidths on data layers. Assign margins
within the requested canvas so cropping does not change page dimensions.

When a journal requests TIFF, use its image-mode and compression requirements.
For R plots with the shared font and line settings, render with an appropriate
final-size TIFF device, such as `ragg::agg_tiff`, and verify the file.

## Final artifact checks

- Read PDF page size and inspect embedded fonts and editable text. Inspect
  statistical marks and lines as vectors, using the PDF object view or an
  equivalent check. A font list alone does not establish the state of the artwork.
- Verify pixel dimensions and stored DPI for each raster output. For each
  embedded raster, divide its pixel dimensions by its width and height in inches
  at final placement and use the smaller value. The containing PDF or PNG's
  export setting cannot recover resolution lost in the original raster.
- Open the final figure and inspect readability, overlaps, clipping and
  missing glyphs. For multipanel figures retain the independently editable
  statistical panels, check labels against the caption, and verify that a scale
  bar was transformed with its image.
- Keep categories visually distinct in grayscale or common forms of color
  vision deficiency, and use a consistent encoding across related figures.

## Related Skills

- data-visualization/ggplot2-fundamentals - Creating plots in R
- data-visualization/heatmaps-clustering - Complex visualizations
- data-visualization/multipanel-figures - Figure composition

## bioSkills Upstream References

Local `SKILL.md` remains the canonical trigger and workflow for this Codex setup. Expanded upstream material from `GPTomics/bioSkills` commit `2fe089dfa64990d79afac39b58a16f074c29e23a` is available at:

- `references/bioSkills-upstream-usage-guide.md` for the converted upstream usage guide.
- `scripts/bioSkills-upstream/` for converted upstream example scripts, when examples exist.

Use the upstream files as supporting references only after reading this local skill first.

#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 1L, dir.exists(args[[1L]]))

script_arg <- grep("^--file=", commandArgs(), value = TRUE)
skill_root <- dirname(dirname(normalizePath(sub("^--file=", "", script_arg))))
source(file.path(skill_root, "scripts", "publication_style.R"))
library(ggplot2)
library(patchwork)

# Prefer the actual default when installed. CI hosts can explicitly use a test font.
family <- Sys.getenv("FIGURE_TEST_FONT", unset = "Arial")
if (!family %in% systemfonts::system_fonts()$family) {
  stop("Set FIGURE_TEST_FONT to an installed sans-serif font for this test")
}
pdf_device <- Sys.getenv("FIGURE_TEST_PDF_DEVICE", unset = "cairo")
theme <- publication_theme(family)
stopifnot(theme$plot.title$size == 8, theme$axis.title$size == 8,
          theme$axis.text$size == 7, theme$plot.tag$size == 9,
          theme$legend.text$size == 8,
          isTRUE(all.equal(theme$axis.line$linewidth * ggplot2::.pt * 0.75, 0.75)),
          isTRUE(all.equal(publication_curve_linewidth * ggplot2::.pt * 0.75, 1)),
          isTRUE(all.equal(publication_error_linewidth * ggplot2::.pt * 0.75, 0.75)))

# Identical group values are deliberately preserved.
data <- data.frame(dose = rep(c(0, 10, 20), 2), value = rep(c(2.0, 2.4, 2.2), 2),
                   group = rep(c("Group 1", "Group 2"), each = 3))
original <- data
series <- data[data$group == "Group 1", ]
line_plot <- ggplot(series, aes(dose, value)) +
  geom_line(linewidth = publication_curve_linewidth, colour = "#0072B2") +
  geom_errorbar(aes(ymin = value - 0.15, ymax = value + 0.15),
                linewidth = publication_error_linewidth, width = 1.2) +
  geom_point(size = 1.7, colour = "#0072B2") +
  labs(title = "Dose response", x = "Dose (Gy)", y = "Response") + theme
comparison <- ggplot(data, aes(group, value)) +
  geom_point(colour = "#0072B2", size = 1.7) +
  labs(title = "Identical observations", x = "Group", y = "Response") + theme
combined <- wrap_plots(line_plot, comparison, ncol = 2) +
  plot_annotation(tag_levels = "A")

for (extension in c("pdf", "png")) {
  save_publication_figure(line_plot, file.path(args[[1L]], paste0("r_single.", extension)), 85, 60, pdf_device = pdf_device)
  save_publication_figure(comparison, file.path(args[[1L]], paste0("r_group.", extension)), 85, 60, pdf_device = pdf_device)
  save_publication_figure(combined, file.path(args[[1L]], paste0("r_multi.", extension)), 175, 65, pdf_device = pdf_device)
}
stopifnot(identical(data, original))
cat("Rendered R single and editable multi-panel figures with", family, "\n")

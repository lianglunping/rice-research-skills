#!/usr/bin/env Rscript
# Four measured statistics in genuinely different broad and local windows.
args <- commandArgs(trailingOnly = TRUE)
if (!length(args) %in% c(3L, 4L)) stop("Usage: CONFIG RESULT_DIR FIGURE_DIR [--contract-only]", call. = FALSE)
if (length(args) == 4L && !identical(args[[4]], "--contract-only")) stop("Unknown fourth argument", call. = FALSE)

cfg <- read.delim(args[[1]], check.names = FALSE, stringsAsFactors = FALSE)
C <- setNames(cfg$value, cfg$field)
result_dir <- normalizePath(args[[2]], mustWork = TRUE)
figure_dir <- args[[3]]
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)

required <- c(
  "popgen_all_start", "popgen_all_end", "popgen_filter_start", "popgen_filter_end",
  "popgen_callable_mask", "figure_font_family", "figure_base_font_pt",
  "figure_panel_label_pt", "fig2_final_height_mm", "figure_final_width_mm", "png_dpi"
)
missing <- setdiff(required, names(C))
if (length(missing)) stop("Missing config: ", paste(missing, collapse = ", "), call. = FALSE)

font_family <- C[["figure_font_family"]]
base_font <- as.numeric(C[["figure_base_font_pt"]])
panel_font <- as.numeric(C[["figure_panel_label_pt"]])
# Cairo/base graphics quantizes cex and rendered 13.0 pt as 12.815789 pt in
# the final PDF. A small source margin is paired with direct final-PDF QA.
panel_draw_font <- panel_font + 0.5
dpi <- as.numeric(C[["png_dpi"]])
broad <- c(as.numeric(C[["popgen_all_start"]]), as.numeric(C[["popgen_all_end"]]))
local <- c(as.numeric(C[["popgen_filter_start"]]), as.numeric(C[["popgen_filter_end"]]))
if (any(!is.finite(broad)) || any(!is.finite(local)) || diff(broad) <= diff(local)) {
  stop("Broad/local windows must be finite and genuinely distinct", call. = FALSE)
}

files <- c(Pi = "pi_tidy.tsv", TajimaD = "tajimad_tidy.tsv", Fst = "fst_tidy.tsv", Pi_ratio = "pi_ratio_tidy.tsv")
value_fields <- c(Pi = "pi", TajimaD = "tajima_d", Fst = "weighted_fst", Pi_ratio = "log2_pi_ratio")
y_labels <- c(Pi = "Pi", TajimaD = "Tajima's D", Fst = "Weighted Fst", Pi_ratio = "log2 Pi ratio")
panel_letters <- setNames(letters[1:8], paste(rep(names(files), each = 2), rep(c("broad", "local"), 4), sep = ":"))
series_colors <- c(
  XI = "#D55E00", GJ = "#0072B2", Or = "#009E73",
  XI_vs_GJ = "#7B5AA6", XI_vs_Or = "#D55E00", GJ_vs_Or = "#0072B2"
)
series_lty <- c(XI = 1, GJ = 2, Or = 4, XI_vs_GJ = 1, XI_vs_Or = 2, GJ_vs_Or = 4)
series_pch <- c(XI = 21, GJ = 22, Or = 24, XI_vs_GJ = 21, XI_vs_Or = 22, GJ_vs_Or = 24)

data <- lapply(files, function(file) read.delim(file.path(result_dir, "popgen", file), check.names = FALSE, stringsAsFactors = FALSE))
midpoint <- function(x) {
  if ("MID" %in% names(x)) return(as.numeric(x$MID))
  if (all(c("BIN_START", "BIN_END") %in% names(x))) return((as.numeric(x$BIN_START) + as.numeric(x$BIN_END)) / 2)
  as.numeric(x[[1]])
}
subset_metric <- function(metric, limits) {
  x <- data[[metric]]
  y <- as.numeric(x[[value_fields[[metric]]]])
  z <- midpoint(x)
  keep <- is.finite(z) & is.finite(y) & z >= limits[[1]] & z <= limits[[2]]
  list(x = x[keep, , drop = FALSE], y = y[keep], z = z[keep])
}

contract <- do.call(rbind, lapply(names(files), function(metric) {
  do.call(rbind, lapply(c("broad", "local"), function(scope) {
    limits <- if (scope == "broad") broad else local
    selected <- subset_metric(metric, limits)
    data.frame(
      metric = metric, scope = scope, start = limits[[1]], end = limits[[2]],
      window_count = nrow(selected$x), finite_value_count = length(selected$y),
      callable_mask = C[["popgen_callable_mask"]],
      interpretation = if (C[["popgen_callable_mask"]] == "unavailable") "nominal-window descriptive summary" else "callable-mask-normalized summary"
    )
  }))
}))
dir.create(file.path(result_dir, "plot_data"), recursive = TRUE, showWarnings = FALSE)
write.table(contract, file.path(result_dir, "plot_data", "selection_window_contract.tsv"), sep = "\t", row.names = FALSE, quote = FALSE)
if (length(args) == 4L) quit(save = "no", status = 0)

draw_metric <- function(metric, limits, scope, panel_letter) {
  selected <- subset_metric(metric, limits)
  x <- selected$x
  y <- selected$y
  z <- selected$z / 1e6
  if (!length(y)) stop("No finite ", metric, " windows in requested scope", call. = FALSE)
  group <- if ("group" %in% names(x)) x$group else x$pair_id
  levels <- unique(group)
  x_limits <- limits / 1e6
  plot(
    z, y, type = "n", xlim = x_limits, xaxs = "i", xlab = paste0("Chr", C[["gene_chr_vcf"]], " position (Mb)"),
    ylab = "", axes = FALSE
  )
  axis(1, cex.axis = 1.0)
  axis(2, las = 1, cex.axis = 1.0)
  mtext(y_labels[[metric]], side = 2, line = 4.8, cex = 1.32)
  box(col = "#333333")
  abline(v = as.numeric(C[c("promoter_start", "gene_start", "gene_end")]) / 1e6, col = "#9E9E9E", lty = 3, lwd = 0.7)
  for (index in seq_along(levels)) {
    level <- levels[[index]]
    keep <- group == level
    order_index <- order(z[keep])
    color <- if (level %in% names(series_colors)) series_colors[[level]] else grDevices::hcl.colors(length(levels), "Dark 3")[[index]]
    line_type <- if (level %in% names(series_lty)) series_lty[[level]] else index
    point_shape <- if (level %in% names(series_pch)) series_pch[[level]] else 20 + index
    lines(z[keep][order_index], y[keep][order_index], col = color, lty = line_type, lwd = 1.05)
    marker_stride <- max(1L, ceiling(length(order_index) / 12))
    marker_index <- order_index[seq.int(1L, length(order_index), by = marker_stride)]
    points(z[keep][marker_index], y[keep][marker_index], pch = point_shape, col = color, bg = "white", cex = 0.48, lwd = 0.65)
  }
  if (metric %in% c("TajimaD", "Fst", "Pi_ratio")) abline(h = 0, lty = 2, col = "#666666", lwd = 0.7)
  legend(
    "topright", legend = levels,
    col = vapply(seq_along(levels), function(index) if (levels[[index]] %in% names(series_colors)) series_colors[[levels[[index]]]] else grDevices::hcl.colors(length(levels), "Dark 3")[[index]], character(1)),
    lty = vapply(seq_along(levels), function(index) if (levels[[index]] %in% names(series_lty)) series_lty[[levels[[index]]]] else index, numeric(1)),
    pch = vapply(seq_along(levels), function(index) if (levels[[index]] %in% names(series_pch)) series_pch[[levels[[index]]]] else 20 + index, numeric(1)),
    pt.bg = "white", pt.cex = 0.7, lwd = 1.05, bty = "n", cex = 0.9, seg.len = 1.6
  )
  title(main = paste(y_labels[[metric]], scope), cex.main = 10.5 / base_font, line = 0.55)
  mtext(panel_letter, side = 3, adj = 0, line = 1.15, font = 2, cex = panel_draw_font / base_font)
}

note <- if (C[["popgen_callable_mask"]] == "unavailable") {
  "No callable mask; Pi and Tajima's D are nominal-window descriptive summaries."
} else {
  "Callable-mask-normalized summaries."
}

draw_pair <- function(metric) {
  # mfrow automatically reduces par("cex") for multi-panel layouts. Restore
  # cex=1 after declaring the layout so final PDF text honors base_font.
  par(family = font_family, ps = base_font, mfrow = c(1, 2), cex = 1, mar = c(3.2, 6.0, 2.8, 0.8), oma = c(1.6, 0.2, 0.2, 0.2), mgp = c(2.0, 0.6, 0), tcl = -0.25, cex.lab = 1.32)
  draw_metric(metric, broad, "broad", panel_letters[[paste(metric, "broad", sep = ":")]])
  draw_metric(metric, local, "local", panel_letters[[paste(metric, "local", sep = ":")]])
  mtext(note, side = 1, outer = TRUE, line = 0.35, cex = 0.9, col = "#444444")
}

for (metric in names(files)) {
  for (scope in c("broad", "local")) {
    limits <- if (scope == "broad") broad else local
    stem <- paste0(metric, "_", scope)
    Cairo::CairoPDF(file.path(figure_dir, paste0(stem, ".pdf")), width = 3.30, height = 2.42, family = font_family, pointsize = base_font, bg = "white")
    par(family = font_family, ps = base_font, mar = c(3.2, 6.0, 2.8, 0.8), mgp = c(2.0, 0.6, 0), tcl = -0.25, cex.lab = 1.32)
    draw_metric(metric, limits, scope, panel_letters[[paste(metric, scope, sep = ":")]])
    dev.off()
    Cairo::CairoPNG(file.path(figure_dir, paste0(stem, ".png")), width = 3.30, height = 2.42, units = "in", dpi = dpi, family = font_family, pointsize = base_font, bg = "white")
    par(family = font_family, ps = base_font, mar = c(3.2, 6.0, 2.8, 0.8), mgp = c(2.0, 0.6, 0), tcl = -0.25, cex.lab = 1.32)
    draw_metric(metric, limits, scope, panel_letters[[paste(metric, scope, sep = ":")]])
    dev.off()
  }
  stem <- paste0(metric, "_broad_local")
  Cairo::CairoPDF(file.path(figure_dir, paste0(stem, ".pdf")), width = 6.75, height = 2.56, family = font_family, pointsize = base_font, bg = "white")
  draw_pair(metric)
  dev.off()
  Cairo::CairoPNG(file.path(figure_dir, paste0(stem, ".png")), width = 6.75, height = 2.56, units = "in", dpi = dpi, family = font_family, pointsize = base_font, bg = "white")
  draw_pair(metric)
  dev.off()
}

fig2_width <- as.numeric(C[["figure_final_width_mm"]]) / 25.4
fig2_height <- as.numeric(C[["fig2_final_height_mm"]]) / 25.4
draw_composite <- function() {
  # Base R scales cex to ~0.66 for a 4 x 2 mfrow. The explicit reset is a
  # final-size typography requirement, not a cosmetic enlargement.
  par(family = font_family, ps = base_font, mfrow = c(4, 2), cex = 1, mar = c(3.1, 6.0, 2.8, 0.8), oma = c(1.8, 0.2, 0.2, 0.2), mgp = c(2.0, 0.6, 0), tcl = -0.25, cex.lab = 1.32)
  for (metric in names(files)) {
    draw_metric(metric, broad, "broad", panel_letters[[paste(metric, "broad", sep = ":")]])
    draw_metric(metric, local, "local", panel_letters[[paste(metric, "local", sep = ":")]])
  }
  mtext(note, side = 1, outer = TRUE, line = 0.45, cex = 0.9, col = "#444444")
}
Cairo::CairoPDF(file.path(figure_dir, "Fig2_SelectionScan.pdf"), width = fig2_width, height = fig2_height, family = font_family, pointsize = base_font, bg = "white")
draw_composite()
dev.off()
Cairo::CairoPNG(file.path(figure_dir, "Fig2_SelectionScan.png"), width = fig2_width, height = fig2_height, units = "in", dpi = dpi, family = font_family, pointsize = base_font, bg = "white")
draw_composite()
dev.off()

writeLines(capture.output(sessionInfo()), file.path(result_dir, "logs", "R_sessionInfo_plot_selection_scan_v4.txt"))

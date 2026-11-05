#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3L) stop("Usage: CONFIG RESULT_DIR FIGURE_DIR", call. = FALSE)

cfg <- read.delim(args[[1]], check.names = FALSE, stringsAsFactors = FALSE)
C <- setNames(cfg$value, cfg$field)
result_dir <- normalizePath(args[[2]], mustWork = TRUE)
figure_dir <- args[[3]]
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)

font_family <- C[["figure_font_family"]]
base_font <- as.numeric(C[["figure_base_font_pt"]])
panel_font <- as.numeric(C[["figure_panel_label_pt"]])
# Cairo/base graphics quantizes cex; draw with a 0.5-pt source margin and
# enforce the configured target against the final PDF content stream.
panel_draw_font <- panel_font + 0.5
dpi <- as.numeric(C[["png_dpi"]])
nodes <- read.delim(file.path(result_dir, "tree", "primary_haplotype_nodes.tsv"), check.names = FALSE, stringsAsFactors = FALSE)
edges <- read.delim(file.path(result_dir, "tree", "primary_haplotype_mst_edges.tsv"), check.names = FALSE, stringsAsFactors = FALSE)
ids <- nodes$primary_haplotype_id
n <- length(ids)
if (n < 1L) stop("No major haplotype nodes", call. = FALSE)

population_colors <- c(XI = "#D55E00", GJ = "#0072B2", Or = "#009E73", Undefined = "#777777")

draw_pie_node <- function(center, values, radius, colors) {
  total <- sum(values)
  if (total <= 0) {
    values <- c(0, 0, 0, 1)
    total <- 1
  }
  angles <- c(0, cumsum(values / total) * 2 * pi)
  for (index in seq_along(values)) {
    if (values[[index]] <= 0) next
    theta <- seq(angles[[index]], angles[[index + 1L]], length.out = max(8, ceiling(120 * values[[index]] / total)))
    polygon(
      c(center[[1]], center[[1]] + radius * cos(theta), center[[1]]),
      c(center[[2]], center[[2]] + radius * sin(theta), center[[2]]),
      col = colors[[index]], border = NA
    )
  }
  outline <- seq(0, 2 * pi, length.out = 181)
  lines(center[[1]] + radius * cos(outline), center[[2]] + radius * sin(outline), col = "#222222", lwd = 0.8)
}

draw <- function() {
  par(family = font_family, ps = base_font, mar = c(1.2, 1.2, 2.5, 1.2), xpd = NA)
  theta <- seq(pi / 2, pi / 2 + 2 * pi, length.out = n + 1L)[-(n + 1L)]
  xy <- cbind(cos(theta), 0.82 * sin(theta) + 0.12)
  rownames(xy) <- ids
  plot(xy, type = "n", asp = 1, axes = FALSE, xlab = "", ylab = "", xlim = c(-1.48, 1.60), ylim = c(-1.40, 1.38))
  mtext("b", side = 3, adj = 0, line = 0.45, font = 2, cex = panel_draw_font / base_font)
  title(main = "Major-haplotype MST", cex.main = 10.5 / base_font, line = 1.0)
  if (nrow(edges)) {
    left <- if ("hap_a" %in% names(edges)) edges$hap_a else edges$from_haplotype_id
    right <- if ("hap_b" %in% names(edges)) edges$hap_b else edges$to_haplotype_id
    for (index in seq_len(nrow(edges))) {
      a <- left[[index]]
      b <- right[[index]]
      segments(xy[a, 1], xy[a, 2], xy[b, 1], xy[b, 2], col = "#4D4D4D", lwd = 1.2)
      text(mean(xy[c(a, b), 1]), mean(xy[c(a, b), 2]), edges$distance[[index]], cex = 1.0, col = "#333333")
    }
  }
  maximum <- max(sqrt(as.numeric(nodes$haplotype_chromosome_count)), 1)
  for (index in seq_len(n)) {
    values <- as.numeric(nodes[index, c("XI", "GJ", "Or", "Undefined")])
    radius <- 0.11 + 0.15 * sqrt(as.numeric(nodes$haplotype_chromosome_count[[index]])) / maximum
    draw_pie_node(xy[index, ], values, radius, population_colors)
    text(xy[index, 1], xy[index, 2] - radius - 0.14, ids[[index]], cex = 1.0, font = 2)
  }
  observed <- names(population_colors)[colSums(nodes[, names(population_colors), drop = FALSE]) > 0]
  legend("bottom", inset = c(0, -0.02), legend = observed, fill = population_colors[observed], bty = "n", ncol = 2, title = "Population", cex = 0.95)
}

width_in <- 3.30
height_in <- 2.42
Cairo::CairoPDF(file.path(figure_dir, "major_network.pdf"), width = width_in, height = height_in, family = font_family, pointsize = base_font, bg = "white")
draw()
dev.off()
Cairo::CairoPNG(file.path(figure_dir, "major_network.png"), width = width_in, height = height_in, units = "in", dpi = dpi, family = font_family, pointsize = base_font, bg = "white")
draw()
dev.off()

writeLines(capture.output(sessionInfo()), file.path(result_dir, "logs", "R_sessionInfo_plot_haplotype_network_v10.txt"))

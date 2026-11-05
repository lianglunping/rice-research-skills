#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3L) stop("Usage: CONFIG RESULT_DIR FIGURE_DIR", call. = FALSE)
if (!requireNamespace("rnaturalearth", quietly = TRUE) || !requireNamespace("sf", quietly = TRUE)) {
  stop("rnaturalearth and sf from the existing publication environment are required", call. = FALSE)
}

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
data <- read.delim(file.path(result_dir, "map", "primary_haplotype_area_centroid_counts.tsv"), check.names = FALSE, stringsAsFactors = FALSE)
ids <- strsplit(C[["frozen_major_haplotype_ids"]], ",", fixed = TRUE)[[1]]
data <- data[data$primary_haplotype_id %in% ids & is.finite(data$longitude) & is.finite(data$latitude), , drop = FALSE]
palette <- setNames(c("#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#6A3D9A", "#777777")[seq_along(ids)], ids)
haplotype_pch <- setNames(c(21, 22, 24, 23, 25, 21, 22, 24)[seq_along(ids)], ids)

draw <- function() {
  par(family = font_family, ps = base_font, mar = c(3.0, 3.2, 3.1, 0.5), mgp = c(1.8, 0.55, 0), tcl = -0.25, xaxs = "i", yaxs = "i")
  world <- rnaturalearth::ne_countries(scale = "medium", returnclass = "sf")
  plot(sf::st_geometry(world), col = "#F2F2F2", border = "#B5B5B5", xlim = c(-180, 180), ylim = c(-60, 85), axes = FALSE)
  axis(1, at = c(-120, 0, 120), labels = c("-120", "0", "120"))
  axis(2, at = c(-30, 0, 30, 60), labels = c("-30", "0", "30", "60"), las = 1)
  box(col = "#777777")
  mtext("d", side = 3, adj = 0, line = 1.35, font = 2, cex = panel_draw_font / base_font)
  title(main = "Original Area centroids", cex.main = 10.5 / base_font, line = 1.4)
  mtext("Area centroids; not sampling coordinates", side = 3, line = 0.15, cex = 0.9, col = "#444444")
  mtext("Longitude", side = 1, line = 1.75)
  mtext("Latitude", side = 2, line = 1.9)
  for (hap in ids) {
    subset <- data[data$primary_haplotype_id == hap, , drop = FALSE]
    points(
      subset$longitude, subset$latitude, pch = haplotype_pch[[hap]], bg = palette[[hap]], col = "#333333",
      cex = pmax(0.45, pmin(2.2, 0.42 + sqrt(as.numeric(subset$haplotype_chromosome_count)) / 7)), lwd = 0.35
    )
  }
  legend("bottomleft", legend = ids, pt.bg = palette[ids], pch = haplotype_pch[ids], bty = "n", title = "Major haplotype", cex = 0.9, pt.cex = 1.0)
}

width_in <- 3.30
height_in <- 2.42
Cairo::CairoPDF(file.path(figure_dir, "major_area_map.pdf"), width = width_in, height = height_in, family = font_family, pointsize = base_font, bg = "white")
draw()
dev.off()
Cairo::CairoPNG(file.path(figure_dir, "major_area_map.png"), width = width_in, height = height_in, units = "in", dpi = dpi, family = font_family, pointsize = base_font, bg = "white")
draw()
dev.off()

writeLines(capture.output(sessionInfo()), file.path(result_dir, "logs", "R_sessionInfo_plot_hap_map_v10.txt"))

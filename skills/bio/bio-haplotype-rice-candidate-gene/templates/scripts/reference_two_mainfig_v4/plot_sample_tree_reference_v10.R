#!/usr/bin/env Rscript
suppressPackageStartupMessages({
  library(ape)
  library(Cairo)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3L) stop("Usage: CONFIG RESULT_DIR FIGURE_DIR", call. = FALSE)
cfg_tbl <- read.delim(args[[1]], check.names = FALSE, stringsAsFactors = FALSE)
cfg <- setNames(cfg_tbl$value, cfg_tbl$field)
result_dir <- normalizePath(args[[2]], mustWork = TRUE)
figure_dir <- args[[3]]
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)

required <- c(
  "gene_id", "tree_basename", "expected_complete_accessions", "png_dpi",
  "tree_ring_gap_fraction", "tree_ring_point_size", "tree_branch_linewidth",
  "expected_tree_XI_accessions", "expected_tree_GJ_accessions",
  "expected_tree_Or_accessions", "expected_tree_Undefined_accessions",
  "figure_font_family", "figure_base_font_pt", "figure_panel_label_pt"
)
missing <- setdiff(required, names(cfg))
if (length(missing)) stop("Missing tree config fields: ", paste(missing, collapse = ", "), call. = FALSE)

font_family <- cfg[["figure_font_family"]]
base_font <- as.numeric(cfg[["figure_base_font_pt"]])
panel_font <- as.numeric(cfg[["figure_panel_label_pt"]])
# Cairo/base graphics quantizes cex; draw with a 0.5-pt source margin and
# enforce the configured target against the final PDF content stream.
panel_draw_font <- panel_font + 0.5
tree_path <- file.path(result_dir, "tree", paste0(cfg[["tree_basename"]], "_1ibs_RapidNJ.newick"))
annotation_path <- file.path(result_dir, "plot_data", "sample_tree_reference_annotation.tsv")
tree <- reorder.phylo(ladderize(read.tree(tree_path)), order = "postorder")
tree$tip.label <- gsub("^'|'$", "", tree$tip.label)
annotation <- read.delim(annotation_path, check.names = FALSE, stringsAsFactors = FALSE)
annotation <- annotation[, c("sample_id", "population_group", "major_diplotype", "raw_major_diplotype")]

expected_tips <- as.integer(cfg[["expected_complete_accessions"]])
if (length(tree$tip.label) != expected_tips || nrow(annotation) != expected_tips ||
    anyDuplicated(tree$tip.label) || anyDuplicated(annotation$sample_id) ||
    !setequal(tree$tip.label, annotation$sample_id)) {
  stop("Tree tips do not equal the retained-accession annotation set.", call. = FALSE)
}

population_colors <- c(XI = "#C8523B", GJ = "#3B78A3", Or = "#2D8C73", Undefined = "#595959")
population_lty <- c(XI = 1, GJ = 2, Or = 4, Undefined = 3)
population_labels <- c(XI = "XI (indica)", GJ = "GJ (japonica)", Or = "Or (O. rufipogon)", Undefined = "Undefined")
observed_counts <- table(factor(annotation$population_group, levels = names(population_colors)))
expected_counts <- c(
  XI = as.integer(cfg[["expected_tree_XI_accessions"]]),
  GJ = as.integer(cfg[["expected_tree_GJ_accessions"]]),
  Or = as.integer(cfg[["expected_tree_Or_accessions"]]),
  Undefined = as.integer(cfg[["expected_tree_Undefined_accessions"]])
)
if (!identical(as.integer(observed_counts), unname(expected_counts))) {
  stop("Tree population counts differ from the frozen retained-cohort contract.", call. = FALSE)
}
observed_groups <- names(expected_counts)[expected_counts > 0]

# Determine pure-group branches from descendant tips. This is the same
# biological annotation used by the prior ggtree implementation, but ape's
# fan renderer avoids a multi-minute 8k-tip ggplot build.
n_tip <- length(tree$tip.label)
n_node <- n_tip + tree$Nnode
group_counts <- matrix(0L, nrow = n_node, ncol = length(population_colors), dimnames = list(NULL, names(population_colors)))
tip_groups <- annotation$population_group[match(tree$tip.label, annotation$sample_id)]
for (index in seq_len(n_tip)) {
  if (tip_groups[[index]] %in% colnames(group_counts)) group_counts[index, tip_groups[[index]]] <- 1L
}
for (index in seq_len(nrow(tree$edge))) {
  group_counts[tree$edge[index, 1L], ] <- group_counts[tree$edge[index, 1L], ] + group_counts[tree$edge[index, 2L], ]
}
node_group <- apply(group_counts, 1L, function(value) {
  present <- names(value)[value > 0]
  if (length(present) == 1L) present else NA_character_
})
edge_group <- node_group[tree$edge[, 2L]]
edge_colors <- ifelse(is.na(edge_group), "#B7B7B7", population_colors[edge_group])
edge_lty <- ifelse(is.na(edge_group), 1, population_lty[edge_group])
branch_annotation <- data.frame(
  parent = tree$edge[, 1L], node = tree$edge[, 2L], branch_group = ifelse(is.na(edge_group), "Mixed", edge_group),
  XI_descendants = group_counts[tree$edge[, 2L], "XI"],
  GJ_descendants = group_counts[tree$edge[, 2L], "GJ"],
  Or_descendants = group_counts[tree$edge[, 2L], "Or"],
  Undefined_descendants = group_counts[tree$edge[, 2L], "Undefined"],
  stringsAsFactors = FALSE
)
write.table(branch_annotation, file.path(result_dir, "plot_data", "tree_branch_group_annotation.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)

tip_annotation <- annotation[match(tree$tip.label, annotation$sample_id), ]
diplotypes <- sort(unique(tip_annotation$major_diplotype))
base_palette <- c("#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#6A3D9A", "#8C564B", "#17BECF", "#BCBD22", "#9467BD", "#1B9E77")
diplotype_colors <- if (length(diplotypes) <= length(base_palette)) base_palette[seq_along(diplotypes)] else grDevices::hcl.colors(length(diplotypes), "Dark 3")
names(diplotype_colors) <- diplotypes
if ("Other diplotypes" %in% diplotypes) diplotype_colors[["Other diplotypes"]] <- "#D3D3D3"
if ("Other/Other" %in% diplotypes) diplotype_colors[["Other/Other"]] <- "#BDBDBD"

plot_tree <- tree
plot_tree$edge.length <- rep(1, nrow(plot_tree$edge))
maximum_depth <- max(node.depth.edgelength(plot_tree)[seq_len(n_tip)])

draw <- function() {
  par(family = font_family, ps = base_font, mar = c(0.8, 0.8, 3.0, 8.2), xpd = NA)
  plot.phylo(
    plot_tree, type = "fan", use.edge.length = TRUE, show.tip.label = FALSE,
    edge.color = edge_colors, edge.lty = edge_lty, edge.width = as.numeric(cfg[["tree_branch_linewidth"]]),
    x.lim = c(-maximum_depth * 1.08, maximum_depth * 1.56),
    y.lim = c(-maximum_depth * 1.10, maximum_depth * 1.10), no.margin = FALSE
  )
  state <- get("last_plot.phylo", envir = .PlotPhyloEnv)
  tip_x <- state$xx[seq_len(n_tip)]
  tip_y <- state$yy[seq_len(n_tip)]
  tip_radius <- sqrt(tip_x^2 + tip_y^2)
  ring_radius <- max(tip_radius) * (1 + as.numeric(cfg[["tree_ring_gap_fraction"]]))
  ring_x <- tip_x / tip_radius * ring_radius
  ring_y <- tip_y / tip_radius * ring_radius
  points(
    ring_x, ring_y, pch = 21, bg = diplotype_colors[tip_annotation$major_diplotype],
    col = NA, cex = as.numeric(cfg[["tree_ring_point_size"]])
  )
  mtext("c", side = 3, adj = 0, line = 1.45, font = 2, cex = panel_draw_font / base_font)
  title(main = "All-accession local IBS/NJ tree", cex.main = 10.5 / base_font, line = 1.15)
  mtext(
    paste0("All ", format(expected_tips, big.mark = ","), " retained accessions; outer ring: major diplotype; radial branch lengths not to scale"),
    side = 3, line = 0.10, cex = 0.9, col = "#444444"
  )
  legend(
    x = maximum_depth * 1.06, y = maximum_depth * 0.70, legend = population_labels[observed_groups],
    col = population_colors[observed_groups], lty = population_lty[observed_groups], lwd = 1.6,
    bty = "n", title = "Rice group", cex = 0.9, seg.len = 1.2
  )
  legend(
    x = maximum_depth * 1.06, y = maximum_depth * 0.08, legend = diplotypes, pt.bg = diplotype_colors[diplotypes],
    pch = 22, pt.cex = 0.95, bty = "n", title = "Major diplotype", cex = 0.90, ncol = if (length(diplotypes) > 6) 2 else 1
  )
  invisible(ring_radius)
}

width_in <- 6.75
height_in <- 4.375
CairoPDF(file.path(figure_dir, "all_accession_tree.pdf"), width = width_in, height = height_in, family = font_family, pointsize = base_font, bg = "white")
ring_radius <- draw()
dev.off()
CairoPNG(file.path(figure_dir, "all_accession_tree.png"), width = width_in, height = height_in, units = "in", dpi = as.numeric(cfg[["png_dpi"]]), family = font_family, pointsize = base_font, bg = "white")
draw()
dev.off()

tip_output <- data.frame(
  sample_id = tip_annotation$sample_id, population_group = tip_annotation$population_group,
  tree_label = tip_annotation$major_diplotype, raw_major_diplotype = tip_annotation$raw_major_diplotype,
  stringsAsFactors = FALSE
)
write.table(tip_output, file.path(result_dir, "plot_data", "tree_tip_major_label.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
geometry <- data.frame(
  metric = c("tree_tip_count", "tree_radius", "ring_radius", "ring_gap_fraction", "displayed_diplotype_count", "renderer"),
  value = c(expected_tips, maximum_depth, ring_radius, cfg[["tree_ring_gap_fraction"]], length(diplotypes), "ape::plot.phylo fan"),
  stringsAsFactors = FALSE
)
write.table(geometry, file.path(result_dir, "plot_data", "tree_ring_geometry.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
writeLines(capture.output(sessionInfo()), file.path(result_dir, "logs", "R_sessionInfo_plot_sample_tree_reference_v10.txt"))

#!/usr/bin/env Rscript
suppressPackageStartupMessages({
  library(ape)
  library(Cairo)
  library(dplyr)
  library(ggplot2)
  library(ggrepel)
  library(ggtree)
  library(igraph)
  library(patchwork)
  library(ragg)
  library(readr)
  library(rnaturalearth)
  library(scales)
  library(scatterpie)
  library(sf)
  library(tidyr)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3L) stop("Usage: plot_publication_composite_v4.R CONFIG RESULT_DIR FIGURE_DIR", call. = FALSE)
config_path <- normalizePath(args[[1]], mustWork = TRUE)
result_dir <- normalizePath(args[[2]], mustWork = TRUE)
figure_dir <- args[[3]]
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)
cfg_tbl <- read_tsv(config_path, show_col_types = FALSE, col_types = "cc")
cfg <- setNames(cfg_tbl$value, cfg_tbl$field)
gene_id <- cfg[["gene_id"]]
font_family <- cfg[["figure_font_family"]]
png_dpi <- as.numeric(cfg[["png_dpi"]])
set.seed(as.integer(cfg[["random_seed"]]))

read_table <- function(path) read_tsv(path, show_col_types = FALSE)
source_result <- normalizePath(cfg[["source_result_dir"]], mustWork = TRUE)
hap_dir <- file.path(source_result, "haplotype")
plot_dir <- file.path(source_result, "plot_data")
tree_dir <- file.path(source_result, "tree")
map_dir <- file.path(source_result, "map")
popgen_dir <- file.path(source_result, "popgen")
output_tree_dir <- file.path(result_dir, "tree")
dir.create(output_tree_dir, recursive = TRUE, showWarnings = FALSE)

display_haps <- read_table(file.path(hap_dir, "display_haplotype_counts_top80.tsv"))
nodes <- read_table(file.path(tree_dir, "display_haplotype_node_table.tsv"))
edges <- read_table(file.path(tree_dir, "display_haplotype_mst_edges.tsv"))
distance_matrix <- read_table(file.path(tree_dir, "display_haplotype_distance_matrix.tsv"))
sites <- read_table(file.path(plot_dir, "display_site_summary_detailed.tsv"))
matrix_all <- read_table(file.path(plot_dir, "display_haplotype_allele_matrix_top80.tsv"))
features <- read_table(file.path(plot_dir, "gene_feature_segments_detailed.tsv"))
map_counts <- read_table(file.path(map_dir, "display_haplotype_area_centroid_counts.tsv"))
pi_tbl <- read_table(file.path(popgen_dir, "pi_tidy.tsv"))
taj_tbl <- read_table(file.path(popgen_dir, "tajimad_tidy.tsv"))
fst_tbl <- read_table(file.path(popgen_dir, "fst_tidy.tsv"))
ratio_tbl <- read_table(file.path(popgen_dir, "pi_ratio_tidy.tsv"))
primary_haps <- read_table(file.path(result_dir, "haplotype", "primary_haplotype_summary.tsv"))
primary_ids <- primary_haps$primary_haplotype_id
primary_matrix_long <- read_table(file.path(result_dir, "plot_data", "primary_variable_allele_matrix_long.tsv"))
primary_sites <- read_table(file.path(result_dir, "plot_data", "primary_variable_site_summary.tsv"))

group_levels <- c("XI", "GJ", "Or", "Undefined")
group_colors <- c(XI = "#D84A5B", GJ = "#3A78B4", Or = "#36A269", Undefined = "#8C8C8C")
feature_colors <- c(
  Promoter = "#5AAEAD", `5UTR` = "#F28E2B", `3UTR` = "#EDC948",
  CDS = "#D1495B", Splice_boundary = "#7B5AA6", Exon_non_CDS = "#B6A2D8",
  Intron = "#B8B8B8", Gene_baseline = "#8A8A8A", Outside = "#D9D9D9"
)
base_colors <- c(A = "#E15759", C = "#4E79A7", G = "#59A14F", T = "#F28E2B", DEL = "#B07AA1", INS = "#76B7B2", REF = "#BDBDBD", InDel = "#76B7B2", Other = "#9C9C9C")
hap_palette_raw <- grDevices::hcl.colors(nrow(display_haps), palette = "Dynamic")
hap_palette_order <- ((seq_along(hap_palette_raw) - 1L) * 31L) %% length(hap_palette_raw) + 1L
hap_colors <- setNames(hap_palette_raw[hap_palette_order], display_haps$display_haplotype_id)
pair_colors <- c(XI_vs_GJ = "#7B5AA6", XI_vs_Or = "#D1495B", GJ_vs_Or = "#2A9D8F")

theme_pub <- theme_classic(base_family = font_family, base_size = 11) +
  theme(
    panel.grid = element_blank(),
    plot.title = element_text(face = "bold", size = 13),
    plot.subtitle = element_text(size = 9, color = "#444444"),
    axis.title = element_text(face = "plain"),
    legend.title = element_text(face = "bold"),
    strip.background = element_rect(fill = "white", color = "black", linewidth = 0.5),
    strip.text = element_text(face = "bold"),
    plot.margin = margin(8, 12, 8, 8)
  )

figure_manifest <- tibble(
  figure_id = character(), figure_kind = character(), parent_figure = character(),
  relative_stem = character(), width_mm = numeric(), height_mm = numeric()
)

save_pair <- function(plot, relative_stem, width = 11, height = 8, kind = "supplementary", parent = "") {
  stem <- file.path(figure_dir, relative_stem)
  dir.create(dirname(stem), recursive = TRUE, showWarnings = FALSE)
  CairoPDF(paste0(stem, ".pdf"), width = width, height = height, family = font_family, onefile = TRUE)
  print(plot)
  dev.off()
  agg_png(paste0(stem, ".png"), width = width, height = height, units = "in", res = png_dpi, background = "white")
  print(plot)
  dev.off()
  figure_manifest <<- bind_rows(figure_manifest, tibble(
    figure_id = basename(relative_stem), figure_kind = kind, parent_figure = parent,
    relative_stem = relative_stem, width_mm = width * 25.4, height_mm = height * 25.4
  ))
  message("[figure] ", relative_stem)
}

gene_title <- function(suffix) bquote(italic(.(gene_id))~.(suffix))

shade_gene <- function() {
  list(
    annotate("rect", xmin = as.numeric(cfg[["promoter_start"]]), xmax = as.numeric(cfg[["promoter_end"]]), ymin = -Inf, ymax = Inf, fill = "#F6BD60", alpha = 0.13),
    annotate("rect", xmin = as.numeric(cfg[["gene_start"]]), xmax = as.numeric(cfg[["gene_end"]]), ymin = -Inf, ymax = Inf, fill = "#5AAEAD", alpha = 0.14)
  )
}

major_plot <- display_haps %>%
  slice_head(n = 20) %>%
  mutate(
    display_haplotype_id = factor(display_haplotype_id, levels = rev(display_haplotype_id)),
    status = if_else(as.character(display_haplotype_id) %in% primary_ids, "Primary joint-threshold set", "Top-80 context")
  ) %>%
  ggplot(aes(x = display_haplotype_id, y = haplotype_chromosome_count, fill = status)) +
  geom_col(width = 0.76) +
  coord_flip() +
  scale_y_log10(labels = label_number(big.mark = ",")) +
  scale_fill_manual(
    values = c("Primary joint-threshold set" = "#2878B5", "Top-80 context" = "#B8B8B8"),
    labels = c("Primary joint-threshold set" = "Primary", "Top-80 context" = "Top-80 context")
  ) +
  labs(
    title = gene_title("phased haplotype chromosome counts"),
    subtitle = "Top 20 by chromosome-copy count; H001-H009 satisfy the joint primary threshold",
    x = "Display haplotype", y = "Haplotype chromosome count (log10 scale)", fill = NULL
  ) +
  theme_pub +
  theme(axis.text.y = element_text(size = 5.5))
save_pair(major_plot, "Fig1_HaplotypeArchitecture/panels/major_haplotype_counts", 10, 8, "main_panel", "Fig1")

graph <- graph_from_data_frame(edges %>% select(hap_a, hap_b, distance), directed = FALSE, vertices = nodes %>% rename(name = display_haplotype_id))
layout <- layout_with_fr(graph, weights = 1 / (E(graph)$distance + 0.25), niter = 3000, grid = "nogrid")
layout_tbl <- tibble(display_haplotype_id = V(graph)$name, x = layout[, 1], y = layout[, 2]) %>%
  left_join(nodes, by = "display_haplotype_id")
edge_plot <- edges %>%
  left_join(layout_tbl %>% select(display_haplotype_id, x, y), by = c("hap_a" = "display_haplotype_id")) %>%
  rename(x_a = x, y_a = y) %>%
  left_join(layout_tbl %>% select(display_haplotype_id, x, y), by = c("hap_b" = "display_haplotype_id")) %>%
  rename(x_b = x, y_b = y) %>%
  mutate(label = paste0("d=", distance))
layout_tbl <- layout_tbl %>%
  mutate(
    radius = rescale(sqrt(haplotype_chromosome_count), to = c(0.006, 0.026) * max(diff(range(x)), diff(range(y)))),
    primary_status = display_haplotype_id %in% primary_ids,
    label_show = if_else(primary_status, display_haplotype_id, "")
  )
edge_plot <- edge_plot %>% mutate(label = if_else(distance > 1, paste0("d=", distance), ""))
network_plot <- ggplot() +
  geom_segment(data = edge_plot, aes(x = x_a, y = y_a, xend = x_b, yend = y_b, linewidth = distance), color = "#5B5B5B", alpha = 0.75, lineend = "round") +
  scale_linewidth_continuous(range = c(0.25, 1.8), name = "Hamming distance") +
  geom_text(data = edge_plot, aes(x = (x_a + x_b) / 2, y = (y_a + y_b) / 2, label = label), family = font_family, size = 1.8, color = "#666666", check_overlap = TRUE) +
  geom_scatterpie(data = filter(layout_tbl, !primary_status), aes(x = x, y = y, r = radius), cols = group_levels, color = "#6F6F6F", linewidth = 0.18) +
  geom_scatterpie(data = filter(layout_tbl, primary_status), aes(x = x, y = y, r = radius), cols = group_levels, color = "black", linewidth = 0.6) +
  geom_text_repel(data = filter(layout_tbl, label_show != ""), aes(x = x, y = y, label = label_show), family = font_family, size = 2.2, min.segment.length = 0, box.padding = 0.15, max.overlaps = Inf) +
  scale_fill_manual(values = group_colors, breaks = group_levels, drop = FALSE) +
  coord_equal(clip = "off") +
  labs(
    title = gene_title("top-80 phased haplotype network"),
    subtitle = "Original pie-node MST grammar; H001-H009 are labelled and outlined",
    fill = "Subgroup"
  ) +
  theme_void(base_family = font_family, base_size = 11) +
  theme(plot.title = element_text(size = 13), plot.subtitle = element_text(size = 9), legend.position = "right", plot.margin = margin(15, 30, 15, 30))
save_pair(network_plot, "Fig1_HaplotypeArchitecture/panels/haplotype_network", 15, 11, "main_panel", "Fig1")

distance_df <- as.data.frame(distance_matrix)
rownames(distance_df) <- distance_df$display_haplotype_id
distance_df$display_haplotype_id <- NULL
distance_df <- distance_df[rownames(distance_df), rownames(distance_df), drop = FALSE]
distance_numeric <- as.matrix(sapply(distance_df, as.numeric))
rownames(distance_numeric) <- rownames(distance_df)
colnames(distance_numeric) <- colnames(distance_df)
nj_tree <- nj(as.dist(distance_numeric))
write.tree(nj_tree, file = file.path(output_tree_dir, "display_haplotype_NJ_tree.newick"))
clusters <- cutree(hclust(as.dist(distance_numeric), method = "average"), k = min(6L, nrow(distance_numeric)))
cluster_groups <- split(names(clusters), clusters)
grouped_tree <- groupOTU(nj_tree, cluster_groups, group_name = "nj_cluster")
cluster_palette <- setNames(grDevices::hcl.colors(length(cluster_groups), "Dark 3"), as.character(seq_along(cluster_groups)))
tree_tip_meta <- nodes %>% transmute(label = display_haplotype_id, haplotype_chromosome_count)
tree_plot <- (ggtree(grouped_tree, layout = "circular", branch.length = "none", aes(color = factor(nj_cluster)), linewidth = 0.7) %<+% tree_tip_meta) +
  scale_color_manual(values = c(`0` = "#7A7A7A", cluster_palette), na.value = "#7A7A7A", guide = "none") +
  geom_tippoint(aes(size = sqrt(haplotype_chromosome_count)), color = "#202020", alpha = 0.65) +
  scale_size_continuous(range = c(0.4, 2.5), trans = "log10", guide = "none") +
  labs(
    title = gene_title("neighbor-joining tree"),
    subtitle = "Unique top-80 phased haplotypes; NJ topology from SNP+InDel Hamming distances; branch lengths not to scale"
  ) +
  theme_void(base_family = font_family, base_size = 11) +
  theme(plot.title = element_text(size = 13), plot.subtitle = element_text(size = 9), plot.margin = margin(20, 20, 20, 20))
save_pair(tree_plot, "Supplementary/FigS1_NJTree", 12, 12, "supplementary", "")
write_tsv(tibble(display_haplotype_id = names(clusters), nj_cluster = as.integer(clusters)), file.path(output_tree_dir, "display_haplotype_NJ_cluster.tsv"))

feature_rects <- features %>% filter(feature_class != "Gene_baseline") %>% mutate(ymin = if_else(feature_class == "Promoter", -0.20, -0.28), ymax = if_else(feature_class == "Promoter", 0.20, 0.28))
gene_baseline <- features %>% filter(feature_class == "Gene_baseline")

gene_variant_plot <- function(flag, title_text, x_start = as.numeric(cfg[["analysis_start"]]), x_end = as.numeric(cfg[["analysis_end"]])) {
  variant_data <- sites %>% filter(.data[[flag]] == TRUE) %>% arrange(POS) %>% mutate(stem_height = 0.72 + (row_number() %% 3) * 0.12)
  visible_features <- feature_rects %>%
    filter(end >= x_start, start <= x_end) %>%
    mutate(start = pmax(start, x_start), end = pmin(end, x_end))
  visible_baseline <- gene_baseline %>%
    filter(end >= x_start, start <= x_end) %>%
    mutate(start = pmax(start, x_start), end = pmin(end, x_end))
  ggplot() +
    geom_segment(data = visible_baseline, aes(x = start, xend = end, y = 0, yend = 0), color = "#595959", linewidth = 3.0, lineend = "butt") +
    geom_rect(data = visible_features, aes(xmin = start, xmax = end, ymin = ymin, ymax = ymax, fill = feature_class), color = "#333333", linewidth = 0.22) +
    geom_segment(data = variant_data, aes(x = POS, xend = POS, y = 0.30, yend = stem_height, color = detailed_feature_class), linewidth = 0.35, alpha = 0.9) +
    geom_point(data = variant_data, aes(x = POS, y = stem_height, color = detailed_feature_class, shape = variant_type), size = 1.7) +
    scale_fill_manual(values = feature_colors, drop = FALSE) +
    scale_color_manual(values = feature_colors, drop = FALSE) +
    scale_shape_manual(values = c(SNP = 16, InDel = 15)) +
    scale_x_continuous(labels = label_number(big.mark = ","), expand = expansion(mult = c(0.01, 0.01))) +
    coord_cartesian(xlim = c(x_start, x_end), ylim = c(-0.42, 1.18), clip = "off") +
    labs(
      title = title_text,
      subtitle = paste0("Primary transcript; ", sum(sites[[flag]]), " displayed post-QC SNP+InDel sites"),
      x = paste0("Position on chromosome ", cfg[["gene_chr_vcf"]], " (bp)"),
      y = NULL, color = "Variant feature", fill = "Gene feature", shape = "Variant type"
    ) +
    theme_pub +
    theme(axis.text.y = element_blank(), axis.ticks.y = element_blank(), axis.line.y = element_blank(), legend.position = "bottom")
}

var_gene_plot <- gene_variant_plot("display_in_focus", gene_title("gene model and informative functional variants"))
save_pair(var_gene_plot, "Fig1_HaplotypeArchitecture/panels/var_gene", 16, 7, "main_panel", "Fig1")
var_gene_all_plot <- gene_variant_plot("display_in_all", gene_title("gene model and all post-QC variants"))
save_pair(var_gene_all_plot, "Supplementary/FigS2_var_gene_all", 18, 8, "supplementary", "")
cds_limits <- range(features$start[features$feature_class == "CDS"], features$end[features$feature_class == "CDS"])
var_gene_cds_plot <- gene_variant_plot("display_in_cds", gene_title("CDS variants"), cds_limits[1], cds_limits[2])
save_pair(var_gene_cds_plot, "Supplementary/FigS3_var_gene_cds", 14, 7, "supplementary", "")
var_gene_promoter_plot <- gene_variant_plot("display_in_promoter", gene_title("promoter variants"), as.numeric(cfg[["promoter_start"]]), as.numeric(cfg[["promoter_end"]]))
save_pair(var_gene_promoter_plot, "Supplementary/FigS4_var_gene_promoter", 12, 7, "supplementary", "")

matrix_plot <- function(flag, title_text, show_text = FALSE) {
  selected_sites <- sites %>% filter(.data[[flag]] == TRUE) %>% arrange(POS)
  site_ids <- selected_sites$variant_index
  data <- matrix_all %>%
    filter(variant_index %in% site_ids) %>%
    mutate(
      display_haplotype_id = factor(display_haplotype_id, levels = rev(display_haps$display_haplotype_id)),
      site_factor = factor(variant_index, levels = site_ids),
      allele_symbol = case_when(
        allele_display %in% c("A", "C", "G", "T", "DEL") ~ allele_display,
        allele_class %in% c("ALT1", "ALT2+") | variant_type == "InDel" ~ "InDel",
        TRUE ~ "Other"
      ),
      allele_text = case_when(
        allele_display %in% c("A", "C", "G", "T", "DEL") ~ allele_display,
        allele_symbol == "InDel" ~ "INS",
        TRUE ~ "OTHER"
      )
    )
  annotation <- selected_sites %>%
    mutate(site_factor = factor(variant_index, levels = site_ids), y = 1)
  top <- ggplot(annotation, aes(site_factor, y, fill = detailed_feature_class)) +
    geom_tile(color = "white", linewidth = 0.08) +
    scale_fill_manual(values = feature_colors, drop = FALSE) +
    labs(x = NULL, y = NULL, fill = "Site class") +
    theme_void(base_family = font_family, base_size = 9) +
    theme(legend.position = "top", plot.margin = margin(0, 5, 0, 5))
  body <- ggplot(data, aes(site_factor, display_haplotype_id, fill = allele_symbol)) +
    geom_tile(color = "white", linewidth = 0.06) +
    scale_fill_manual(values = base_colors, drop = FALSE) +
    labs(x = NULL, y = "Phased haplotype", fill = "Allele") +
    theme_pub +
    theme(axis.text.x = element_blank(), axis.ticks.x = element_blank(), axis.text.y = element_text(size = 4.5), legend.position = "top", plot.margin = margin(0, 5, 0, 5))
  if (show_text) {
    body <- body + geom_text(aes(label = allele_text), family = font_family, size = 1.05, color = "#1F1F1F", check_overlap = FALSE)
  }
  bottom <- ggplot(annotation, aes(site_factor, 0, color = detailed_feature_class)) +
    geom_segment(aes(xend = site_factor, yend = 0.75), linewidth = 0.25) +
    geom_point(y = 0.75, size = 0.8) +
    scale_color_manual(values = feature_colors, guide = "none") +
    scale_x_discrete(labels = setNames(format(selected_sites$POS, big.mark = ","), selected_sites$variant_index)) +
    coord_cartesian(ylim = c(0, 0.82), clip = "off") +
    labs(x = paste0("Variant position on chromosome ", cfg[["gene_chr_vcf"]]), y = NULL) +
    theme_void(base_family = font_family, base_size = 8) +
    theme(axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5, size = if (nrow(selected_sites) <= 60) 5 else 2.5), axis.title.x = element_text(size = 9), plot.margin = margin(0, 5, 5, 5))
  combined <- top / body / bottom + plot_layout(heights = c(0.7, 10, 1.6)) +
    plot_annotation(
      title = title_text,
      subtitle = paste0(nrow(display_haps), " unique phased haplotypes x ", nrow(selected_sites), " post-QC variant sites"),
      theme = theme(
        text = element_text(family = font_family),
        plot.title = element_text(family = font_family, face = "bold", size = 13),
        plot.subtitle = element_text(family = font_family, size = 9)
      )
    )
  list(plot = combined, n_sites = nrow(selected_sites))
}

primary_matrix_plot <- function(composite = FALSE) {
  selected_sites <- primary_sites %>% arrange(display_site_order) %>% mutate(site_factor = factor(variant_id, levels = variant_id))
  data <- primary_matrix_long %>%
    filter(variant_id %in% selected_sites$variant_id) %>%
    mutate(
      primary_haplotype_id = factor(primary_haplotype_id, levels = rev(primary_ids)),
      site_factor = factor(variant_id, levels = selected_sites$variant_id),
      allele_symbol = if_else(plot_allele %in% names(base_colors), plot_allele, "Other"),
      allele_text = if_else(plot_allele == "INS", "INS", plot_allele)
    )
  annotation <- selected_sites %>% mutate(y = 1)
  top <- ggplot(annotation, aes(site_factor, y, fill = feature_class)) +
    geom_tile(color = "white", linewidth = 0.08) +
    scale_fill_manual(values = feature_colors, drop = FALSE) +
    labs(x = NULL, y = NULL, fill = "Site class") +
    theme_void(base_family = font_family, base_size = 9) +
    theme(
      legend.position = "top",
      legend.title = element_text(size = if (composite) 6 else 9, face = "bold"),
      legend.text = element_text(size = if (composite) 6 else 8),
      legend.key.height = grid::unit(if (composite) 2.2 else 4, "mm"),
      legend.key.width = grid::unit(if (composite) 3.4 else 6, "mm"),
      legend.margin = margin(0, 0, 0, 0),
      plot.margin = margin(0, 5, 0, 5)
    )
  body <- ggplot(data, aes(site_factor, primary_haplotype_id, fill = allele_symbol)) +
    geom_tile(color = "white", linewidth = 0.18) +
    geom_text(aes(label = allele_text), family = font_family, size = if (composite) 1.55 else 2.25, color = "#202020") +
    scale_fill_manual(values = base_colors, drop = FALSE) +
    labs(x = NULL, y = if (composite) "Haplotype" else "Primary haplotype", fill = "Allele") +
    theme_pub +
    theme(
      axis.text.x = element_blank(),
      axis.ticks.x = element_blank(),
      axis.text.y = element_text(size = if (composite) 6 else 8, face = "bold"),
      axis.title.y = element_text(size = if (composite) 7 else 11),
      legend.position = "top",
      legend.title = element_text(size = if (composite) 6 else 9, face = "bold"),
      legend.text = element_text(size = if (composite) 6 else 8),
      legend.key.height = grid::unit(if (composite) 2.2 else 4, "mm"),
      legend.key.width = grid::unit(if (composite) 3.4 else 6, "mm"),
      legend.margin = margin(0, 0, 0, 0),
      plot.margin = margin(0, 5, 0, 5)
    )
  bottom <- ggplot(annotation, aes(site_factor, 0, color = feature_class)) +
    geom_segment(aes(xend = site_factor, yend = 0.75), linewidth = 0.25) +
    geom_point(y = 0.75, size = 0.8) +
    scale_color_manual(values = feature_colors, guide = "none") +
    scale_x_discrete(labels = setNames(format(selected_sites$POS, big.mark = ","), selected_sites$variant_id)) +
    coord_cartesian(ylim = c(0, 0.82), clip = "off") +
    labs(x = paste0("Variant position on chromosome ", cfg[["gene_chr_vcf"]]), y = NULL) +
    theme_void(base_family = font_family, base_size = 8) +
    theme(
      axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5, size = 5),
      axis.title.x = element_text(size = if (composite) 7 else 9),
      plot.margin = margin(0, 5, if (composite) 1 else 5, 5)
    )
  top / body / bottom + plot_layout(heights = if (composite) c(0.55, 7.2, 1.5) else c(0.7, 6, 1.8)) +
    plot_annotation(
      title = if (composite) NULL else gene_title("primary-haplotype informative allele matrix"),
      subtitle = if (composite) NULL else paste0(length(primary_ids), " primary haplotypes x ", nrow(selected_sites), " differentiating sites"),
      theme = theme(plot.title = element_text(family = font_family, size = 13), plot.subtitle = element_text(family = font_family, size = 9))
    )
}

vat_primary_plot <- primary_matrix_plot(composite = FALSE)
save_pair(vat_primary_plot, "Fig1_HaplotypeArchitecture/panels/vat_tab", 16, 9, "main_panel", "Fig1")
vat_all <- matrix_plot("display_in_all", gene_title("complete post-QC allele matrix"), show_text = FALSE)
save_pair(vat_all$plot, "Supplementary/FigS5_vat_tab_all", 24, 15, "supplementary", "")
vat_cds <- matrix_plot("display_in_cds", gene_title("CDS allele matrix"), show_text = FALSE)
save_pair(vat_cds$plot, "Supplementary/FigS6_vat_tab_cds", 20, 15, "supplementary", "")
vat_promoter <- matrix_plot("display_in_promoter", gene_title("promoter allele matrix"), show_text = nrow(sites %>% filter(display_in_promoter == TRUE)) <= 60)
save_pair(vat_promoter$plot, "Supplementary/FigS7_vat_tab_promoter", 14, 15, "supplementary", "")

world <- ne_countries(scale = "medium", returnclass = "sf")
mapped <- map_counts %>%
  mutate(longitude = as.numeric(longitude), latitude = as.numeric(latitude)) %>%
  filter(is.finite(longitude), is.finite(latitude))

top_haps_map <- display_haps$display_haplotype_id[seq_len(min(8L, nrow(display_haps)))]
map_pie <- mapped %>%
  mutate(map_haplotype = if_else(display_haplotype_id %in% top_haps_map, display_haplotype_id, "Other")) %>%
  group_by(original_area, canonical_area, longitude, latitude, map_haplotype) %>%
  summarise(n = sum(haplotype_chromosome_count), .groups = "drop") %>%
  pivot_wider(names_from = map_haplotype, values_from = n, values_fill = 0)
for (column in c(top_haps_map, "Other")) if (!column %in% names(map_pie)) map_pie[[column]] <- 0
map_pie$total <- rowSums(map_pie[, intersect(c(top_haps_map, "Other"), names(map_pie)), drop = FALSE])
map_pie$radius <- rescale(sqrt(map_pie$total), to = c(1.2, 5.0))
top_map_palette <- c("#E15759", "#4E79A7", "#59A14F", "#F28E2B", "#B07AA1", "#76B7B2", "#EDC948", "#9C755F")
map_hap_colors <- c(setNames(top_map_palette[seq_along(top_haps_map)], top_haps_map), Other = "#BAB0AC")
map_all_plot <- ggplot() +
  geom_sf(data = world, fill = "#F4F4F2", color = "#B0B0B0", linewidth = 0.18) +
  geom_scatterpie(data = map_pie, aes(x = longitude, y = latitude, r = radius), cols = names(map_hap_colors), color = "#505050", linewidth = 0.2) +
  scale_fill_manual(values = map_hap_colors, drop = FALSE) +
  coord_sf(xlim = c(-180, 180), ylim = c(-55, 80), expand = FALSE) +
  labs(
    title = gene_title("area-level haplotype distribution"),
    subtitle = "Top eight haplotypes plus Other; points are Original Area centroids, not accession sampling coordinates",
    fill = "Haplotype"
  ) +
  theme_void(base_family = font_family, base_size = 10) +
  theme(plot.title = element_text(size = 13), plot.subtitle = element_text(size = 9), legend.position = "right")
save_pair(map_all_plot, "Supplementary/FigS8_hap_map_all", 16, 8.5, "supplementary", "")

top12 <- primary_ids
by_hap <- mapped %>%
  filter(display_haplotype_id %in% top12) %>%
  group_by(display_haplotype_id, original_area, longitude, latitude) %>%
  summarise(n = sum(haplotype_chromosome_count), .groups = "drop")
map_by_hap_plot <- ggplot() +
  geom_sf(data = world, fill = "#F5F5F3", color = "#C0C0C0", linewidth = 0.12) +
  geom_point(data = by_hap, aes(longitude, latitude, size = n, color = display_haplotype_id), alpha = 0.78) +
  scale_color_manual(values = hap_colors[top12], guide = "none") +
  scale_size_continuous(range = c(0.5, 5.2), name = "Chromosome count") +
  facet_wrap(~display_haplotype_id, ncol = 4) +
  coord_sf(xlim = c(-180, 180), ylim = c(-55, 80), expand = FALSE) +
  labs(title = gene_title("primary-haplotype area profiles"), subtitle = "Original Area centroid approximation; not accession sampling coordinates") +
  theme_void(base_family = font_family, base_size = 8) +
  theme(plot.title = element_text(size = 13), plot.subtitle = element_text(size = 9), strip.text = element_text(face = "bold"), legend.position = "right")
save_pair(map_by_hap_plot, "Fig1_HaplotypeArchitecture/panels/hap_map_by_haplotype", 16, 12, "main_panel", "Fig1")

by_group <- mapped %>%
  group_by(detailed_group, original_area, longitude, latitude) %>%
  summarise(n = sum(haplotype_chromosome_count), .groups = "drop") %>%
  mutate(detailed_group = factor(detailed_group, levels = group_levels))
undefined_note <- tibble(
  detailed_group = factor("Undefined", levels = group_levels),
  longitude = 0, latitude = 10, label = "No retained complete samples"
)
map_facet_plot <- ggplot() +
  geom_sf(data = world, fill = "#F5F5F3", color = "#C0C0C0", linewidth = 0.14) +
  geom_point(data = by_group, aes(longitude, latitude, size = n, color = detailed_group), alpha = 0.76) +
  geom_text(data = undefined_note, aes(longitude, latitude, label = label), family = font_family, size = 3.2, color = "#555555") +
  scale_color_manual(values = group_colors, drop = FALSE, guide = "none") +
  scale_size_continuous(range = c(0.6, 5.5), name = "Chromosome count") +
  facet_wrap(~detailed_group, ncol = 2, drop = FALSE) +
  coord_sf(xlim = c(-180, 180), ylim = c(-55, 80), expand = FALSE) +
  labs(title = gene_title("subgroup area profiles"), subtitle = "Original Area centroid approximation; not accession sampling coordinates") +
  theme_void(base_family = font_family, base_size = 9) +
  theme(plot.title = element_text(size = 13), plot.subtitle = element_text(size = 9), strip.text = element_text(face = "bold"), legend.position = "right")
save_pair(map_facet_plot, "Supplementary/FigS9_hap_map_facet", 15, 10, "supplementary", "")

all_start <- as.numeric(cfg[["popgen_all_start"]])
all_end <- as.numeric(cfg[["popgen_all_end"]])
filter_start <- as.numeric(cfg[["popgen_filter_start"]])
filter_end <- as.numeric(cfg[["popgen_filter_end"]])
chrom_label <- paste("Chromosome", cfg[["gene_chr_vcf"]])

pop_line <- function(data, id_col, value_col, colors, xlim, title, y_label, zero_line = FALSE) {
  plot <- ggplot(data, aes(x = MID, y = .data[[value_col]], color = .data[[id_col]], group = .data[[id_col]])) +
    shade_gene() +
    geom_line(linewidth = 0.72, na.rm = TRUE) +
    scale_color_manual(values = colors, drop = FALSE) +
    scale_x_continuous(limits = xlim, labels = label_number(scale = 1e-6, accuracy = 0.01), expand = expansion(mult = c(0.005, 0.005))) +
    labs(title = title, subtitle = "SNP-only vcftools windows; promoter and gene body are shaded", x = paste0(chrom_label, " position (Mb)"), y = y_label, color = NULL) +
    theme_pub +
    theme(legend.position = "bottom")
  if (zero_line) plot <- plot + geom_hline(yintercept = 0, color = "#666666", linewidth = 0.35, linetype = 2)
  plot
}

pi_plot_tbl <- pi_tbl %>% mutate(neglog10_pi = if_else(pi > 0, -log10(pi), NA_real_))
pi_filter_plot <- pop_line(pi_plot_tbl, "group", "neglog10_pi", group_colors[c("XI", "GJ", "Or")], c(filter_start, filter_end), gene_title("local nucleotide diversity"), expression(-log[10](pi)), FALSE)
pi_all_plot <- pop_line(pi_plot_tbl, "group", "neglog10_pi", group_colors[c("XI", "GJ", "Or")], c(all_start, all_end), gene_title("broad-region nucleotide diversity"), expression(-log[10](pi)), FALSE)
taj_all_plot <- pop_line(taj_tbl, "group", "tajima_d", group_colors[c("XI", "GJ", "Or")], c(all_start, all_end), gene_title("broad-region Tajima's D"), "Tajima's D", TRUE)
taj_filter_plot <- pop_line(taj_tbl, "group", "tajima_d", group_colors[c("XI", "GJ", "Or")], c(filter_start, filter_end), gene_title("local Tajima's D"), "Tajima's D", TRUE)
fst_all_plot <- pop_line(fst_tbl, "pair_id", "weighted_fst", pair_colors, c(all_start, all_end), gene_title("broad-region population differentiation"), "Weighted Fst", TRUE)
fst_filter_plot <- pop_line(fst_tbl, "pair_id", "weighted_fst", pair_colors, c(filter_start, filter_end), gene_title("local population differentiation"), "Weighted Fst", TRUE)
ratio_plot_tbl <- ratio_tbl %>% mutate(log2_ratio = if_else(pi_ratio > 0, log2(pi_ratio), NA_real_))
ratio_filter_plot <- pop_line(ratio_plot_tbl, "pair_id", "log2_ratio", pair_colors, c(filter_start, filter_end), gene_title("local nucleotide-diversity ratios"), expression(log[2](pi[A] / pi[B])), TRUE)

save_pair(pi_all_plot, file.path("Fig2_PopulationGenetics", "panels", paste0(gene_id, "_Pi_all")), 12, 7, "main_panel", "Fig2")
save_pair(pi_filter_plot, file.path("Fig2_PopulationGenetics", "panels", paste0(gene_id, "_Pi")), 10, 7, "main_panel", "Fig2")
save_pair(taj_all_plot, file.path("Fig2_PopulationGenetics", "panels", paste0(gene_id, "_TajimaD_all")), 12, 7, "main_panel", "Fig2")
save_pair(taj_filter_plot, file.path("Fig2_PopulationGenetics", "panels", paste0(gene_id, "_TajimaD_filter")), 10, 7, "main_panel", "Fig2")
save_pair(fst_all_plot, file.path("Fig2_PopulationGenetics", "panels", paste0(gene_id, "_Fst_all")), 12, 7, "main_panel", "Fig2")
save_pair(fst_filter_plot, file.path("Fig2_PopulationGenetics", "panels", paste0(gene_id, "_Fst_filter")), 10, 7, "main_panel", "Fig2")
save_pair(ratio_filter_plot, "Supplementary/FigS10_Pi_ratio", 10, 7, "supplementary", "")

profiles <- bind_rows(
  pi_tbl %>% transmute(MID, series = group, metric = "Pi", value = pi),
  taj_tbl %>% transmute(MID, series = group, metric = "TajimaD", value = tajima_d),
  fst_tbl %>% transmute(MID, series = pair_id, metric = "Fst", value = weighted_fst)
)
profile_colors <- c(group_colors[c("XI", "GJ", "Or")], pair_colors)
profiles_plot <- ggplot(profiles, aes(MID, value, color = series, group = series)) +
  shade_gene() +
  geom_line(linewidth = 0.58, na.rm = TRUE) +
  facet_grid(metric ~ ., scales = "free_y") +
  scale_color_manual(values = profile_colors) +
  scale_x_continuous(limits = c(all_start, all_end), labels = label_number(scale = 1e-6, accuracy = 0.01), expand = expansion(mult = c(0.005, 0.005))) +
  labs(title = paste0(gene_id, " local population-genetic profiles"), subtitle = "Pi, Tajima's D, and Weir-Cockerham weighted Fst from SNP-only vcftools windows", x = paste0("Position on chromosome ", cfg[["gene_chr_vcf"]], " (Mb)"), y = "Statistic value", color = "Group / pair") +
  theme_pub +
  theme(legend.position = "right")

major_composite <- major_plot +
  labs(title = NULL, subtitle = NULL, x = NULL, y = "Chromosome count (log10)") +
  guides(fill = guide_legend(nrow = 2, byrow = TRUE)) +
  theme(
    axis.text.x = element_text(size = 6),
    axis.text.y = element_text(size = 6),
    axis.title.x = element_text(size = 7),
    legend.position = "bottom",
    legend.text = element_text(size = 6),
    legend.key.height = grid::unit(2.4, "mm"),
    legend.key.width = grid::unit(3.8, "mm"),
    legend.margin = margin(0, 0, 0, 0),
    plot.margin = margin(9, 4, 3, 16)
  )
network_composite <- network_plot +
  labs(title = NULL, subtitle = NULL) +
  guides(linewidth = "none", fill = guide_legend(ncol = 1)) +
  theme(
    legend.title = element_text(size = 6.2, face = "bold"),
    legend.text = element_text(size = 6),
    legend.key.height = grid::unit(2.6, "mm"),
    legend.key.width = grid::unit(3.2, "mm"),
    plot.margin = margin(2, 4, 2, 2)
  )
gene_composite <- var_gene_plot +
  labs(title = NULL, subtitle = NULL, shape = NULL) +
  guides(
    shape = "none",
    color = guide_legend(nrow = 1, byrow = TRUE),
    fill = guide_legend(nrow = 1, byrow = TRUE)
  ) +
  theme(
    axis.text.x = element_text(size = 6),
    axis.title.x = element_text(size = 7),
    legend.position = "bottom",
    legend.box = "vertical",
    legend.box.spacing = grid::unit(0, "mm"),
    legend.title = element_text(size = 6, face = "bold"),
    legend.text = element_text(size = 6),
    legend.key.height = grid::unit(2.2, "mm"),
    legend.key.width = grid::unit(3.0, "mm"),
    legend.spacing.x = grid::unit(1.0, "mm"),
    legend.margin = margin(0, 0, 0, 0),
    plot.margin = margin(2, 4, 1, 4)
  )
matrix_composite <- primary_matrix_plot(composite = TRUE)
map_composite <- map_by_hap_plot +
  facet_wrap(~display_haplotype_id, ncol = 5) +
  labs(title = NULL, subtitle = NULL) +
  theme(
    strip.text = element_text(size = 6, face = "bold"),
    legend.title = element_text(size = 6.2, face = "bold"),
    legend.text = element_text(size = 6),
    legend.key.height = grid::unit(2.6, "mm"),
    plot.margin = margin(2, 2, 2, 2)
  )

fig1_composite <- (
  (wrap_elements(full = major_composite) | wrap_elements(full = network_composite)) /
    wrap_elements(full = gene_composite) /
    wrap_elements(full = matrix_composite) /
    wrap_elements(full = map_composite)
) +
  plot_layout(widths = c(0.38, 0.62), heights = c(0.28, 0.18, 0.28, 0.26)) +
  plot_annotation(
    title = gene_title("haplotype architecture"), tag_levels = "a",
    theme = theme(
      text = element_text(family = font_family),
      plot.title = element_text(family = font_family, size = 10, margin = margin(b = 2)),
      plot.tag = element_text(family = font_family, face = "bold", size = 10)
    )
  )
fig1_composite <- fig1_composite & theme(
  text = element_text(family = font_family),
  plot.tag = element_text(family = font_family, face = "bold", size = 10)
)

pi_all_composite <- pi_all_plot + labs(title = "Broad region", subtitle = NULL) + theme(plot.title = element_text(size = 8, face = "bold"), plot.margin = margin(2, 2, 2, 2))
pi_filter_composite <- pi_filter_plot + labs(title = "Local region", subtitle = NULL) + theme(plot.title = element_text(size = 8, face = "bold"), plot.margin = margin(2, 2, 2, 2))
taj_all_composite <- taj_all_plot + labs(title = NULL, subtitle = NULL) + theme(plot.margin = margin(2, 2, 2, 2))
taj_filter_composite <- taj_filter_plot + labs(title = NULL, subtitle = NULL) + theme(plot.margin = margin(2, 2, 2, 2))
fst_all_composite <- fst_all_plot + labs(title = NULL, subtitle = NULL) + theme(plot.margin = margin(2, 2, 2, 2))
fst_filter_composite <- fst_filter_plot + labs(title = NULL, subtitle = NULL) + theme(plot.margin = margin(2, 2, 2, 2))

fig2_composite <- (
  (wrap_elements(full = pi_all_composite) | wrap_elements(full = pi_filter_composite)) /
    (wrap_elements(full = taj_all_composite) | wrap_elements(full = taj_filter_composite)) /
    (wrap_elements(full = fst_all_composite) | wrap_elements(full = fst_filter_composite))
) +
  plot_layout(widths = c(0.5, 0.5), heights = c(1, 1, 1)) +
  plot_annotation(
    title = gene_title("broad and local population-genetic context"), tag_levels = "a",
    theme = theme(
      text = element_text(family = font_family),
      plot.title = element_text(family = font_family, size = 10, margin = margin(b = 2)),
      plot.tag = element_text(family = font_family, face = "bold", size = 10)
    )
  )
fig2_composite <- fig2_composite & theme(
  text = element_text(family = font_family),
  plot.tag = element_text(family = font_family, face = "bold", size = 10)
)

save_pair(
  fig1_composite, "Fig1_HaplotypeArchitecture/Fig1_HaplotypeArchitecture",
  as.numeric(cfg[["fig1_width_mm"]]) / 25.4, as.numeric(cfg[["fig1_height_mm"]]) / 25.4,
  "main_composite", "Fig1"
)
save_pair(
  fig2_composite, "Fig2_PopulationGenetics/Fig2_PopulationGenetics",
  as.numeric(cfg[["fig2_width_mm"]]) / 25.4, as.numeric(cfg[["fig2_height_mm"]]) / 25.4,
  "main_composite", "Fig2"
)

summary_dir <- file.path(result_dir, "summary")
dir.create(summary_dir, recursive = TRUE, showWarnings = FALSE)
write_tsv(figure_manifest, file.path(summary_dir, "figure_manifest.tsv"))
openxlsx::write.xlsx(figure_manifest, file.path(summary_dir, "figure_manifest.xlsx"), overwrite = TRUE)

session <- capture.output(sessionInfo())
writeLines(session, file.path(result_dir, "logs", "R_sessionInfo_plot_publication_composite_v4.txt"))
cat(sprintf("[plot] completed %d figure pairs\n", nrow(figure_manifest)))

#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(ape)
  library(Cairo)
  library(dplyr)
  library(ggplot2)
  library(ggrepel)
  library(ggtree)
  library(ggraph)
  library(igraph)
  library(openxlsx)
  library(patchwork)
  library(ragg)
  library(readr)
  library(scales)
  library(scatterpie)
  library(tidyr)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3) {
  stop("Usage: plot_publication_compact_v3.R CONFIG RESULT_DIR FIGURE_DIR")
}

config_path <- normalizePath(args[[1]], mustWork = TRUE)
result_dir <- normalizePath(args[[2]], mustWork = TRUE)
figure_dir <- args[[3]]
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)

config_table <- read_tsv(config_path, show_col_types = FALSE)
cfg <- setNames(config_table$value, config_table$field)
cfg_num <- function(name) as.numeric(cfg[[name]])
font_family <- cfg[["figure_font_family"]]
base_size <- cfg_num("figure_font_size_pt")
png_dpi <- cfg_num("png_dpi")
gene_id <- cfg[["gene_id"]]
gene_symbol <- cfg[["gene_symbol"]]
analysis_start <- cfg_num("analysis_start")
analysis_end <- cfg_num("analysis_end")
gene_start <- cfg_num("gene_start")
gene_end <- cfg_num("gene_end")
promoter_start <- cfg_num("promoter_start")
promoter_end <- cfg_num("promoter_end")
set.seed(as.integer(cfg[["random_seed"]]))

group_colors <- c(XI = "#D55E00", GJ = "#0072B2", Or = "#009E73", Undefined = "#8A8A8A")
direction_colors <- c(`XI-enriched` = "#D55E00", `GJ-enriched` = "#0072B2")
allele_colors <- c(A = "#009E73", C = "#0072B2", G = "#E69F00", T = "#D55E00", DEL = "#666666", INS = "#984EA3", REF = "#BDBDBD", ALT = "#4D4D4D")
feature_colors <- c(Promoter = "#66C2A5", `5UTR` = "#BDBDBD", CDS = "#222222", `3UTR` = "#BDBDBD", Intron = "#FFFFFF", Splice_boundary = "#E78AC3", Exon_non_CDS = "#BDBDBD")

theme_pub <- function(base = base_size) {
  theme_classic(base_family = font_family, base_size = base) +
    theme(
      text = element_text(family = font_family, colour = "#222222"),
      axis.text = element_text(colour = "#222222"),
      axis.title = element_text(colour = "#222222"),
      plot.title = element_text(size = base + 0.5, face = "plain", margin = margin(b = 4)),
      plot.subtitle = element_text(size = base - 1, colour = "#4D4D4D", margin = margin(b = 5)),
      plot.tag = element_text(family = font_family, face = "bold", size = base + 4),
      legend.title = element_text(size = base - 0.5),
      legend.text = element_text(size = base - 1),
      panel.grid = element_blank(),
      plot.margin = margin(5, 5, 5, 5)
    )
}
theme_set(theme_pub())

read_table <- function(...) read_tsv(file.path(result_dir, ...), show_col_types = FALSE)
primary <- read_table("haplotype", "primary_haplotype_summary.tsv")
all_haplotypes <- read_table("haplotype", "all_haplotype_summary.tsv")
carrier_tests <- read_table("haplotype", "XI_GJ_carrier_tests.tsv")
subgroup_counts <- read_table("haplotype", "primary_haplotype_subgroup_counts.tsv")
subgroup_frequencies <- read_table("haplotype", "primary_haplotype_subgroup_frequencies.tsv")
variable_sites <- read_table("plot_data", "primary_variable_site_summary.tsv")
matrix_long <- read_table("plot_data", "primary_variable_allele_matrix_long.tsv")
gene_features <- read_table("plot_data", "gene_feature_segments_detailed.tsv")
nodes <- read_table("tree", "primary_haplotype_nodes.tsv")
edges <- read_table("tree", "primary_haplotype_mst_edges.tsv")
distance_matrix <- read_table("tree", "primary_haplotype_distance_matrix.tsv")
site_diff <- read_table("popgen", "XI_GJ_site_differentiation.tsv")
pi_data <- read_table("popgen", "pi_tidy.tsv")
tajima_data <- read_table("popgen", "tajimad_tidy.tsv")
fst_data <- read_table("popgen", "fst_tidy.tsv")
map_data_hap <- read_table("map", "primary_haplotype_area_centroid_counts.tsv")

hap_levels <- primary$primary_haplotype_id
subgroup_levels <- c("XI1", "XI2", "XI3", "XI4", "XI5", "GJ1", "GJ2", "GJ3", "GJ4-1", "GJ4-2", "GJ5")
variable_sites <- variable_sites %>%
  arrange(display_site_order) %>%
  mutate(
    site_column = sprintf("S%02d", display_site_order),
    matrix_x = display_site_order,
    gene_x = 0.5 + (POS - analysis_start) / (analysis_end - analysis_start) * n()
  )
site_labels <- setNames(variable_sites$site_column, variable_sites$variant_id)

figure_manifest <- tibble(
  figure_id = character(), figure_kind = character(), parent_figure = character(),
  relative_stem = character(), width_mm = numeric(), height_mm = numeric()
)

save_pair <- function(plot_object, relative_stem, width_mm, height_mm, kind, parent = "") {
  stem <- file.path(figure_dir, relative_stem)
  dir.create(dirname(stem), recursive = TRUE, showWarnings = FALSE)
  CairoPDF(
    file = paste0(stem, ".pdf"), width = width_mm / 25.4, height = height_mm / 25.4,
    family = font_family, onefile = TRUE
  )
  print(plot_object)
  dev.off()
  agg_png(
    filename = paste0(stem, ".png"), width = width_mm, height = height_mm,
    units = "mm", res = png_dpi, background = "white"
  )
  print(plot_object)
  dev.off()
  figure_manifest <<- bind_rows(figure_manifest, tibble(
    figure_id = basename(relative_stem), figure_kind = kind, parent_figure = parent,
    relative_stem = relative_stem, width_mm = width_mm, height_mm = height_mm
  ))
}

short_consequence <- function(x) {
  result <- x
  result[grepl("Promoter", result, fixed = TRUE)] <- "Prom."
  result[grepl("Intron", result, fixed = TRUE)] <- "Intron"
  result[grepl("spanning-deletion", result, fixed = TRUE)] <- "del. span"
  result[grepl("in-frame", result, fixed = TRUE)] <- "in-frame"
  result[grepl("frameshift", result, fixed = TRUE)] <- "frameshift"
  result[grepl("UTR", result, fixed = TRUE)] <- gsub("UTR", " UTR", result[grepl("UTR", result, fixed = TRUE)])
  result[nchar(result) > 12] <- substr(result[nchar(result) > 12], 1, 12)
  result
}

# Fig. 1a: gene model, primary alleles, and detailed subgroup chromosome counts.
n_sites <- nrow(variable_sites)
feature_plot_data <- gene_features %>%
  mutate(
    xmin = 0.5 + (start - analysis_start) / (analysis_end - analysis_start) * n_sites,
    xmax = 0.5 + (end - analysis_start) / (analysis_end - analysis_start) * n_sites,
    ymin = case_when(feature_class == "Promoter" ~ 0.43, feature_class == "Gene_baseline" ~ 0.52, TRUE ~ 0.38),
    ymax = case_when(feature_class == "Promoter" ~ 0.61, feature_class == "Gene_baseline" ~ 0.54, TRUE ~ 0.66)
  )

gene_model_plot <- ggplot() +
  geom_segment(aes(x = 0.5, xend = n_sites + 0.5, y = 0.53, yend = 0.53), linewidth = 0.35, colour = "#333333") +
  geom_rect(
    data = filter(feature_plot_data, feature_class != "Gene_baseline"),
    aes(xmin = xmin, xmax = xmax, ymin = ymin, ymax = ymax, fill = feature_class),
    colour = "#333333", linewidth = 0.2
  ) +
  geom_segment(
    data = variable_sites,
    aes(x = gene_x, xend = matrix_x, y = 0.38, yend = 0.06),
    linewidth = 0.18, colour = "#A6A6A6"
  ) +
  geom_point(data = variable_sites, aes(x = gene_x, y = 0.38), size = 0.8, colour = "#222222") +
  geom_text(
    data = variable_sites,
    aes(x = matrix_x, y = 0.01, label = short_consequence(coding_consequence)),
    angle = 90, hjust = 1, vjust = 0.5, family = font_family, size = 1.55, colour = "#444444"
  ) +
  annotate(
    "text", x = 0.5 + (gene_start + gene_end - 2 * analysis_start) / (2 * (analysis_end - analysis_start)) * n_sites,
    y = 0.83, label = paste0(gene_id, " (", gene_symbol, ")"), family = font_family,
    fontface = "italic", size = 2.6
  ) +
  scale_fill_manual(values = c(Promoter = "#66C2A5", `5UTR` = "#BDBDBD", CDS = "#222222", `3UTR` = "#BDBDBD"), drop = FALSE) +
  coord_cartesian(xlim = c(0.35, n_sites + 0.65), ylim = c(-0.24, 0.95), clip = "off") +
  guides(fill = "none") +
  theme_void(base_family = font_family) +
  theme(plot.margin = margin(4, 3, 0, 22))

matrix_plot_data <- matrix_long %>%
  filter(variant_id %in% variable_sites$variant_id) %>%
  mutate(
    matrix_x = match(variant_id, variable_sites$variant_id),
    primary_haplotype_id = factor(primary_haplotype_id, levels = rev(hap_levels)),
    plot_allele = if_else(plot_allele %in% names(allele_colors), plot_allele, "INS"),
    allele_text_colour = if_else(plot_allele %in% c("G", "REF"), "#222222", "white")
  )

haplotype_matrix_plot <- ggplot(matrix_plot_data, aes(x = matrix_x, y = primary_haplotype_id)) +
  geom_tile(aes(fill = plot_allele), colour = "white", linewidth = 0.35) +
  geom_text(aes(label = plot_allele, colour = allele_text_colour), family = font_family, size = 1.6, fontface = "bold") +
  scale_fill_manual(values = allele_colors, drop = FALSE) +
  scale_colour_identity() +
  scale_x_continuous(
    breaks = seq_len(n_sites), labels = paste(variable_sites$site_column, variable_sites$POS), position = "top",
    expand = expansion(add = 0)
  ) +
  scale_y_discrete(drop = FALSE, expand = expansion(add = 0)) +
  labs(x = NULL, y = NULL, fill = "Allele") +
  theme_pub(base_size - 1) +
  theme(
    axis.line = element_blank(), axis.ticks = element_blank(),
    axis.text.x = element_text(size = base_size - 2, angle = 90, hjust = 0, vjust = 0.5),
    axis.text.y = element_text(size = base_size - 0.5, face = "bold"),
    legend.position = "bottom", legend.key.width = unit(4.5, "mm"),
    plot.margin = margin(0, 3, 2, 22)
  )

count_long <- subgroup_counts %>%
  select(primary_haplotype_id, all_of(subgroup_levels), carrier_accession_count) %>%
  pivot_longer(-primary_haplotype_id, names_to = "column", values_to = "count") %>%
  mutate(
    primary_haplotype_id = factor(primary_haplotype_id, levels = rev(hap_levels)),
    column = factor(column, levels = c(subgroup_levels, "carrier_accession_count")),
    parent_group = case_when(
      grepl("^XI", as.character(column)) ~ "XI",
      grepl("^GJ", as.character(column)) ~ "GJ",
      TRUE ~ "Carrier accessions"
    )
  )
count_labels <- c(setNames(subgroup_levels, subgroup_levels), carrier_accession_count = "Carriers")

subgroup_count_plot <- ggplot(count_long, aes(x = column, y = primary_haplotype_id)) +
  geom_tile(aes(fill = parent_group), colour = "white", linewidth = 0.35, alpha = 0.18) +
  geom_text(aes(label = format(count, big.mark = ",", scientific = FALSE)), family = font_family, size = 1.75) +
  scale_fill_manual(values = c(XI = group_colors[["XI"]], GJ = group_colors[["GJ"]], `Carrier accessions` = "#666666")) +
  scale_x_discrete(labels = count_labels, position = "top", expand = expansion(add = 0)) +
  scale_y_discrete(drop = FALSE, expand = expansion(add = 0)) +
  labs(x = NULL, y = NULL) +
  theme_pub(base_size - 1) +
  theme(
    axis.line = element_blank(), axis.ticks = element_blank(), axis.text.y = element_blank(),
    axis.text.x = element_text(size = base_size - 2, angle = 90, hjust = 0, vjust = 0.5),
    legend.position = "none", plot.margin = margin(0, 5, 2, 0)
  )

count_header_plot <- ggplot() +
  annotate(
    "text", x = 0.5, y = 0.5,
    label = "Detailed-subgroup chromosome-copy counts and carrier accessions",
    family = font_family, size = 2.2, colour = "#333333"
  ) +
  theme_void(base_family = font_family) +
  theme(plot.margin = margin(4, 5, 0, 0))

fig1a_core <- (gene_model_plot | count_header_plot) /
  (haplotype_matrix_plot | subgroup_count_plot) +
  plot_layout(widths = c(0.62, 0.38), heights = c(0.31, 0.69))
fig1a <- fig1a_core

# Fig. 1b: accession-level XI-GJ carrier-rate differences.
carrier_plot_data <- carrier_tests %>%
  mutate(
    primary_haplotype_id = factor(primary_haplotype_id, levels = rev(hap_levels)),
    difference_pp = 100 * rate_difference_XI_minus_GJ,
    low_pp = 100 * rate_difference_CI_low,
    high_pp = 100 * rate_difference_CI_high,
    direction = if_else(difference_pp >= 0, "XI-enriched", "GJ-enriched"),
    q_label = if_else(BH_q < 0.001, "q < 0.001", sprintf("q = %.3f", BH_q))
  )
q_x <- max(carrier_plot_data$high_pp, na.rm = TRUE) + 4
x_min <- min(carrier_plot_data$low_pp, na.rm = TRUE) - 3
x_max <- q_x + 11

fig1b_core <- ggplot(carrier_plot_data, aes(y = primary_haplotype_id)) +
  geom_vline(xintercept = 0, linetype = "dashed", linewidth = 0.35, colour = "#777777") +
  geom_segment(aes(x = low_pp, xend = high_pp, yend = primary_haplotype_id, colour = direction), linewidth = 0.8) +
  geom_point(aes(x = difference_pp, colour = direction), size = 2.4) +
  geom_text(aes(x = q_x, label = q_label), hjust = 0, family = font_family, size = 2.1, colour = "#333333") +
  scale_colour_manual(values = direction_colors) +
  coord_cartesian(xlim = c(x_min, x_max), clip = "off") +
  labs(
    title = "XI-GJ carrier-rate difference",
    subtitle = "Newcombe 95% CI; two-sided Fisher test; BH-adjusted q",
    x = "Carrier-rate difference (percentage points)", y = NULL, colour = NULL
  ) +
  theme_pub(base_size - 0.5) +
  theme(legend.position = "bottom", plot.margin = margin(6, 15, 5, 8))
fig1b <- fig1b_core

# Fig. 1c: normalized detailed-subgroup chromosome frequencies.
subgroup_heatmap_data <- subgroup_frequencies %>%
  mutate(
    primary_haplotype_id = factor(primary_haplotype_id, levels = rev(hap_levels)),
    subgroup = factor(subgroup, levels = subgroup_levels),
    cell_label = case_when(
      is.na(within_subgroup_chromosome_frequency) ~ "NA",
      within_subgroup_chromosome_frequency == 0 ~ "0",
      within_subgroup_chromosome_frequency < 0.001 ~ "<0.1",
      TRUE ~ sprintf("%.1f", 100 * within_subgroup_chromosome_frequency)
    )
  )

fig1c_core <- ggplot(subgroup_heatmap_data, aes(x = subgroup, y = primary_haplotype_id)) +
  geom_tile(aes(fill = within_subgroup_chromosome_frequency), colour = "white", linewidth = 0.35) +
  geom_text(aes(label = cell_label), family = font_family, size = 1.75) +
  scale_fill_viridis_c(
    option = "C", begin = 0.05, end = 0.95, labels = percent_format(accuracy = 1),
    na.value = "#EEEEEE", guide = guide_colourbar(display = "rectangles", nbin = 100)
  ) +
  scale_x_discrete(position = "top", expand = expansion(add = 0)) +
  scale_y_discrete(drop = FALSE, expand = expansion(add = 0)) +
  labs(
    title = "Detailed-subgroup chromosome frequencies",
    subtitle = "Cell labels are percentages; descriptive for retained complete-case accessions",
    x = NULL, y = NULL, fill = "Frequency"
  ) +
  theme_pub(base_size - 0.5) +
  theme(
    axis.line = element_blank(), axis.ticks = element_blank(),
    axis.text.x = element_text(angle = 45, hjust = 0, vjust = 0.5),
    legend.position = "bottom", plot.margin = margin(6, 5, 5, 8)
  )
fig1c <- fig1c_core

fig1 <- wrap_elements(full = fig1a) / (wrap_elements(full = fig1b) | wrap_elements(full = fig1c)) +
  plot_layout(heights = c(0.64, 0.36), widths = c(0.5, 0.5)) +
  plot_annotation(tag_levels = "a")

fig1_dir <- "Fig1_HaplotypeArchitecture_XI_GJ"
save_pair(fig1a, file.path(fig1_dir, "panels", "Fig1a_HaplotypeMatrix"), 180, 128, "main_panel", "Fig1")
save_pair(fig1b, file.path(fig1_dir, "panels", "Fig1b_XI_GJ_CarrierDifference"), 90, 88, "main_panel", "Fig1")
save_pair(fig1c, file.path(fig1_dir, "panels", "Fig1c_SubgroupChromosomeFrequency"), 90, 88, "main_panel", "Fig1")
save_pair(fig1, file.path(fig1_dir, "Fig1_HaplotypeArchitecture_XI_GJ"), cfg_num("fig1_width_mm"), cfg_num("fig1_height_mm"), "main_composite", "Fig1")

# Fig. 2a: minimum-spanning haplotype network.
network_graph <- graph_from_data_frame(
  edges %>% transmute(from = hap_a, to = hap_b, distance = as.numeric(distance)),
  directed = FALSE,
  vertices = nodes %>% transmute(name = primary_haplotype_id)
)
root_index <- which(V(network_graph)$name == "H001")
tree_layout <- layout_as_tree(network_graph, root = root_index, circular = FALSE)
network_layout <- cbind(
  rescale(max(tree_layout[, 2]) - tree_layout[, 2], to = c(0.08, 0.92)),
  rescale(tree_layout[, 1], to = c(0.10, 0.90))
)
network_nodes <- nodes %>%
  mutate(name = primary_haplotype_id) %>%
  left_join(tibble(name = V(network_graph)$name, x = network_layout[, 1], y = network_layout[, 2]), by = "name") %>%
  mutate(total = XI + GJ + Or + Undefined, radius = 0.035 + 0.075 * sqrt(total / max(total)))
network_edges <- as_data_frame(network_graph, what = "edges") %>%
  left_join(network_nodes %>% select(name, x_from = x, y_from = y), by = c("from" = "name")) %>%
  left_join(network_nodes %>% select(name, x_to = x, y_to = y), by = c("to" = "name")) %>%
  mutate(x_mid = (x_from + x_to) / 2, y_mid = (y_from + y_to) / 2)

fig2a_core <- ggplot() +
  geom_segment(
    data = network_edges,
    aes(x = x_from, y = y_from, xend = x_to, yend = y_to),
    linewidth = 0.55, colour = "#777777"
  ) +
  geom_label(
    data = network_edges, aes(x = x_mid, y = y_mid, label = distance),
    family = font_family, size = 1.8, linewidth = 0, fill = alpha("white", 0.85)
  ) +
  geom_scatterpie(
    data = network_nodes, aes(x = x, y = y, r = radius),
    cols = c("XI", "GJ", "Or", "Undefined"), colour = "#333333", linewidth = 0.25
  ) +
  geom_text(
    data = network_nodes, aes(x = x, y = y + radius + 0.028, label = primary_haplotype_id),
    family = font_family, fontface = "bold", size = 2.4
  ) +
  scale_fill_manual(values = group_colors, breaks = names(group_colors)) +
  coord_equal(xlim = c(-0.02, 1.02), ylim = c(-0.02, 1.04), clip = "off") +
  labs(
    title = "Primary-haplotype network",
    subtitle = "Minimum spanning tree\nEdge labels: full-pattern Hamming distance",
    fill = "Group"
  ) +
  theme_void(base_family = font_family, base_size = base_size) +
  theme(
    plot.title = element_text(family = font_family, size = base_size + 0.5, margin = margin(b = 3, l = 7)),
    plot.subtitle = element_text(family = font_family, size = base_size - 1, colour = "#4D4D4D", margin = margin(l = 7)),
    legend.position = "bottom", legend.title = element_text(size = base_size - 0.5),
    legend.text = element_text(size = base_size - 1), plot.margin = margin(8, 8, 5, 8)
  )
fig2a <- fig2a_core

# Fig. 2b: target-interval site differentiation.
target_sites <- site_diff %>%
  filter(in_analysis_interval == "TRUE", passes_pairwise_max_missing_0.80 == "TRUE") %>%
  arrange(POS)

shade_locus <- function(plot_object, x_scale = 1) {
  plot_object +
    annotate("rect", xmin = promoter_start / x_scale, xmax = promoter_end / x_scale, ymin = -Inf, ymax = Inf, fill = "#FEE8C8", alpha = 0.42) +
    annotate("rect", xmin = gene_start / x_scale, xmax = gene_end / x_scale, ymin = -Inf, ymax = Inf, fill = "#DDEFEF", alpha = 0.42)
}

delta_plot <- ggplot(target_sites, aes(x = POS, y = delta_AF_XI_minus_GJ))
delta_plot <- shade_locus(delta_plot) +
  geom_hline(yintercept = 0, linewidth = 0.3, colour = "#777777") +
  geom_segment(aes(xend = POS, y = 0, yend = delta_AF_XI_minus_GJ, colour = delta_AF_XI_minus_GJ >= 0), linewidth = 0.45) +
  geom_point(aes(colour = delta_AF_XI_minus_GJ >= 0), size = 1.25) +
  scale_colour_manual(values = c(`TRUE` = group_colors[["XI"]], `FALSE` = group_colors[["GJ"]]), guide = "none") +
  scale_x_continuous(labels = label_comma(), limits = c(analysis_start, analysis_end), expand = c(0, 0)) +
  labs(x = NULL, y = "Delta AF (XI-GJ)", title = "Site-level allele-frequency contrast") +
  theme_pub(base_size - 1) +
  theme(axis.text.x = element_blank(), axis.ticks.x = element_blank(), plot.margin = margin(3, 5, 1, 10))

fst_finite <- target_sites %>% filter(is.finite(site_Weir_Cockerham_Fst))
fst_plot <- ggplot(fst_finite, aes(x = POS, y = site_Weir_Cockerham_Fst))
fst_plot <- shade_locus(fst_plot) +
  geom_hline(yintercept = 0, linewidth = 0.3, colour = "#777777") +
  geom_segment(aes(xend = POS, y = 0, yend = site_Weir_Cockerham_Fst), linewidth = 0.45, colour = "#5E3C99") +
  geom_point(size = 1.25, colour = "#5E3C99") +
  scale_x_continuous(labels = label_comma(), limits = c(analysis_start, analysis_end), expand = c(0, 0)) +
  labs(x = paste0("Chromosome ", cfg[["gene_chr_vcf"]], " position (bp)"), y = "Per-site Fst", title = "Weir-Cockerham per-site Fst") +
  theme_pub(base_size - 1) +
  theme(plot.margin = margin(1, 5, 3, 10))

model_strip <- ggplot() +
  geom_segment(aes(x = analysis_start, xend = analysis_end, y = 0, yend = 0), linewidth = 0.35, colour = "#333333") +
  geom_rect(
    data = filter(gene_features, feature_class != "Gene_baseline"),
    aes(xmin = start, xmax = end, ymin = -0.15, ymax = 0.15, fill = feature_class),
    colour = "#333333", linewidth = 0.2
  ) +
  annotate("text", x = (gene_start + gene_end) / 2, y = 0.38, label = gene_id, family = font_family, fontface = "italic", size = 2.1) +
  scale_fill_manual(values = c(Promoter = "#F4A261", `5UTR` = "#BDBDBD", CDS = "#222222", `3UTR` = "#BDBDBD"), guide = "none") +
  coord_cartesian(xlim = c(analysis_start, analysis_end), ylim = c(-0.25, 0.55), clip = "off") +
  theme_void(base_family = font_family) +
  theme(plot.margin = margin(0, 5, 0, 10))

fig2b_core <- delta_plot / fst_plot / model_strip + plot_layout(heights = c(0.43, 0.43, 0.14))
fig2b <- fig2b_core

# Fig. 2c: local XI/GJ population-genetic profiles.
filter_start_mb <- cfg_num("popgen_filter_start") / 1e6
filter_end_mb <- cfg_num("popgen_filter_end") / 1e6
promoter_start_mb <- promoter_start / 1e6
promoter_end_mb <- promoter_end / 1e6
gene_start_mb <- gene_start / 1e6
gene_end_mb <- gene_end / 1e6

shade_regional <- function(plot_object) {
  plot_object +
    annotate("rect", xmin = promoter_start_mb, xmax = promoter_end_mb, ymin = -Inf, ymax = Inf, fill = "#FEE8C8", alpha = 0.42) +
    annotate("rect", xmin = gene_start_mb, xmax = gene_end_mb, ymin = -Inf, ymax = Inf, fill = "#DDEFEF", alpha = 0.42)
}

pi_focus <- pi_data %>% filter(in_filter_scope == "TRUE", group %in% c("XI", "GJ")) %>% mutate(x = MID / 1e6, y = value * 1e4)
tajima_focus <- tajima_data %>% filter(in_filter_scope == "TRUE", group %in% c("XI", "GJ")) %>% mutate(x = MID / 1e6, y = value)
fst_focus <- fst_data %>% filter(in_filter_scope == "TRUE", pair_id == "XI_vs_GJ") %>% mutate(x = MID / 1e6, y = value)

pi_plot <- ggplot(pi_focus, aes(x = x, y = y, colour = group))
pi_plot <- shade_regional(pi_plot) +
  geom_line(linewidth = 0.65) + geom_point(size = 0.75) +
  scale_colour_manual(values = group_colors[c("XI", "GJ")]) +
  scale_x_continuous(limits = c(filter_start_mb, filter_end_mb), expand = c(0, 0)) +
  labs(x = NULL, y = "Pi (x10^-4)", title = "Nucleotide diversity", colour = NULL) +
  theme_pub(base_size - 1) + theme(axis.text.x = element_blank(), axis.ticks.x = element_blank(), legend.position = "top", plot.margin = margin(3, 5, 1, 10))

tajima_plot <- ggplot(tajima_focus, aes(x = x, y = y, colour = group))
tajima_plot <- shade_regional(tajima_plot) +
  geom_hline(yintercept = 0, linetype = "dashed", linewidth = 0.3, colour = "#777777") +
  geom_line(linewidth = 0.65) + geom_point(size = 0.75) +
  scale_colour_manual(values = group_colors[c("XI", "GJ")], guide = "none") +
  scale_x_continuous(limits = c(filter_start_mb, filter_end_mb), expand = c(0, 0)) +
  labs(x = NULL, y = "Tajima's D", title = "Site-frequency-spectrum summary") +
  theme_pub(base_size - 1) + theme(axis.text.x = element_blank(), axis.ticks.x = element_blank(), plot.margin = margin(1, 5, 1, 10))

regional_fst_plot <- ggplot(fst_focus, aes(x = x, y = y))
regional_fst_plot <- shade_regional(regional_fst_plot) +
  geom_hline(yintercept = 0, linewidth = 0.3, colour = "#777777") +
  geom_line(linewidth = 0.65, colour = "#5E3C99") + geom_point(size = 0.75, colour = "#5E3C99") +
  scale_x_continuous(limits = c(filter_start_mb, filter_end_mb), expand = c(0, 0)) +
  labs(x = paste0("Chromosome ", cfg[["gene_chr_vcf"]], " position (Mb)"), y = "Weighted Fst", title = "XI-GJ differentiation") +
  theme_pub(base_size - 1) + theme(plot.margin = margin(1, 5, 3, 10))

fig2c_core <- pi_plot / tajima_plot / regional_fst_plot + plot_layout(heights = c(1, 1, 1))
fig2c <- fig2c_core

fig2 <- (wrap_elements(full = fig2a) | wrap_elements(full = fig2b)) / wrap_elements(full = fig2c) +
  plot_layout(widths = c(0.43, 0.57), heights = c(0.57, 0.43)) +
  plot_annotation(tag_levels = "a")
fig2_dir <- "Fig2_HaplotypeRelationships_XI_GJ"
save_pair(fig2a, file.path(fig2_dir, "panels", "Fig2a_PrimaryHaplotypeNetwork"), 78, 104, "main_panel", "Fig2")
save_pair(fig2b, file.path(fig2_dir, "panels", "Fig2b_SiteDifferentiation"), 102, 104, "main_panel", "Fig2")
save_pair(fig2c, file.path(fig2_dir, "panels", "Fig2c_RegionalPopulationGenetics"), 180, 78, "main_panel", "Fig2")
save_pair(fig2, file.path(fig2_dir, "Fig2_HaplotypeRelationships_XI_GJ"), cfg_num("fig2_width_mm"), cfg_num("fig2_height_mm"), "main_composite", "Fig2")

# Fig. S1: all unfiltered haplotypes, with the primary set highlighted.
rank_plot_data <- all_haplotypes %>%
  mutate(primary_status = if_else(selected_primary == "TRUE", "Primary", "Other"))
figs1 <- ggplot(rank_plot_data, aes(x = rank, y = haplotype_chromosome_count, colour = primary_status)) +
  geom_line(aes(group = 1), colour = "#BDBDBD", linewidth = 0.4) +
  geom_point(size = 1.15, alpha = 0.85) +
  geom_text_repel(
    data = filter(rank_plot_data, primary_status == "Primary"),
    aes(label = primary_haplotype_id),
    family = font_family, size = 1.8, direction = "y", nudge_x = 4,
    seed = as.integer(cfg[["random_seed"]]), max.overlaps = Inf,
    min.segment.length = 0, box.padding = 0.25, point.padding = 0.15,
    segment.colour = "#808080", segment.size = 0.2,
    show.legend = FALSE
  ) +
  scale_y_log10(labels = label_comma()) +
  scale_colour_manual(values = c(Primary = "#0072B2", Other = "#A6A6A6")) +
  labs(
    title = "Haplotype rank-abundance",
    subtitle = sprintf("All %s phased chromosome-copy haplotypes; the primary set is highlighted", nrow(all_haplotypes)),
    x = "Haplotype rank", y = "Chromosome-copy count (log10 scale)", colour = NULL
  ) +
  theme_pub() + theme(legend.position = "top")

# Fig. S2: true neighbor-joining tree with branch lengths.
distance_values <- as.matrix(distance_matrix[, -1])
mode(distance_values) <- "numeric"
rownames(distance_values) <- distance_matrix$primary_haplotype_id
colnames(distance_values) <- names(distance_matrix)[-1]
nj_tree <- nj(as.dist(distance_values))
write.tree(nj_tree, file = file.path(result_dir, "tree", "primary_haplotype_NJ_tree.newick"))
tip_data <- nodes %>% transmute(label = primary_haplotype_id, enrichment_direction)
tree_max_depth <- max(node.depth.edgelength(nj_tree))
figs2 <- ggtree(nj_tree, linewidth = 0.55) %<+% tip_data +
  geom_tippoint(aes(colour = enrichment_direction), size = 2.2) +
  geom_tiplab(aes(label = label), family = font_family, fontface = "bold", size = 3, offset = 0.4, show.legend = FALSE) +
  scale_colour_manual(values = direction_colors, na.value = "#333333") +
  xlim(0, tree_max_depth * 1.28) +
  labs(
    title = "Neighbor-joining tree",
    subtitle = "Full-pattern Hamming distance; branch lengths are shown to scale",
    colour = NULL
  ) +
  theme_tree2() +
  theme(
    text = element_text(family = font_family, size = base_size),
    axis.text = element_text(family = font_family, size = base_size - 1, colour = "#222222"),
    axis.title = element_text(family = font_family, size = base_size),
    plot.title = element_text(family = font_family, size = base_size + 0.5),
    plot.subtitle = element_text(family = font_family, size = base_size - 1, colour = "#4D4D4D"),
    legend.position = "bottom", plot.margin = margin(8, 15, 8, 8)
  )

# Fig. S3: area-centroid distribution, explicitly not accession coordinates.
world <- map_data("world")
map_plot_data <- map_data_hap %>%
  mutate(longitude = as.numeric(longitude), latitude = as.numeric(latitude)) %>%
  filter(is.finite(longitude), is.finite(latitude)) %>%
  mutate(primary_haplotype_id = factor(primary_haplotype_id, levels = hap_levels))
figs3 <- ggplot() +
  geom_polygon(data = world, aes(x = long, y = lat, group = group), fill = "#F2F2F2", colour = "#D0D0D0", linewidth = 0.16) +
  geom_point(
    data = map_plot_data,
    aes(x = longitude, y = latitude, size = haplotype_chromosome_count, colour = detailed_group),
    alpha = 0.72
  ) +
  facet_wrap(~primary_haplotype_id, ncol = 3) +
  scale_colour_manual(values = group_colors, drop = FALSE) +
  scale_size_area(max_size = 4.2, breaks = c(10, 100, 500)) +
  coord_quickmap(xlim = c(-180, 180), ylim = c(-60, 85), expand = FALSE) +
  labs(
    title = "Area-centroid distribution",
    subtitle = "Original Area centroids; points are not accession sampling coordinates",
    x = NULL, y = NULL, colour = "Group", size = "Chr copies"
  ) +
  theme_void(base_family = font_family, base_size = base_size) +
  theme(
    strip.text = element_text(family = font_family, face = "bold", size = base_size - 0.5),
    plot.title = element_text(family = font_family, size = base_size + 0.5),
    plot.subtitle = element_text(family = font_family, size = base_size - 1, colour = "#4D4D4D"),
    legend.position = "bottom", panel.spacing = unit(1.5, "mm"), plot.margin = margin(8, 8, 8, 8)
  )

save_pair(figs1, file.path("Supplementary", "FigS1_AllHaplotypeRankAbundance"), 180, 105, "supplementary", "")
save_pair(figs2, file.path("Supplementary", "FigS2_MajorHaplotypeNJTree"), 135, 105, "supplementary", "")
save_pair(figs3, file.path("Supplementary", "FigS3_AreaCentroidDistribution"), 180, 120, "supplementary", "")

summary_dir <- file.path(result_dir, "summary")
dir.create(summary_dir, recursive = TRUE, showWarnings = FALSE)
write_tsv(figure_manifest, file.path(summary_dir, "figure_manifest.tsv"))
write.xlsx(figure_manifest, file.path(summary_dir, "figure_manifest.xlsx"), overwrite = TRUE)
writeLines(capture.output(sessionInfo()), file.path(result_dir, "logs", "R_sessionInfo.txt"))
message(sprintf("[plot] figure_pairs=%d output=%s", nrow(figure_manifest), figure_dir))

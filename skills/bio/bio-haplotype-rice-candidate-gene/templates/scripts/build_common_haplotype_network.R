#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)

get_arg <- function(name, default = NULL) {
  flag <- paste0("--", name)
  idx <- match(flag, args)
  if (is.na(idx)) return(default)
  if (idx == length(args)) stop(flag, " requires a value", call. = FALSE)
  args[[idx + 1]]
}

required_arg <- function(name) {
  value <- get_arg(name)
  if (is.null(value) || identical(value, "")) stop("--", name, " is required", call. = FALSE)
  value
}

genotype_path <- required_arg("genotype")
manifest_path <- required_arg("sample-manifest")
out_dir <- required_arg("out-dir")
prefix <- required_arg("prefix")
frequency_min <- as.numeric(get_arg("frequency-min", "0.005"))
plot_enabled <- toupper(get_arg("plot", "TRUE")) %in% c("TRUE", "T", "1", "YES")

if (!is.finite(frequency_min) || frequency_min < 0 || frequency_min >= 1) {
  stop("--frequency-min must be in [0, 1)", call. = FALSE)
}

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

read_table <- function(path) {
  con <- if (grepl("\\.gz$", path)) gzfile(path, "rt") else file(path, "rt")
  on.exit(close(con), add = TRUE)
  read.delim(con, sep = "\t", check.names = FALSE, stringsAsFactors = FALSE, quote = "", comment.char = "")
}

write_pair <- function(df, stem) {
  tsv <- paste0(stem, ".tsv")
  write.table(df, tsv, sep = "\t", quote = FALSE, row.names = FALSE, na = "")
  if (requireNamespace("openxlsx", quietly = TRUE)) {
    openxlsx::write.xlsx(df, paste0(stem, ".xlsx"), overwrite = TRUE)
  } else {
    warning("openxlsx not available; skipped XLSX for ", stem, call. = FALSE)
  }
}

geno <- read_table(genotype_path)
manifest <- read_table(manifest_path)

if (!all(c("CHROM", "POS", "REF", "ALT") %in% names(geno)[1:4])) {
  stop("Genotype table must start with CHROM, POS, REF, ALT", call. = FALSE)
}
if (!"sample_id" %in% names(manifest)) {
  sample_col <- intersect(names(manifest), c("Sample.ID", "Sample ID", "ID", "Accession.ID"))
  if (length(sample_col) == 0) stop("Sample manifest must contain sample_id", call. = FALSE)
  names(manifest)[names(manifest) == sample_col[[1]]] <- "sample_id"
}
if (!"analysis_group" %in% names(manifest)) {
  manifest$analysis_group <- "Undefined"
}

sample_ids <- names(geno)[5:ncol(geno)]
manifest <- manifest[match(sample_ids, manifest$sample_id), , drop = FALSE]
manifest$sample_id <- sample_ids
manifest$analysis_group[is.na(manifest$analysis_group) | manifest$analysis_group == ""] <- "Undefined"

variant_labels <- paste0(geno$CHROM, ":", geno$POS, ":", geno$REF, ">", geno$ALT)
hap_rows <- list()
skipped_rows <- list()

split_gt <- function(gt) {
  gt <- as.character(gt)
  if (is.na(gt) || gt == "" || grepl("\\.", gt)) return(NULL)
  gt0 <- strsplit(gt, ":", fixed = TRUE)[[1]][[1]]
  sep <- if (grepl("\\|", gt0)) "\\|" else if (grepl("/", gt0)) "/" else NA_character_
  if (is.na(sep)) return(NULL)
  alleles <- strsplit(gt0, sep)[[1]]
  if (length(alleles) != 2 || any(alleles == ".")) return(NULL)
  if (identical(sep, "/") && alleles[[1]] != alleles[[2]]) return(NULL)
  alleles
}

for (sample_id in sample_ids) {
  gts <- geno[[sample_id]]
  alleles <- lapply(gts, split_gt)
  if (any(vapply(alleles, is.null, logical(1)))) {
    skipped_rows[[length(skipped_rows) + 1L]] <- data.frame(
      sample_id = sample_id,
      reason = "missing_or_unphased_heterozygous_genotype",
      stringsAsFactors = FALSE
    )
    next
  }
  chr1 <- paste(vapply(alleles, function(x) x[[1]], character(1)), collapse = "")
  chr2 <- paste(vapply(alleles, function(x) x[[2]], character(1)), collapse = "")
  hap_rows[[length(hap_rows) + 1L]] <- data.frame(sample_id = sample_id, chromosome_copy = "1", haplotype_pattern = chr1, stringsAsFactors = FALSE)
  hap_rows[[length(hap_rows) + 1L]] <- data.frame(sample_id = sample_id, chromosome_copy = "2", haplotype_pattern = chr2, stringsAsFactors = FALSE)
}

hap_long <- if (length(hap_rows) > 0) do.call(rbind, hap_rows) else data.frame(sample_id = character(), chromosome_copy = character(), haplotype_pattern = character())
skipped <- if (length(skipped_rows) > 0) do.call(rbind, skipped_rows) else data.frame(sample_id = character(), reason = character())
total_hap_chromosomes <- nrow(hap_long)
if (total_hap_chromosomes == 0) stop("No complete phased haplotypes were retained", call. = FALSE)

counts <- as.data.frame(table(hap_long$haplotype_pattern), stringsAsFactors = FALSE)
names(counts) <- c("haplotype_pattern", "haplotype_chromosome_count")
counts$haplotype_chromosome_count <- as.integer(counts$haplotype_chromosome_count)
counts$frequency <- counts$haplotype_chromosome_count / total_hap_chromosomes
counts <- counts[counts$frequency > frequency_min, , drop = FALSE]
if (nrow(counts) == 0) {
  stop("No common haplotypes passed frequency >", frequency_min, call. = FALSE)
}
counts <- counts[order(-counts$haplotype_chromosome_count, counts$haplotype_pattern), , drop = FALSE]
counts$haplotype_id <- sprintf("H%03d", seq_len(nrow(counts)))
counts$frequency_threshold <- frequency_min
counts$total_haplotype_chromosomes <- total_hap_chromosomes
counts <- counts[, c("haplotype_id", "haplotype_pattern", "haplotype_chromosome_count", "frequency", "frequency_threshold", "total_haplotype_chromosomes")]

common_patterns <- counts$haplotype_pattern
hap_long <- merge(hap_long, counts[, c("haplotype_id", "haplotype_pattern")], by = "haplotype_pattern")
hap_long <- merge(hap_long, manifest[, c("sample_id", "analysis_group")], by = "sample_id", all.x = TRUE)
hap_long$analysis_group[is.na(hap_long$analysis_group) | hap_long$analysis_group == ""] <- "Undefined"
hap_long <- hap_long[order(hap_long$haplotype_id, hap_long$sample_id, hap_long$chromosome_copy), ]

groups <- sort(unique(c("Wild", "Cultivar", "Undefined", hap_long$analysis_group)))
group_matrix <- as.data.frame.matrix(table(
  factor(hap_long$haplotype_id, levels = counts$haplotype_id),
  factor(hap_long$analysis_group, levels = groups)
))
group_matrix$haplotype_id <- rownames(group_matrix)
node_table <- merge(
  counts[, c("haplotype_id", "haplotype_pattern", "haplotype_chromosome_count", "frequency")],
  group_matrix,
  by = "haplotype_id",
  all.x = TRUE,
  sort = FALSE
)
node_table <- node_table[match(counts$haplotype_id, node_table$haplotype_id), , drop = FALSE]
for (group in groups) {
  if (!group %in% names(node_table)) node_table[[group]] <- 0L
  node_table[[group]][is.na(node_table[[group]])] <- 0L
}

hamming <- function(a, b) {
  av <- strsplit(a, "", fixed = TRUE)[[1]]
  bv <- strsplit(b, "", fixed = TRUE)[[1]]
  if (length(av) != length(bv)) stop("Haplotype patterns differ in length", call. = FALSE)
  sum(av != bv)
}

if (nrow(counts) >= 2) {
  pairs <- combn(counts$haplotype_id, 2)
  edge_all <- data.frame(
    hap_a = pairs[1, ],
    hap_b = pairs[2, ],
    stringsAsFactors = FALSE
  )
  pattern_by_hap <- stats::setNames(counts$haplotype_pattern, counts$haplotype_id)
  edge_all$distance <- mapply(function(a, b) hamming(pattern_by_hap[[a]], pattern_by_hap[[b]]), edge_all$hap_a, edge_all$hap_b)
  if (requireNamespace("igraph", quietly = TRUE)) {
    graph <- igraph::graph_from_data_frame(edge_all[, c("hap_a", "hap_b", "distance")], directed = FALSE)
    mst <- igraph::mst(graph, weights = igraph::E(graph)$distance)
    edges <- igraph::as_data_frame(mst, what = "edges")
    names(edges) <- c("hap_a", "hap_b", "distance")
    edges$distance <- as.integer(edges$distance)
  } else {
    edge_all <- edge_all[order(edge_all$distance, edge_all$hap_a, edge_all$hap_b), ]
    parent <- stats::setNames(counts$haplotype_id, counts$haplotype_id)
    find <- function(x) {
      while (parent[[x]] != x) x <- parent[[x]]
      x
    }
    chosen <- list()
    for (i in seq_len(nrow(edge_all))) {
      a <- edge_all$hap_a[[i]]
      b <- edge_all$hap_b[[i]]
      ra <- find(a)
      rb <- find(b)
      if (ra != rb) {
        parent[[rb]] <- ra
        chosen[[length(chosen) + 1L]] <- edge_all[i, ]
      }
    }
    edges <- do.call(rbind, chosen)
  }
} else {
  edge_all <- data.frame(hap_a = character(), hap_b = character(), distance = integer())
  edges <- data.frame(hap_a = character(), hap_b = character(), distance = integer())
}

variant_table <- data.frame(
  variant_index = seq_along(variant_labels),
  variant_label = variant_labels,
  CHROM = geno$CHROM,
  POS = geno$POS,
  REF = geno$REF,
  ALT = geno$ALT,
  stringsAsFactors = FALSE
)
audit <- data.frame(
  metric = c(
    "input_genotype", "sample_manifest", "variant_count", "sample_count",
    "complete_sample_count", "skipped_sample_count", "total_haplotype_chromosomes",
    "common_haplotype_frequency_min", "common_haplotype_count"
  ),
  value = c(
    genotype_path, manifest_path, nrow(geno), length(sample_ids),
    length(unique(hap_long$sample_id)), nrow(skipped), total_hap_chromosomes,
    frequency_min, nrow(counts)
  ),
  stringsAsFactors = FALSE
)

stem <- file.path(out_dir, prefix)
write_pair(counts, paste0(stem, ".common_haplotype_counts"))
write_pair(hap_long[, c("sample_id", "chromosome_copy", "haplotype_id", "haplotype_pattern", "analysis_group")], paste0(stem, ".common_haplotype_sample_assignment"))
write_pair(node_table, paste0(stem, ".common_haplotype_node_table"))
write_pair(edge_all, paste0(stem, ".common_haplotype_pairwise_distances"))
write_pair(edges, paste0(stem, ".common_haplotype_edges"))
write_pair(variant_table, paste0(stem, ".common_haplotype_variant_table"))
write_pair(skipped, paste0(stem, ".common_haplotype_skipped_samples"))
write_pair(audit, paste0(stem, ".common_haplotype_network_audit"))
write.table(edges, paste0(stem, ".network_publisher_edges.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)

if (plot_enabled) {
  node_radius <- sqrt(node_table$haplotype_chromosome_count)
  node_radius <- 6 + 10 * (node_radius - min(node_radius)) / max(1, max(node_radius) - min(node_radius))
  if (requireNamespace("igraph", quietly = TRUE) && nrow(counts) > 0) {
    graph <- igraph::graph_from_data_frame(edges, directed = FALSE, vertices = data.frame(name = counts$haplotype_id))
    set.seed(20260706)
    layout <- igraph::layout_with_fr(graph)
    plot_network <- function(file, device) {
      if (device == "pdf") grDevices::pdf(file, width = 8, height = 7)
      if (device == "png") grDevices::png(file, width = 4800, height = 4200, res = 600)
      on.exit(grDevices::dev.off(), add = TRUE)
      igraph::plot.igraph(
        graph,
        layout = layout,
        vertex.size = node_radius,
        vertex.label = paste0(node_table$haplotype_id, "\n", node_table$haplotype_chromosome_count),
        vertex.color = "#8ECae6",
        vertex.frame.color = "#1D3557",
        edge.width = pmax(1, edges$distance),
        edge.label = edges$distance,
        main = paste0(prefix, " common haplotype network")
      )
    }
    plot_network(paste0(stem, ".common_haplotype_network.pdf"), "pdf")
    plot_network(paste0(stem, ".common_haplotype_network.png"), "png")
  } else {
    grDevices::pdf(paste0(stem, ".common_haplotype_network.pdf"), width = 8, height = 7)
    plot.new()
    text(0.5, 0.5, "Single common haplotype; no edges")
    grDevices::dev.off()
    grDevices::png(paste0(stem, ".common_haplotype_network.png"), width = 4800, height = 4200, res = 600)
    plot.new()
    text(0.5, 0.5, "Single common haplotype; no edges")
    grDevices::dev.off()
  }
}

#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
get_arg <- function(name, default = NULL) {
  idx <- match(paste0("--", name), args)
  if (is.na(idx)) return(default)
  args[[idx + 1L]]
}
prefix <- get_arg("prefix")
out_dir <- get_arg("out-dir")
frequency_min <- as.numeric(get_arg("frequency-min", "0.005"))
if (is.null(prefix) || is.null(out_dir)) stop("--prefix and --out-dir are required", call. = FALSE)

read_tsv <- function(name) {
  read.delim(file.path(out_dir, paste0(prefix, ".", name, ".tsv")), sep = "\t", check.names = FALSE, stringsAsFactors = FALSE)
}
exists_nonempty <- function(path) file.exists(path) && file.info(path)$size > 0

checks <- list()
add_check <- function(check, ok, detail) {
  checks[[length(checks) + 1L]] <<- data.frame(check = check, status = if (ok) "PASS" else "FAIL", detail = detail, stringsAsFactors = FALSE)
}

required <- c(
  "common_haplotype_counts", "common_haplotype_sample_assignment", "common_haplotype_node_table",
  "common_haplotype_edges", "common_haplotype_network_audit"
)
required_paths <- file.path(out_dir, paste0(prefix, ".", required, ".tsv"))
add_check("required_tables", all(vapply(required_paths, exists_nonempty, logical(1))), paste(required_paths, collapse = ";"))

if (all(vapply(required_paths, exists_nonempty, logical(1)))) {
  counts <- read_tsv("common_haplotype_counts")
  assignment <- read_tsv("common_haplotype_sample_assignment")
  nodes <- read_tsv("common_haplotype_node_table")
  edges <- read_tsv("common_haplotype_edges")
  add_check("frequency_threshold", all(abs(counts$frequency_threshold - frequency_min) < 1e-12), paste0("expected ", frequency_min))
  assigned_counts <- as.data.frame(table(assignment$haplotype_id), stringsAsFactors = FALSE)
  names(assigned_counts) <- c("haplotype_id", "assigned_count")
  merged <- merge(counts[, c("haplotype_id", "haplotype_chromosome_count")], assigned_counts, by = "haplotype_id", all.x = TRUE)
  merged$assigned_count[is.na(merged$assigned_count)] <- 0L
  add_check("count_consistency", all(merged$haplotype_chromosome_count == merged$assigned_count), "counts match assignment table")
  add_check("node_consistency", setequal(nodes$haplotype_id, counts$haplotype_id), "node ids match count table")
  expected_edges <- max(0L, nrow(counts) - 1L)
  add_check("mst_edge_count", nrow(edges) == expected_edges, paste0("expected ", expected_edges, " edges"))
  add_check("group_columns", all(c("Wild", "Cultivar", "Undefined") %in% names(nodes)), "node table includes required group columns")
}

pdf <- file.path(out_dir, paste0(prefix, ".common_haplotype_network.pdf"))
png <- file.path(out_dir, paste0(prefix, ".common_haplotype_network.png"))
add_check("figure_outputs", exists_nonempty(pdf) && exists_nonempty(png), paste(pdf, png, sep = ";"))

qa <- do.call(rbind, checks)
write.table(qa, file.path(out_dir, paste0(prefix, ".common_haplotype_network_qa.tsv")), sep = "\t", quote = FALSE, row.names = FALSE)
if (requireNamespace("openxlsx", quietly = TRUE)) {
  openxlsx::write.xlsx(qa, file.path(out_dir, paste0(prefix, ".common_haplotype_network_qa.xlsx")), overwrite = TRUE)
}
if (any(qa$status != "PASS")) {
  print(qa)
  quit(status = 1)
}

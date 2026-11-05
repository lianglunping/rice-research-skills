# 3K reference two-main-figure v1

Use `formal_mode=3k_reference_two_mainfig_v1` when the customer wants exactly two manuscript-style composites from the 3K cultivated-rice dataset and has not requested a wild-versus-cultivated comparison. Fig1 and Fig2 must share the same 3K source and metadata contract.

## Cohort and input roles

- Use the frozen 3K genotype source and `3K-info.csv`; report the source/header sample count, metadata match, excluded `K5=na`, and K5 recoding.
- Treat sample count as role-specific evidence, not a project constant. Read every delivered VCF header independently: a post-QC/K5-restricted Fig1 VCF may legitimately have fewer sample columns than the unpruned Fig2 wide VCF. Record the exclusion rule and reconcile each header count to its own sample manifest; never assert that the two counts must be identical.
- Do not add wild rice when the customer asks for 3K cultivated rice only.
- Fig1 may apply the declared haplotype-site call-rate, MAF, bad-rate, complete-homozygote, and major-haplotype filters.
- Fig2 must use a dataset-matched 3K wide interval. Keep its SFS/statistic filter independent of Fig1: canonical biallelic SNPs plus the declared call-rate threshold, with no MAF filter by default for Pi and Tajima's D.
- The standard remote full source is `/path/to/reference-data/3K/3K/SNP/29M.vcf.gz`. If command-line `bcftools/tabix` is absent but `pysam` and the `.tbi` exist, a read-only indexed `pysam.VariantFile.fetch` extraction is acceptable. Record any source-index timestamp warning and validate the extracted subset's record count, coordinate bounds, sorting, local index, and hashes.
- Before computation or rendering, preflight every configured input and plotting asset, including GFF3, metadata, interval VCF/index pairs, a world-map geometry/coordinate table, fonts, and the project-local Python/R libraries. Record the exact resolved path and SHA-256 for immutable data assets. A missing map asset is an input failure to repair, not a reason to substitute an unrecorded base map.

## Figure contract

Deliver exactly two main composites with nested reusable panels:

1. `Fig1_Haplotype`: A = gene/allele matrix, B = displayed-site major-haplotype MST, C = world coordinate distribution, D = accession relationship tree.
2. `Fig2_SelectionScan`: Pi, Tajima's D, Weir-Cockerham weighted Fst, and log2 Pi ratio, each shown as a genuine broad/local pair in a 4 x 2 layout.

Fig1 rules:

- In A, the gene model may use connector guides but should not add undifferentiated black variant dots when the table already gives exact sites. For a negative-strand primary transcript, state and draw transcription from right to left, define the promoter on the higher-coordinate side, and use a strand-aware caption rather than a visually ambiguous generic `5' to 3'` label. No text may be covered or clipped.
- In B, compute distance from exactly the A-panel displayed sites. Encode one SNP difference as one short perpendicular edge tick; do not repeat the distance as a numeric label.
- In C, aggregate an exact coordinate into one pie. Pie sectors encode major haplotype, pie area encodes location accession `n`, and deterministic displacement plus leader lines resolves collisions.
- In D, saturated branch color encodes haplotype. A spatially separate low-saturation outer band may encode K5; palettes and legends must be distinct.

Fig2 rules:

- Default to a roughly ±200-kb broad context and a true narrower local context, frozen in configuration.
- Use 10-kb windows with 5-kb steps unless the data density or client specification justifies another predeclared choice.
- Compare only the declared groups, commonly XI and GJ. Define ratio direction explicitly, for example `log2(Pi_XI/Pi_GJ)`.
- Without a callable mask, label Pi and Tajima's D as nominal-window descriptive summaries and do not infer confirmed selection from peaks or troughs.

## R/Cairo runtime gate

R remains the default Fig2 renderer. Before formal plotting, open a real test PDF and PNG with the configured device and font. A successful `install.packages()` call is insufficient if `library(Cairo)` or device creation fails.

On macOS, a CRAN binary may hard-link XQuartz libraries under `/opt/X11`. Resolve this by either an explicitly authorized XQuartz installation or a project-isolated source build linked to Homebrew Cairo through `pkg-config`. Record R, Cairo R package, system Cairo, and rasterizer versions.

If the direct high-DPI PNG differs from or clips relative to the accepted R vector PDF, keep the PDF as the geometry authority and rasterize it deterministically at a validated DPI. Verify the entire page, exact pixel dimensions, text clearance, and PDF/PNG semantic parity.

## Release and QA

The release root is exactly `figure/`, `manuscript/`, `table/`, and `README.md`. `figure/` contains exactly `Fig1_Haplotype/` and `Fig2_SelectionScan/`. Include PDF and PNG composites, nested panels, source TSV/XLSX, the branch-length Newick, Fig1 post-QC VCF, Fig2 wide-interval VCF, recursive data dictionaries, and disclosure of the distinct Fig1/Fig2 filters. Keep the release manifest, hashes, QA tables, absolute-path configuration, logs, and environment evidence in the internal result tree rather than the customer tree.

Require:

- Fig1 source QA all PASS, A/B site-distance equality, MST `N-1`, C pie count conservation, D tip/annotation equality, and no clipped text.
- Fig2 four metrics × two populated scopes, no unapproved MAF filter, explicit ratio direction, source-index disclosure, vector text, no Type 3 fonts, and complete-page PNG parity.
- exactly two main composites, an external recursive release manifest that verifies the customer tree, and a customer-safe manuscript with no internal absolute paths.
- a UTF-8-safe ZIP whose decoded member names exactly match the release tree on Python and command-line readers; CRC, member inventory, SHA-256, safe relative paths, and the four-entry top-level whitelist must all pass.

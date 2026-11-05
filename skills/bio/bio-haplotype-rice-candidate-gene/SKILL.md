---
name: bio-haplotype-rice-candidate-gene
description: "Rice candidate-gene haplotype analysis with reference/gene mapping, population structure, missingness and phenotype-association limits."
---

# Rice Candidate Gene Haplotype Analysis

## Goal

Given standard inputs (Fst/Pi/TajimaD directories + GFF3 + VCF.gz or 万份水稻 genotype tables), produce a fully QA-passed delivery package containing figures, data tables, and a Chinese methods description suitable for a thesis or manuscript. For a concise XI/GJ-centered result, use the publication-compact mode described below.

For trait-first client runs with both 3K and 万份水稻 data available, first audit phenotype sample overlap for both datasets, then run the formal haplotype workflow on the dataset with the larger matched phenotype sample count. See `references/data-sources.md`.

For domestication-style candidate-gene interpretation, add the common-haplotype network module inspired by Zhang et al. 2023 (`Multiple domestications of Asian rice`) but keep conclusion wording descriptive unless wild/cultivar sampling, metadata, and statistical support are explicit. See `references/domestication-common-haplotype-network.md`.

## Standard Inputs

```
{GENE_DIR}/
├── 01.Fst/          # {Group1}_{Group2}.windowed.weir.fst files
├── 02.Pi/           # {Group}.windowed.pi + {Group}.recode.vcf
├── 03.TajimaD/      # {Group}.Tajima.D files
├── {GENE_ID}.gff3   # MSU_osa1r7 annotation
└── {GENE_ID}.vcf.gz # 3K RGP VCF for the gene region (+ tabix index)
```

Plus shared metadata: `3K-info.csv` (columns: ID, K5, lat, lon, …)

Trait-first dual-dataset runs may also use:

```
remote_host=REPLACE_HOST
remote_conda_env=ngs
remote_3k_vcf_dir=/path/to/reference-data/3K/3K/SNP
remote_superrice_vcf_dir=/path/to/reference-data/superrice
superrice_remote_snp_dir=/path/to/reference-data/superrice/1.rare_SNP
superrice_remote_indel_dir=/path/to/reference-data/superrice/2.rare_InDel
dataset_selection_rule=max_trait_overlap
common_haplotype_frequency_min=0.005
phasing_mode=auto
```

## Pipeline Steps

### Step 0: New Gene Setup

1. Create the project runtime file `scripts/formal_release_config.tsv` from `references/config-template.tsv`.
2. Populate: gene coordinates from GFF3, chromosome (GFF = "ChrNN", VCF = "NN"), promoter (2 kb strand-aware upstream), analysis interval = gene ∪ promoter, dataset mode, and site-QC decision fields.
3. Use the driver matched to the dataset: the validated 3K driver may be `run_formal_analysis_siteqc.sh`; a 万份水稻 project must use its own formal superrice driver and must not inherit a 3K-only site-QC threshold by filename.

For full pipeline step descriptions, see `references/pipeline-guide.md`.

### Step 0b: Trait-First Dataset Selection

When a phenotype table is provided and both 3K and 万份水稻 VCF sources are available, do not pick a dataset by habit. Compare phenotype sample overlap first and select the dataset with the larger matched sample count. If tied, stop and ask. On `REPLACE_HOST`, activate `conda activate ngs`; prefer `fd` and `rg` for remote enumeration and audits.

### Step 0c: 万份水稻 / Common-Haplotype Network Setup

When `dataset_mode=superrice`, extract the target interval from `/path/to/reference-data/superrice/1.rare_SNP/Chr*.rareSNP.genotype.gz` and, when needed, `/path/to/reference-data/superrice/2.rare_InDel/Chr*.rareINDEL.genotype.gz` using `templates/scripts/extract_superrice_region.py`. Use the verified local metadata root `/path/to/metadata/`; revalidate it before each formal run.

Default common-haplotype threshold is frequency `> 0.5%` (`common_haplotype_frequency_min=0.005`). If genotype fields are already phased (`0|1`), do not run Beagle by default. Use Beagle only when `phasing_mode=beagle` or when `phasing_mode=auto` detects unphased heterozygotes (`0/1`) that are required for the analysis.

Before formalizing a 万份水稻 result, run and retain a site-QC threshold sensitivity table. Report raw/retained SNP and InDel counts, complete-sample count, and complete-sample retention by `analysis_group` for every tested threshold. Select and record a threshold by the documented rule; never reuse `0.03` or `0.10` as a universal value. Read `references/pipeline-decisions.md` DEC-013 and `references/qa-checklist.md` for the required evidence.

Audit the complete strand-aware promoter interval before site filtering. A promoter with raw variants but zero post-QC variants is a valid result: keep the interval in the gene model, report raw count, minimum bad-rate, threshold, and post-QC count, and deliver the raw per-site QC table. Never omit the promoter silently, force a site through QC for visual balance, or rewrite "included but zero retained" as "no promoter variation."

### Step 0d: 万份水稻 Reference-Compatible Formal Mode

When the requested output must match the information structure of the established 23-pair formal release, set `formal_mode=superrice_reference_compatible_v2` and read `references/superrice-reference-compatible-v2.md`. This mode is distinct from the Wild/Cultivar domestication-summary mode.

Required defaults for this mode are:

- Detailed groups: `XI* -> XI`, `GJ* -> GJ`, `Or* -> Or`, everything else `Undefined`.
- Haplotype definition: phased chromosome copies using SNP+InDel; keep the project-specific site-QC sensitivity decision.
- Display set: every `n >= 30` major haplotype plus frequency-ranked haplotypes to a predeclared maximum, normally top 80.
- Population genetics: canonical biallelic SNP-only VCF; Pi/Tajima's D/Weir-Cockerham Fst from `vcftools`; never substitute a custom weighted-Fst formula.
- Relationship views: a pie-node MST network and a separate true `ape::nj` tree. A topology-only circular NJ display is allowed only when the figure explicitly states that branch lengths are not to scale and the branch-length Newick is delivered.
- Maps: a versioned `Original Area -> centroid` table with mapping method/confidence and mapped-rate audit. Every map must state that points are not accession sampling coordinates.
- Figures: detailed promoter/UTR/CDS/intron model, A/C/G/T/DEL/INS matrix, genuinely distinct all/filter population-genetic ranges, PDF+600-dpi PNG pairs, and row-by-row manual publication review.

Keep three VCF roles explicit and never substitute one for another:

- `formal_haplotype_vcf`: all approved post-QC SNP+InDel sites and all source accessions, with numeric phased GT; this is the customer-facing source VCF.
- `population_genetics_vcf`: canonical biallelic SNP-only records used by vcftools for Pi, Tajima's D, and Weir-Cockerham Fst.
- `tree_snp_vcf`: the declared SNP subset used to infer the sample tree; it is a tree input, not the formal haplotype source VCF.

The formal haplotype VCF must be bgzip-compressed, tabix-indexed, and accompanied by a conversion audit. Deliver the three files under `table/SourceData/VCF/`; see DEC-027 and `references/qa-checklist.md`.

### Step 0e: 万份水稻 Publication-Compact XI/GJ Mode

When the client wants 1-2 manuscript-style main figures rather than a large figure inventory, set `formal_mode=superrice_publication_compact_v3` and read `references/superrice-publication-compact-v3.md`.

Use a validated superrice result as a read-only source. Default primary haplotypes require both `carrier accession n >= 30` and strict `max(XI_chr_frequency,GJ_chr_frequency) > 0.005`; equality to 0.5% does not pass. Also deliver an unfiltered table containing every haplotype.

Use accession carrier presence/absence for two-sided Fisher tests, BH correction, and Newcombe-Wilson rate-difference CIs. Chromosome-copy frequency is descriptive and may be used for the predeclared screen, but chromosome copies are not independent inferential units.

Produce two composite main figures, six reusable panel pairs, and three supplementary pairs. Store each main figure, its panels, legend, and Source Data workbook in one directory. Require vector PDF with no embedded raster objects, 600-dpi PNG, English figure text, Arial or Times New Roman, italic gene labels, and a post-render manual review table.

### Step 0f: 万份水稻 Reference Two-Main-Figure Mode

When the requested layout is a screenshot-style gene/variant table plus major-only relationship views, an all-retained-accession sample tree, and a separate selection-scan composite, set `formal_mode=superrice_reference_two_mainfig_v4` and read `references/superrice-reference-two-mainfig-v4.md` completely.

Use `templates/config-superrice-reference-two-mainfig-v4.tsv` and `templates/scripts/reference_two_mainfig_v4/`. This mode is a read-only derivative of a validated reference-compatible source run. Its project config must freeze the phased chromosome-copy `n >= 30` major set, all retained accession IDs, formal SNP+InDel VCF role, canonical SNP-only popgen/tree role, broad/local windows, callable-mask status, approved v2 result/release/ZIP paths, and a complete source-input SHA allowlist.

Do not reuse compact-v3's accession-carrier-plus-frequency threshold in this mode. Network, map, and gene/allele matrix IDs must equal the frozen major set. Infer and deliver a RapidNJ tree containing all retained accessions. When many accessions have identical local SNP genotypes and the full rendered tree becomes unreadable, the main figure may instead show a weighted tree of unique local genotype classes only if the release also delivers the full retained-accession Newick, the class summary, the accession-to-class membership table, and an audit proving membership closure. The figure title and legend must state the aggregation and node-size transform; do not call the class tree an all-accession tree. Customer delivery has exactly two main composites, while reusable panels remain nested under those figures.

When the client requests the analogous two-main-figure package from cultivated-rice 3K data, set `formal_mode=3k_reference_two_mainfig_v1` and read `references/3k-reference-two-mainfig-v1.md` completely. Fig1 and Fig2 must use the same 3K cohort and metadata contract; never combine a 3K haplotype Fig1 with a superrice population-genetics Fig2.

Plot at the declared 180-mm final physical size rather than composing oversized panels and shrinking them. The default final-size floor is 8.5 pt for all ordinary text and 13 pt for panel labels. PDF text must be editable vector text, embedded, and limited to Arial or Times New Roman; reject Helvetica, Symbol, Type 3, rasterized text, and embedded image XObjects. The Chinese manuscript is not a short README: generate structured 材料与方法、结果与分析、逐 panel 图注和参考文献 from the config and result tables, including databases, software versions, parameters, denominators, units, Source Data links, and evidence boundaries.

### Step 1: Run the Pipeline

For 3K runs, use the configured formal driver, commonly:

```bash
bash scripts/run_formal_analysis_siteqc.sh
```

For 万份水稻 runs, execute the project-specific formal superrice driver recorded in the config and project README. It must write the identical contract, threshold-sensitivity, sample-QC, release-manifest, and QA evidence surfaces.

For `superrice_publication_compact_v3`, copy `templates/scripts/publication_compact_v3/`, adapt `templates/config-superrice-publication-compact-v3.tsv`, and run the compact driver only after the source run has passed its own QA.

For `superrice_reference_two_mainfig_v4`, copy `templates/scripts/reference_two_mainfig_v4/`, adapt `templates/config-superrice-reference-two-mainfig-v4.tsv`, and run the derivative sequentially per gene. The driver intentionally stops at the manual visual-review gate before any release/ZIP is built.

The corresponding formal driver must cover versions → metadata → interval extraction/filtering → haplotype QC → relationship/popgen summaries → figures → QA. Logs land in `results/{RUN_ID}/logs/`.

For projects that enable the common-haplotype module, run `build_common_haplotype_network.R` after interval genotype extraction / haplotype construction and include its QA output in the final release.

### Step 2: Review QA Results

```bash
cat results/{RUN_ID}/summary/formal_release_qa.tsv
```

Confirm every check shows `PASS`, including the PDF text-layer chromosome-label guard, complete-sample retention by metadata group, and a row-by-row manual visual review. Publication-compact mode must additionally recompute the joint threshold and XI/GJ statistics, verify matrix dimensions, require `N-1` MST edges and NJ tip equality, and reject any embedded PDF raster object. Fix any failures before proceeding; see `references/qa-checklist.md`.

### Step 3: Package Delivery

The default customer release root has exactly four entries:

```text
release/{RELEASE_ID}/
├── figure/
├── manuscript/
├── table/
└── README.md
```

Place the formal haplotype VCF, its `.tbi`, and conversion audit under `table/SourceData/VCF/`. Every directory at or below `table/` must contain `README.md` that documents all immediate children; every real table must include a sheet-aware, exact-column data dictionary with units, denominators, coordinates, allowed values, and missing-value rules. Generate these descriptions from the delivered files and run recursive schema coverage QA; read `references/table-readme-contract.md` before packaging.

Keep scripts, logs, internal QA workbooks/TSVs, schema inventories, README manifests, contact sheets, environment exports, and temporary tests outside the customer release and ZIP. The internal result directory retains all reproducibility and acceptance evidence. Confirm the ZIP top-level whitelist and run `unzip -t` before delivery. See DEC-028.

### Step 4: Archive Superseded Runs

After a corrected release is accepted, keep the active `results/{RUN_ID}`, `release/{RELEASE_ID}`, scripts, inputs, audit notes, and the main delivery zip. Move superseded/failed runs, obsolete delivery zips, and top-level run logs to `archive/{YYYYMMDD}_superseded_runs/` with a short README and SHA256 manifest. Delete only redundant duplicates and empty temporary folders; never delete raw inputs.

## Critical Quality Rules

Non-obvious rules that must be preserved across all genes:

| Rule | Description |
|------|-------------|
| **variant_count** | Report `post_site_qc_variant_count` (not pre-QC) in Figure_Legends and Results_Discussion. See DEC-005. |
| **per-site bad-rate** | For the established 3K workflow, threshold = 3% `(missing + het) / total`. For 万份水稻, select a project-specific threshold from a recorded sensitivity audit; do not generalize a prior project's value. See DEC-001 and DEC-013. |
| **retained cohort** | Report complete/skipped samples overall and by `analysis_group`. If a group has zero or strongly unequal retention, describe results as the retained cohort only and do not make comparative group-frequency, selection, or population-history claims. |
| **major haplotype threshold** | Default n ≥ 30 (parameterizable). Encoded in `formal_release_config.tsv`. |
| **common haplotype threshold** | Default frequency > 0.5% (`0.005`) for domestication-style phased haplotype networks. This is separate from `n ≥ 30`. |
| **publication-compact primary threshold** | Require accession carriers `n >= 30` AND strict `max(XI_chr_freq,GJ_chr_freq) > 0.005`; keep both units and operators in a threshold-audit table. |
| **XI/GJ inference unit** | Use unique accession carrier/non-carrier status for Fisher, BH, and Newcombe-Wilson CIs. Never treat the two phased chromosome copies as independent samples. |
| **two result versions** | Deliver the thresholded primary set for concise figures and an unfiltered all-haplotype TSV/XLSX plus rank-abundance supplement. |
| **superrice phasing mode** | If 万份水稻 genotype fields contain `|`, treat them as phased and do not re-phase. Beagle is optional, not automatic. |
| **network evidence boundary** | Haplotype networks are descriptive. Do not claim domestication origin, introgression, or selection from the network alone. |
| **"混合群" not "芒稻"** | Call the Adm K5 group "混合群（Admixture）" in all Chinese text. |
| **Tajima's D order** | Positive D → 平衡选择或瓶颈效应 first; negative D → 方向性选择或扩张 second. |
| **run_id is dynamic** | `run_id <- basename(result_dir)` in formal_full_analysis.R; never hardcode a run ID. |
| **chromosome labels are dynamic** | Figure labels must be derived from `gene_chr_vcf` / `project_contract.tsv` (e.g. `Chromosome 7`), never copied as literal `Chromosome 11` or donor-gene text. |
| **PDF text-layer QA is mandatory** | QA must extract text from all release PDFs with `pdftotext` and fail on unexpected chromosome labels. Visual rendering alone is not sufficient. |
| **publication visual review is mandatory** | Inspect every figure at export scale and save a table with figure name, reviewer focus, status, and any action. A PDF/PNG pair or high DPI alone is not publication acceptance. |
| **pure vector PDF** | Reject PDFs containing embedded raster objects, including rasterized colour bars; use vector rectangle colour bars and retain an editable text layer. |
| **final-size typography** | Declare 180-mm default final width; ordinary text >= 8.5 pt and panel labels >= 13 pt after composition. Allow only embedded Arial or Times New Roman; reject Helvetica, Symbol, Type 3, rasterized text, unreadable Poppler word boxes, and positive-area collisions between axis titles and tick labels. Increase spacing or use truthful compact tick notation; never repair crowding by shrinking below the text floor. |
| **text-clearance gate** | Treat every covered, clipped, or overlapping label as a release-blocking failure. Run Poppler word-box collision/clipping checks on the final composite and dense component panels; also inspect the rendered image because word-box checks cannot detect connector, branch, grid, symbol, or legend graphics crossing glyphs. Page-level word-box PASS is insufficient for tables: use actual font metrics plus padding to verify every header label is fully contained within its intended cell. If rotated text exceeds cell height, increase the row height or use a horizontal multiline label. Draw guide/edge geometry before text, give critical labels opaque white clearance, use deterministic collision-aware placement for network labels, suppress duplicate endpoint labels, and reserve a dedicated legend region outside axes. Never pass by shrinking below the font floor. |
| **A/B displayed-site distance contract** | When a haplotype MST is presented as the relationship view of an A-panel allele matrix, compute every pairwise and MST edge distance from the exact sites displayed in A. Record the site count and independently recompute every edge. Encode one SNP difference as one short perpendicular edge tick; if a network intentionally uses the full post-QC matrix instead, label that different basis explicitly and do not imply direct A/B correspondence. |
| **promoter zero-retention contract** | Freeze the strand-aware promoter before extraction and include every raw promoter record in site QC. If zero sites pass, draw and label the promoter interval, report raw count/minimum bad-rate/threshold/post-QC zero, and deliver the raw site-QC table. Do not add black variant points, manufacture a promoter marker, relax the threshold for appearance, or state that promoter variation is absent. |
| **visual channel semantics** | Within each panel, one visual channel has one declared meaning. For the 3K four-panel haplotype figure, use A = gene/allele matrix, B = displayed-site MST, C = world distribution, and D = accession tree. In C, aggregate records at the exact metadata coordinate into one pie: sector color encodes major haplotype and pie area encodes location accession `n`; use deterministic symbol displacement plus leader lines when pies overlap, and audit source-to-pie count conservation and post-layout collision clearance. In D, saturated branch color encodes major haplotype; K5 may use a spatially separate, low-saturation outer-ring color band with its own palette and legend when line styles become visually dense. Gene-model variant positions may use connector guides without black point markers when the table already supplies exact positions. |
| **nonredundant tree display contract** | The full retained-accession tree remains the evidence surface. A unique-genotype-class display is allowed only to resolve demonstrated overplotting from repeated local genotypes; deliver the full Newick, class Newick, class summary, accession membership, and count-closure audit. Encode haplotype/diplotype with saturated color and rice group with line style or a distinct low-saturation channel; disclose aggregation and any logarithmic node-size transform. |
| **Chinese manuscript depth** | Methods must state databases, references, versions, parameters and analysis chain; Results must be data-driven and evidence-bounded; legends must define Fig1 a-d and Fig2 a-h with units, denominators, encodings, statistical meaning, limitations and Source Data. Customer manuscript files must not expose internal absolute paths; retain paths and hashes only in internal provenance/QA. |
| **compact figure organization** | Default to two composite main figures; retain each component as a separate PDF/PNG under the parent figure's `panels/` directory with matching Source Data. |
| **reference two-main-figure mode** | `superrice_reference_two_mainfig_v4` uses phased chromosome-copy `n >= 30`; Fig1 contains screenshot-style gene/variant matrix, major-only MST, all-retained-accession IBS/NJ tree with major-diplotype outer ring, and major-only centroid map; Fig2 contains Pi, Tajima's D, Weir-Cockerham Fst, and Pi ratio in true broad/local pairs. |
| **sparse matrix annotation** | If an allele matrix contains one allele class only, verify it against the source table and place the count-based explanation on the figure or in its delivered legend; do not leave a blank-looking matrix unexplained. |
| **geography evidence boundary** | Use maps only for accession latitude/longitude. When metadata has only `Original Area`, label every map as an area-level summary and do not imply sampling coordinates. |
| **grouping mode is explicit** | Do not mix domestication binary grouping with reference-compatible detailed grouping. Record `grouping_mode` and retain Undefined without forcing cA/cB or ambiguous labels into XI/GJ/Or. |
| **top-80 is display-only** | In reference-compatible mode, include all major haplotypes and then supplement to top 80. Do not redefine the `n >= 30` major threshold to reach 80. |
| **standard Fst only** | Formal population-genetic Fst must be `vcftools --weir-fst-pop` weighted Fst (or another explicitly approved standard estimator). A hand-written weighted average is not an equivalent replacement. |
| **SFS and callable-mask disclosure** | Do not apply a MAF filter to Tajima's D/Pi without a predeclared reason. Record missingness filtering and callable-mask availability; without a callable mask, describe nominal-window Pi/Tajima's D as descriptive. |
| **same-dataset two-main-figure contract** | Fig1 and Fig2 in one release must be derived from the same declared dataset and compatible sample metadata. If Fig1 uses 3K, obtain a 3K wide interval for Fig2; do not silently reuse superrice statistics. Keep Fig1 haplotype-site MAF/site-bad-rate filtering separate from Fig2 SFS-based statistics, which default to no MAF filter. |
| **role-specific VCF sample counts** | Read sample/site counts from every VCF independently and reconcile them to that file's declared role and exclusions. A K5-restricted post-QC Fig1 VCF and an unpruned Fig2 wide VCF may validly differ; never hardcode equality or copy one count into another README/QA rule. |
| **strand-aware gene-model direction** | For negative-strand targets, place the promoter on the higher-coordinate side and state/draw transcription from right to left in A, Methods, and the legend. Do not use an ambiguous generic `5' to 3'` label without an explicit directional mapping. |
| **plotting-asset preflight** | Before formal computation/rendering, resolve and hash-check configured annotations, metadata, VCF/index pairs, static world-map assets, fonts, and project-local runtimes. Missing R packages or map assets are repairable input/runtime failures, not permission to omit or silently substitute the intended panel. |
| **R graphics runtime repair** | A missing or unloadable required R package is an environment failure to repair, not a reason to silently switch plotting languages. Install into a project-isolated R library, record the version, and run real PDF/PNG smoke tests. On macOS, if the CRAN `Cairo` binary hard-links `/opt/X11`, either install XQuartz with explicit authority or compile `Cairo` from source against Homebrew Cairo; do not claim success after package installation alone. |
| **PDF-derived PNG parity** | Treat the reviewed vector PDF as the geometry authority. If a direct high-DPI device clips or changes text, block release and deterministically rasterize the accepted single-page PDF at a verified DPI. Check pixel dimensions and visually compare the full page; record distinct Fig1/Fig2 DPI when they differ. |
| **MST is not NJ** | The network and NJ tree are separate evidence surfaces. QA must confirm the NJ Newick tip set and the MST `N-1` edge count independently. |
| **reference-style matrices** | Display actual A/C/G/T and DEL/INS categories, preserve full alleles in tables, and provide promoter/CDS/all/default views with a detailed primary-transcript model. |
| **XI/GJ evidence boundary** | Specific haplotype carrier-frequency shifts may coexist with low regional Fst. Do not upgrade this to strong regional differentiation, selection, origin, introgression, causality, or breeding value. |
| **three VCF roles** | Keep the customer-facing post-QC SNP+InDel haplotype VCF separate from the canonical biallelic SNP-only population-genetics VCF and the tree-input SNP VCF. Never deliver the latter two as substitutes for the formal haplotype VCF. |
| **formal VCF audit** | Deliver the bgzip VCF, `.tbi`, and conversion audit under `table/SourceData/VCF/`; verify sample/site/SNP/InDel counts, REF/ALT and order, phased GT encoding, normalized GT hash, and bcftools/tabix readability. |
| **recursive table README contract** | Every directory at or below `table/` has `README.md`; each README lists every immediate child, and every XLSX sheet plus every TSV/CSV/VCF field has an exact, non-empty definition including unit/denominator, coordinates, allowed values, and missing-value behavior. Documentation-only revisions use a new release version and preserve accepted scientific payload files byte-for-byte. |
| **README generator-validator agreement** | Freeze one schema for generation and validation. The default field dictionary is a four-column Markdown table (`Column`, `Definition`, `Unit / denominator / allowed values`, `Missing-value rule`); VCF uses literal `#CHROM` and file-specific header counts. A generated README that fails its paired validator blocks release. |
| **customer release boundary** | Customer ZIP top level is exactly `figure/`, `manuscript/`, `table/`, and `README.md`. QA evidence, scripts, logs, environment records, and temporary files remain internal. |
| **UTF-8 ZIP integrity** | Build customer ZIPs with UTF-8 member names and verify them with an independent reader. CRC, safe relative paths, exact four-entry top level, release-tree inventory, and per-member SHA256 must pass; quarantine a non-UTF-8 package instead of delivering or overwriting evidence. |

## Output Structure

```
release/{RELEASE_ID}/
├── figure/           # Project-specific vector PDF + 600-dpi PNG figures
├── manuscript/       # Chinese thesis-style Methods, Results, and figure legends
├── table/            # Publication tables; every nested directory has a schema-aware README.md
└── README.md         # Customer-facing contents, scope, and reproduction pointer
```

## References

- `references/config-template.tsv` — blank config template for new genes
- `references/data-sources.md` — fixed REPLACE_HOST VCF paths, ngs environment, fd/rg preference, and trait-overlap dataset selection
- `references/domestication-common-haplotype-network.md` — Zhang et al. 2023-inspired common haplotype network module and evidence boundaries
- `references/pipeline-guide.md` — full pipeline step descriptions and new-gene adaptation checklist
- `references/pipeline-decisions.md` — rationale for all major analytical choices (DEC-001 to DEC-028)
- `references/superrice-reference-compatible-v2.md` — validated reference-compatible 万份水稻 formal workflow, 23-pair figure contract, and acceptance boundaries
- `references/superrice-publication-compact-v3.md` — concise XI/GJ-focused two-main-figure workflow, dual haplotype outputs, inference units, and publication QA
- `references/superrice-reference-two-mainfig-v4.md` — screenshot-style haplotype Fig1, all-accession sample tree, selection-scan Fig2, input-role separation, and release gates
- `references/3k-reference-two-mainfig-v1.md` — dataset-matched 3K Fig1/Fig2 workflow, no-MAF SFS statistics, R/Cairo runtime gate, PDF/PNG parity, and release contract
- `references/qa-checklist.md` — QA check descriptions and common failure fixes
- `references/table-readme-contract.md` — recursive table directory inventory, exact-column data dictionaries, special-format documentation, and acceptance rules
- `references/method-template.md` — 方法描述.md template for new genes
- `templates/scripts/extract_superrice_region.py` — interval extractor for 万份水稻 wide genotype tables
- `templates/scripts/build_common_haplotype_network.R` — phased common-haplotype network table/figure generator
- `templates/scripts/qa_common_haplotype_network.R` — common-haplotype network QA checks
- `templates/scripts/qa_table_readme_contract.py` — generic recursive README, immediate-child, XLSX/TSV/CSV column, and VCF documentation validator
- `templates/config-superrice-reference-compatible-v2.tsv` — reusable config skeleton for the publication-style superrice v2 mode
- `templates/config-superrice-publication-compact-v3.tsv` — reusable config skeleton for the compact XI/GJ mode
- `templates/config-superrice-reference-two-mainfig-v4.tsv` — reusable config skeleton for the two-main-figure sample-tree mode
- `templates/scripts/publication_compact_v3/` — table, plotting, visual-review, release, QA, and driver templates for compact mode
- `templates/scripts/reference_two_mainfig_v4/` — major-table, all-accession tree, plotting, visual gate, release, schema README, and verify-only templates for reference v4 mode

## Scope notes

Before choosing inputs, comparison units or conclusion thresholds, read
[the scientific scope notes](references/scope-notes.md) for this task.

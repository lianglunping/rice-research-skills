# QA Checklist — Formal Release

The formal release QA script (for example, `qa_formal_release.R` or `qa_formal_superrice_release.py`) runs the QA suite. All checks must PASS. The current suite includes chromosome-label checks against both text files and the PDF text layer.

## Check Descriptions

| Check | What it verifies |
|-------|-----------------|
| `required_files` | All mandatory input files exist and are non-empty |
| `coordinate_contract` | Gene/promoter/analysis interval matches config |
| `filtered_vcf_variant_positions` | All haplotype-input variant positions are within analysis interval |
| `hapSummary_plot_positions` | All positions in gene_variant_sites.tsv are within analysis interval |
| `hapSummary_metadata_guard` | No configured VCF/sample-manifest counts appear as variant positions |
| `plotting_asset_preflight` | Every configured annotation, metadata, VCF/index, world-map asset, font, and project-local runtime path exists and immutable data assets match their recorded hashes before rendering |
| `negative_strand_transcription_direction` | Negative-strand gene model, promoter interval, arrow direction, A-panel label, Methods, and legend consistently state right-to-left transcription and higher-coordinate promoter placement |
| `major_haplotype_threshold` | All major haplotypes have n ≥ 30 |
| `strict_primary_threshold_recomputed` | Compact mode recomputes `carrier n >= threshold AND max(XI,GJ chr frequency) > threshold`; equality and just-above synthetic cases behave correctly |
| `accession_fisher_bh_newcombe_recomputed` | XI/GJ carrier counts, two-sided Fisher p, BH q, and Newcombe-Wilson CI are independently reproduced with accessions as units |
| `major_haplotype_metrics` | Key metrics TSV is internally consistent |
| `site_qc_threshold_sensitivity` | For 万份水稻, the selected threshold is in the sensitivity table and agrees with config, retained variant counts, and Methods |
| `sample_retention_by_group` | Complete/skipped/total counts and rates are available by `analysis_group`; zero or strongly unequal retention is carried into interpretation limits |
| `figure_pdf_png_pairs` | Every PDF figure has a matching PNG |
| `figure_manifest_contract` | Compact mode contains the declared two composites, six main panels, and three supplementary pairs |
| `full_unfiltered_matrix_shape` | All-haplotype all-site matrix dimensions match the declared haplotype and post-QC variant counts |
| `formal_manifest_status` | All manifest rows show SHA256 match |
| `old_project_residue_guard` | No unexpected chromosome labels from a different gene appear in release text |
| `pdf_text_chromosome_guard` | Text extracted from all release PDFs has only the configured chromosome label, or no chromosome label |
| `pdf_render_visual_check` | Key PDFs render to PNG without corruption |
| `pdf_embedded_configured_font` | Every PDF embeds only the configured Arial or Times New Roman family, including an italic face for gene labels |
| `editable_vector_pdf_no_embedded_raster` | `pdfimages -list` finds no raster object, including rasterized continuous legends |
| `pdf_text_bbox_no_overlap` | Poppler word boxes show no positive-area collision between Fig2 y-axis title words and numeric tick labels at final size |
| `pdf_text_bbox_global_no_overlap` | Every final composite and dense panel has zero positive-area word-box overlaps and zero words outside the page box; duplicate endpoint coordinates are suppressed before rendering |
| `table_header_cell_containment` | Every table-header label fits wholly inside its intended cell using the embedded font's measured extent plus explicit padding; page-level non-overlap alone is insufficient |
| `panel_a_b_distance_contract` | Panel B pairwise/MST distances are independently recomputed from the exact allele columns displayed in panel A, and one perpendicular edge tick represents one displayed-site SNP difference |
| `cross_panel_visual_encoding_contract` | Gene-model point markers, MST ticks, C-map pie encodings, and D-tree branch/K5 encodings match the declared one-channel-one-meaning contract |
| `panel_c_map_pie_contract` | Panel C has one pie per exact metadata coordinate; sector colors encode major haplotypes, pie area encodes location accession `n`, source/pie carrier totals are identical, and any deterministic displacement is recorded with leader lines |
| `panel_c_symbol_declutter_contract` | Rendered map pies satisfy the declared radius ceiling and have no positive-area symbol overlap after deterministic placement |
| `panel_order_contract` | Four-panel order and labels are A gene/allele matrix, B displayed-site MST, C world distribution, and D accession tree |
| `rendered_text_graphics_clearance` | Manual final-size review confirms that connectors, MST edges, nodes, axes, symbols, legends, and panel boundaries do not cross or cover glyphs; legends occupy reserved non-axis regions |
| `figure_text_english_only` | Extracted figure text contains no CJK characters and no donor gene/chromosome label |
| `formal_figure_visual_review` | Every exported figure has a manual-review row with status, review focus, and action taken |
| `sparse_allele_matrix_annotation` | A one-class allele matrix matches source cells and carries an explicit count-based explanation in the figure or delivered legend |
| `delivery_zip_integrity` | Customer ZIP passes `unzip -t`, has exactly `figure/`, `manuscript/`, `table/`, and `README.md` at top level, and excludes scripts, logs, internal QA, environment files, and temporary tests |
| `formal_haplotype_vcf_contract` | Customer source VCF has all approved post-QC SNP+InDel sites and source accessions; sample/site/SNP/InDel counts, REF/ALT, site/sample order, numeric phased GT, missing GT, and normalized GT hash match the source matrix |
| `formal_haplotype_vcf_index` | Delivered VCF is bgzip-readable, has a matching tabix `.tbi`, passes bcftools parsing and region query, and has a non-empty conversion audit |
| `vcf_role_separation` | Formal SNP+InDel haplotype VCF, canonical biallelic SNP-only population-genetics VCF, and tree-input SNP VCF have explicit roles and paths; neither analysis subset substitutes for the customer source VCF |
| `role_specific_vcf_sample_counts` | Each delivered VCF's sample/site counts are read from its own header/content and reconciled to its role-specific exclusion rules; QA does not hardcode equality across roles |
| `internal_qa_release_boundary` | All-PASS QA tables, logs, manifests, environment records, and visual-review evidence remain in the internal result tree and are absent from the customer ZIP |
| `trait_sample_overlap_selection` | For trait-first dual-dataset runs, the selected dataset has the largest phenotype sample overlap, or a tie stopped the workflow |
| `selected_dataset_manifest` | The final report records selected dataset, both candidate VCF paths, sample match counts, and metadata paths |
| `phenotype_join_integrity` | Every trait value used in statistics traces back to a phenotype source row and a matched VCF/sample metadata ID |
| `common_haplotype_required_tables` | Common-haplotype counts, assignment, node, edge, and audit tables exist |
| `common_haplotype_frequency_threshold` | The network uses the configured frequency threshold, default `>0.005` |
| `common_haplotype_count_consistency` | Haplotype counts match chromosome-level sample assignments |
| `common_haplotype_mst_edges` | MST edge count equals `common_haplotype_count - 1` when there is more than one node |
| `common_haplotype_group_columns` | Node table includes Wild, Cultivar, and Undefined group columns |
| `superrice_standard_vcf` | Reference-compatible mode has a bgzip/tabix-valid canonical biallelic SNP-only population-genetics VCF plus conversion audit; this does not satisfy `formal_haplotype_vcf_contract` |
| `detailed_subgroup_contract` | XI/GJ/Or/Undefined counts sum to the VCF sample count and Undefined is excluded from population genetics |
| `display_top80_contract` | Every major haplotype is present and frequency-ranked supporting haplotypes fill, but do not redefine, top 80 |
| `true_nj_tree_tip_contract` | The NJ Newick tip set equals the unique displayed haplotype set; it is not an MST plot renamed as NJ |
| `weir_cockerham_fst_plausibility` | Fst comes from vcftools `WEIGHTED_FST`, has explicit two-population keep lists, and finite values stay within the estimator's plausible range |
| `all_filter_ranges_distinct` | The all and filter views use different predeclared coordinate spans and different included-window counts |
| `callable_mask_disclosure` | MAF filtering, missingness filtering, and callable-mask availability are recorded in config and Methods |
| `area_centroid_map_boundary` | Original Area maps use a versioned centroid table, report mapping rate, and state that points are not accession sampling coordinates |
| `mst_edge_count` | Compact primary-haplotype MST has `N-1` edges |
| `nj_tip_contract` | Compact NJ Newick tips exactly equal the primary haplotype IDs |
| `release_manifest_sha256` | Every release file listed before packaging still matches its SHA256 |
| `recursive_table_readme_coverage` | Every directory at or below `table/`, including `table/` itself, contains `README.md` |
| `table_readme_item_inventory` | Each table README names and explains every immediate child file and subdirectory |
| `xlsx_table_readme_schema_coverage` | Every delivered workbook, sheet, actual column, row unit, denominator/unit, coordinate convention, allowed value, and missing-value rule is documented |
| `tsv_csv_table_readme_schema_coverage` | Every delivered TSV/CSV file and exact header column has a non-empty data-dictionary entry |
| `vcf_table_readme_contract` | VCF README covers fixed fields, FORMAT/GT, sample columns, phasing/missing encoding, sample/site counts, tabix index, and conversion audit |
| `table_readme_generator_validator_agreement` | A representative generator output passes the same four-column schema expected by the README validator, including literal `#CHROM` and file-specific VCF counts |
| `table_documentation_payload_invariance` | A documentation-only release uses a new version and preserves all accepted non-README scientific payload files byte-for-byte |
| `delivery_zip_utf8_member_names` | ZIP member names decode identically to customer-tree relative paths, including Chinese manuscript filenames, and member hashes equal the source release |

## Common Failures and Fixes

### `required_files` FAIL
- Check which file is missing from the error message.
- Most common: `formal_release_file_manifest.tsv` — means step 10 didn't complete.
- Re-run from step `10_formal_full_analysis`.

### `coordinate_contract` FAIL
- The `expected` list in `qa_formal_release.R` lines 20–32 doesn't match `formal_release_config.tsv`.
- Update `qa_formal_release.R` `expected` block for the new gene.

### `old_project_residue_guard` FAIL
- A chromosome name from the donor gene is still hardcoded somewhere in release text, scripts, or TSV summaries.
- Error message shows `path:linenum:content`. Fix those lines.
- Common source: copied labels such as `Chromosome 11`, `chromosome 11`, or `Chr11`.

### `pdf_text_chromosome_guard` FAIL
- A figure contains an unexpected chromosome label in the PDF text layer.
- Confirm the target chromosome from `project_contract.tsv` field `gene_chr_vcf`.
- Fix plotting code in `formal_full_analysis.R`; axis labels must be generated dynamically, for example:

```r
chromosome_title <- paste("Chromosome", gene_chr_vcf)
chromosome_sentence <- paste("chromosome", gene_chr_vcf)
labs(x = chromosome_title, ...)
labs(x = paste0("Position on ", chromosome_sentence, " (bp)"), ...)
```

- Re-run the formal pipeline after fixing. Do not patch exported PDFs manually.

### `figure_pdf_png_pairs` FAIL
- A figure was saved as PDF but the PNG export failed, or vice versa.
- Check `formal_full_analysis.R` figure export block; ensure both `pdf()` and `png()` calls are present.

### `trait_sample_overlap_selection` FAIL
- Confirm both 3K and 万份水稻 sample lists were extracted from the current VCF sources.
- Confirm phenotype sample IDs were normalized with the same rule as VCF sample IDs.
- If both datasets have the same matched sample count, do not choose silently; ask for a decision and record it in the audit.
- For `REPLACE_HOST` remote audits, activate `conda activate ngs` and prefer `fd` plus `rg` for locating files.

### `major_haplotype_threshold` FAIL
- A haplotype with n < 30 was included in the major haplotype set.
- Usually caused by `major_hap_threshold` parameter being set lower than 30.
- Verify line: `major_hap_threshold <- 30L` in `prepare_formal_inputs_siteqc.R`.

### Publication-compact threshold or XI/GJ statistics FAIL

- Rebuild the threshold audit from the all-haplotype assignment table; do not select rows from a prior top-N display table.
- Confirm that `n` counts unique carrier accessions and that XI/GJ frequency denominators count phased chromosome copies from retained complete-case accessions.
- Keep the frequency operator strict `>`; exactly 0.5% must remain excluded when the configured threshold is `0.005`.
- Recompute Fisher, BH, and Newcombe intervals from accession carrier/non-carrier tables. Do not use haplotype chromosome counts as independent test observations.
- Confirm XI and GJ denominators against `sample_retention_by_detailed_group.tsv` rather than raw metadata totals.

### Common-haplotype network QA FAIL
- Run `templates/scripts/qa_common_haplotype_network.R` with the same `--prefix`, `--out-dir`, and `--frequency-min` used to build the network.
- If `frequency_threshold` fails, confirm `common_haplotype_frequency_min` in `formal_release_config.tsv` and the `--frequency-min` CLI argument.
- If `count_consistency` fails, regenerate the network from the original interval genotype table; do not manually edit node or assignment tables.
- If `group_columns` fails, confirm the sample manifest contains `analysis_group` and that ambiguous samples are recorded as `Undefined`.
- If `mst_edge_count` fails, inspect `common_haplotype_edges.tsv`; for `N` common haplotypes, the MST must have `N - 1` edges unless `N = 0`.

### `formal_manifest_status` FAIL
- A file was modified after the manifest was generated.
- Re-run step 10 to regenerate all release files.

### `pdf_render_visual_check` FAIL
- `pdftoppm` not found: install poppler (`brew install poppler`).
- PDF render size < 1000 bytes: figure saved empty. Check R warnings in step 10 log.

### `editable_vector_pdf_no_embedded_raster` FAIL

- Run `pdfimages -list FIGURE.pdf` and identify the affected panel.
- A very short raster such as `300 x 3` commonly comes from ggplot2's default raster colour bar. Use `guide_colourbar(display="rectangles", nbin=100)` and re-export.
- Do not accept an embedded raster merely because it is not full-page; the compact-mode contract is fully vector PDF.

### `pdf_text_bbox_no_overlap` FAIL

- Render the affected Fig2 composite and paired panel at declared final size; confirm whether the collision is an axis-title/tick-label problem rather than an extraction duplicate.
- Increase the left plot margin together with the y-title `mgp` distance, or use a truthful compact scientific tick format. Moving only the plot margin can leave the title and tick label colliding.
- Keep ordinary text at or above the configured floor; do not make the test pass by shrinking axis or tick text.

### Global text overlap, clipping, or graphical coverage FAIL

- Run `pdftotext -bbox-layout` on the final composite and every dense panel. Fail on any positive-area word-box collision or word outside the page box; do not restrict the test to one known axis.
- Inspect the final-size PNG after the mechanical check. Poppler word boxes cannot detect a connector, MST edge, node, map symbol, grid line, or legend graphic crossing a glyph.
- Render geometry first and text last. Give coordinate, network, and edge labels an opaque white clearance; use deterministic candidate placement that rejects intersections with nodes and already occupied label boxes.
- If a gene endpoint equals or nearly coincides with the analysis endpoint, show one truthful endpoint label instead of overprinting the same coordinate twice.
- Reserve a separate legend band outside the plotting axes. Increase panel height or margins when needed; never solve coverage by shrinking ordinary text below the configured floor.

### `table_header_cell_containment` FAIL

- Treat the assigned table cell, not the PDF page, as the clipping boundary. A word can be inside the page and still be cut by or spill across a cell border.
- Measure the exact embedded-font text width/height after rotation and require explicit padding on all four sides; approximate character counts are not sufficient for release QA.
- Increase the header row height or switch an overlong rotated label to a centered horizontal multiline label, such as `carrier\nn`; never mask the overflow with a white rectangle.
- Inspect a crop of the densest header at final export DPI and record manual PASS only after every first and last glyph is visible inside its intended cell.

### `panel_a_b_distance_contract` or `cross_panel_visual_encoding_contract` FAIL

- Recompute each B-panel edge distance from the exact haplotype columns visible in A. If B intentionally uses all post-QC sites, relabel the basis explicitly and do not describe it as directly corresponding to the reduced A matrix.
- Draw one short perpendicular tick per SNP difference. Compare the rendered tick count against the audited edge table; do not use an unexplained number floating beside the edge.
- In C, aggregate records at each exact metadata coordinate into one pie. Use sector color for major haplotype and pie area for location accession `n`; verify that every sector total and the grand total equal the source table. If pies overlap, reduce the declared radius range and apply deterministic displacement with faint leader lines; save original and rendered coordinates and fail on residual positive-area overlap.
- In D, use saturated branch color for major haplotype. If an achromatic K5 line-style ring becomes a dense dark band, replace it with a spatially separate low-saturation outer-ring color band, a non-overlapping palette role, and its own legend.
- Confirm the narrative panel order is A gene/allele matrix, B displayed-site MST, C world distribution, and D accession tree.
- If exact variant coordinates are already connected to the A-panel table, omit redundant black dots on the gene model unless the marker color has a declared biological meaning.

### Compact figure or manual-review contract FAIL

- Compare `figure_manifest.tsv` with the actual figure directory; the declared compact contract is 2 composites, 6 main panels, and 3 supplementary figures unless config explicitly changes it.
- Regenerate contact sheets after the final plotting change, then inspect full-size dense panels.
- Ensure every primary haplotype is labelled in the all-haplotype rank plot; deterministic `ggrepel` is preferred over `check_overlap=TRUE`, which silently drops labels.
- Write manual-review rows only after inspection. File existence, DPI, and successful rendering cannot auto-authorize PASS.

### `sample_retention_by_group` FAIL or WARN
- Regenerate a summary from `sample_qc_status.tsv`; do not infer retained groups from raw metadata totals.
- If a group has zero retained samples or markedly lower retention than the comparison group, retain the haplotype result as descriptive only and remove/qualify group-frequency, selection, and population-history language.

### `sparse_allele_matrix_annotation` FAIL
- Count source cells by `feature_class` and `allele_class` in the display matrix.
- If one class occupies every cell, add the exact `cells = major haplotypes x variant sites` statement to the figure subtitle or delivered figure legend, then re-render from the plotting source.
- Do not hide a valid sparse panel merely to make the release look fuller.

### Reference-compatible superrice QA FAIL

- If Fst is outside a plausible range or differs from vcftools raw output, delete the custom estimator and rebuild from `--weir-fst-pop`; do not rescale the result.
- If `true_nj_tree_tip_contract` fails, rebuild the symmetric distance matrix and `ape::nj` Newick. An MST edge table cannot satisfy this check.
- If all/filter views contain the same windows, fix the coordinate contract and rerender; changing only the title is not sufficient.
- If a zero-retained group disappears from a map, add an explicit empty/not-applicable facet and carry the retained-cohort limitation into Methods and Results.
- If no callable-site mask exists, retain the warning and descriptive wording. Do not imply that nominal-window Pi is a callable-genome-corrected absolute estimate.

### Formal haplotype VCF or customer-package QA FAIL

- Rebuild the VCF from the approved post-QC SNP+InDel matrix, not from the population-genetics or tree-input SNP subset.
- Compare exact sample and site order before comparing hashes; a set-level match is insufficient for deterministic reconstruction.
- Normalize source and VCF GT to the same numeric phased representation before hashing. Permit only phased numeric GT and `.|.` in the delivered VCF.
- Recheck SNP/InDel and multiallelic counts against the conversion audit, then verify with `bcftools view`, `bcftools query`, and a tabix region query.
- Keep the conversion audit with the VCF and `.tbi` under `table/SourceData/VCF/`.
- If the ZIP contains QA workbooks, scripts, logs, manifests, contact sheets, or environment files, rebuild the customer tree from the four-entry whitelist. Do not delete the internal copies.
- Run internal QA before packaging and verify-only QA after packaging; customer ZIP integrity does not replace internal scientific QA.

### Recursive table README or schema coverage FAIL

- Enumerate the delivered `table/` tree itself; do not use a remembered file list from an older gene or release.
- Read every XLSX sheet and header with `openpyxl`, and every TSV/CSV header with `csv`. Bind each observed column to a curated definition and fail if any definition is absent.
- For each true table, document row unit, exact column meaning, unit/denominator, reference build and coordinate convention, allowed categorical values, and permitted missing values.
- For VCF, document fixed fields, `FORMAT/GT`, sample columns as a class, numeric allele-index mapping, phasing, missing GT, `.tbi`, and every conversion-audit metric.
- Run `templates/scripts/qa_table_readme_contract.py --table-dir RELEASE/table --output RESULTS/summary/table_readme_qa.tsv` and fix all failures before ZIP creation.
- For a documentation-only revision, create a new release version and compare SHA256 values against the accepted source release. Do not rebuild or silently alter figures, manuscripts, tables, VCF, or tree files.

## Adapting qa_formal_release.R for a New Gene

Do not hardcode the new gene's chromosome or coordinates in `qa_formal_release.R`. The QA script should read:

- `gene_id`
- `gene_chr_gff`
- `gene_chr_vcf`
- gene/promoter/analysis coordinates
- major haplotype threshold

from the project formal config and `summary/project_contract.tsv`.

The residue guard should be generic: construct the list of unexpected rice chromosomes from `1:12` minus the configured `gene_chr_vcf`, then fail on labels such as `Chromosome N`, `chromosome N`, or `ChrN` for any unexpected chromosome. This avoids the failure mode where the QA itself is still checking an older donor gene.

# QA Checklist — Formal Release

The QA script (`qa_formal_release.R`) runs a formal release QA suite. All checks must PASS. The current suite includes chromosome-label checks against both text files and the PDF text layer.

## Check Descriptions

| Check | What it verifies |
|-------|-----------------|
| `required_files` | All mandatory input files exist and are non-empty |
| `coordinate_contract` | Gene/promoter/analysis interval matches config |
| `filtered_vcf_variant_positions` | All haplotype-input variant positions are within analysis interval |
| `hapSummary_plot_positions` | All positions in gene_variant_sites.tsv are within analysis interval |
| `hapSummary_metadata_guard` | No sample count values (3023/3024) appear as variant positions |
| `major_haplotype_threshold` | All major haplotypes have n ≥ 30 |
| `major_haplotype_metrics` | Key metrics TSV is internally consistent |
| `figure_pdf_png_pairs` | Every PDF figure has a matching PNG |
| `formal_manifest_status` | All manifest rows show SHA256 match |
| `old_project_residue_guard` | No unexpected chromosome labels from a different gene appear in release text |
| `pdf_text_chromosome_guard` | Text extracted from all release PDFs has only the configured chromosome label, or no chromosome label |
| `pdf_render_visual_check` | Key PDFs render to PNG without corruption |

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

### `major_haplotype_threshold` FAIL
- A haplotype with n < 30 was included in the major haplotype set.
- Usually caused by `major_hap_threshold` parameter being set lower than 30.
- Verify line: `major_hap_threshold <- 30L` in `prepare_formal_inputs_sitebad03.R`.

### `formal_manifest_status` FAIL
- A file was modified after the manifest was generated.
- Re-run step 10 to regenerate all release files.

### `pdf_render_visual_check` FAIL
- `pdftoppm` not found: install poppler (`brew install poppler`).
- PDF render size < 1000 bytes: figure saved empty. Check R warnings in step 10 log.

## Adapting qa_formal_release.R for a New Gene

Do not hardcode the new gene's chromosome or coordinates in `qa_formal_release.R`. The QA script should read:

- `gene_id`
- `gene_chr_gff`
- `gene_chr_vcf`
- gene/promoter/analysis coordinates
- major haplotype threshold

from `results/{RUN_ID}/scripts/formal_release_config.tsv` and `summary/project_contract.tsv`.

The residue guard should be generic: construct the list of unexpected rice chromosomes from `1:12` minus the configured `gene_chr_vcf`, then fail on labels such as `Chromosome N`, `chromosome N`, or `ChrN` for any unexpected chromosome. This avoids the failure mode where the QA itself is still checking an older donor gene.

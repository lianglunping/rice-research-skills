# Wet-Lab Figure Decoding

Use this when explaining wet-lab panels to dry-lab readers. Mark simplified analogies as `【类比】`.

## Common Assays

- **Western blot (WB)**: darker/thicker band usually indicates higher detected protein abundance, but only relative to loading control and exposure. Check marker, target band size, loading control, replicate statement, and quantification.
- **Co-IP**: tests whether proteins are in the same pulled-down complex. Explain `Input` as total starting protein and `IP` as pulled-down fraction. Watch for IgG/empty-vector controls and reciprocal IP.
- **EMSA**: shifted band indicates slower migration of DNA/protein complex. Specificity needs competitor probes and mutated probes.
- **Yeast two-hybrid (Y2H)**: growth or color on selective medium suggests protein interaction in yeast. It is not direct in-planta proof.
- **Pull-down**: in-vitro or cell-extract binding support; check bait/prey, negative control, input, and reciprocal setup.
- **ChIP-qPCR/ChIP-seq**: enrichment suggests chromatin association at loci. Check antibody specificity, IgG/input control, peak calling, and biological replicates.
- **Dual-luciferase/reporter assay**: reporter activity supports regulatory effect on a promoter or element. Check internal control, empty vector, promoter mutant, and cell/protoplast context.
- **qRT-PCR**: transcript abundance, not protein activity. Check reference gene, tissue/time/treatment, normalization, and biological replicates.
- **Microscopy/localization**: signal location depends on marker, channel, merge, scale bar, negative control, and overexpression artifacts.
- **Histology/staining**: staining intensity is semi-quantitative unless quantified with consistent acquisition and controls.

## Omics and Genetics Visuals

- **Heatmap**: decode rows, columns, color scale, normalization, clustering, and whether values are expression, z-score, correlation, or enrichment.
- **PCA/UMAP/t-SNE**: separation suggests major variance structure, not causality. Check variance explained, batch effects, and sample labels.
- **Manhattan plot**: peaks indicate statistical association, not causal variant. Check model, population structure, correction threshold, LD, and candidate interval.
- **QTL plot**: interval and LOD/effect need population design and permutation threshold.
- **IGV/genome browser**: visually check reads, variants, split reads, coverage, strand, coordinate system, and sample lanes. Do not infer genotype quality without caller metrics.
- **Circos/synteny plots**: structural overview; do not treat as causal evidence without validation.

## Overinterpretation Alerts

- Interaction in yeast or vitro is not automatically in-planta interaction.
- Expression change is not automatically upstream regulation.
- Association peak is not automatically causal mutation.
- Overexpression phenotype may not represent natural allele function.
- Knockout phenotype can be background-dependent or pleiotropic.
- Representative images without quantification and replicates are weak evidence.

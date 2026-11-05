# Superrice Reference Two-Main-Figure v4

## Scope

Use `formal_mode=superrice_reference_two_mainfig_v4` when the client requests a screenshot-style gene/variant table, major-only haplotype relationship views, a sample-level tree containing all retained accessions, and exactly two main composite figures. This is a read-only derivative of a validated 万份水稻 reference-compatible source result; do not redo extraction, site QC, phasing, or retained-cohort selection.

## Frozen units and input roles

- Define the major set by phased chromosome-copy count `n >= 30`. Keep all haplotypes in internal source tables, but show only the frozen major IDs in the gene matrix, network, and centroid map.
- Keep the formal SNP+InDel VCF, canonical biallelic SNP-only population-genetics VCF, and tree SNP VCF as explicit roles. The formal SNP+InDel VCF, `.tbi`, and conversion audit are the only VCF trio delivered to the customer.
- Build the sample tree from all retained accessions. Its tips are accession IDs, not haplotype IDs. Use locus-level diploid allele-sharing 1-IBS and RapidNJ; describe it as a local sample relationship tree, not a genome-wide phylogeny.
- Record the absence of a callable mask. Without one, Pi and Tajima's D are nominal-window descriptive summaries; do not infer confirmed selection from local peaks.

## Figure contract

Deliver exactly two main composite figures:

1. `Fig1_Haplotype`: screenshot-style primary-transcript/promoter model plus major-variable allele table; major-only MST network; all-retained-accession IBS/NJ tree with a major-diplotype outer ring; and major-only Original Area centroid map.
2. `Fig2_SelectionScan`: Pi, Tajima's D, Weir-Cockerham weighted Fst, and log2 Pi ratio, each shown as a true broad/local pair in a 4 x 2 layout.

Reusable panels may be nested under their parent figure. They do not create a third main composite. Use English figure text, white background, colorblind-friendly mappings, editable vector PDF without embedded raster objects, and 600-dpi PNG.

颜色不得是唯一分组通道：窗口折线和样本树分支使用颜色与线型/点形冗余编码，主要单倍型地图使用颜色与点形冗余编码；图例同步显示这些编码，使灰度和常见色觉模拟下仍可辨认。

### Final-size typography and editable PDF contract

- Declare the `final physical size` in the project config before plotting. The default full-page width is 180 mm; design every panel at its final cell size rather than shrinking an 8-16 inch panel during composition.
- At final physical size, ordinary labels, axes, legends, annotations, table cells, and footnotes use at least `8.5 pt`; titles normally use 10-11 pt and panel labels use at least `13 pt`. Do not make a dense panel technically fit by lowering the text floor.
- Figure text is English and uses only `Arial` or `Times New Roman`. Helvetica, Symbol, Type 3 fonts, unembedded fonts, and rasterized text fail release QA. Gene labels remain italic within the allowed family.
- PDF text must remain `editable vector text`: `pdftotext` must recover it, `pdffonts` must report embedded allowed fonts, and no `/Image` XObject may be present. Lines, points, rectangles, tree branches, network edges, and map geometry should also remain vector whenever the plotting backend supports it.
- Mechanical font and object inspection does not replace human review. Inspect the latest render at 100% final size plus grayscale, protan, deutan, and tritan simulations; record legibility, clipping, crowding, axis-title/tick-label separation, and legend comprehension panel by panel. When long numeric ticks crowd a y-axis title, increase the title/tick spacing or use a truthful compact scientific notation; never lower the font below the declared floor.

### Chinese manuscript contract

The customer `manuscript/` directory is Chinese-first and contains substantive `材料与方法.md`, `结果与分析.md`, `图注.md`, and `参考文献.md` files generated from the frozen config and result tables.

- 材料与方法：逐节写明万份水稻变异图数据库、MSU Rice Genome Annotation Project Release 7、参考与注释文件、坐标与链方向、群体归并、site bad-rate 与完整材料规则、相位 SNP+InDel 单倍型、major threshold、MST、locus-level 1-IBS/RapidNJ sample tree、Original Area centroid、VCFtools Pi/Tajima's D/Weir-Cockerham Fst/Pi ratio、callable-mask 状态、软件版本、绘图与 QA。
- 结果与分析：从交付 TSV/XLSX 动态写入 retained denominator、post-QC SNP/InDel、all/major haplotypes、major coverage、promoter contribution、XI/GJ carrier statistics、tree tips、MST nodes/edges、mapped numerator/denominator 和 target-overlap popgen ranges。每节区分观察、统计关联与不能由当前证据支持的机制性结论。
- 图注：按论文 legend 体例逐 panel 解释。Fig1 必须逐 panel 定义 a-d；Fig2 必须逐 panel 定义 a-h。写清对象、颜色/线型、符号大小、统计单位、分母、窗口、坐标、branch-length display、Original Area centroid 限制、callable-mask 限制和对应 Source Data。
- 文稿 QA 不以字符数替代内容判断，但应拒绝单段摘要式 Methods/Results/Legends；数据库、软件版本、参数、panel 定义或证据边界缺一项均不得发布。
- 客户文稿只报告数据库、参考/注释版本、文件角色和可复现参数；不得出现 `/Users/`、`/home/`、Windows drive 等内部绝对路径。真实路径与哈希仅保留在项目内部 provenance/QA 证据中。

## Required QA

- Recompute the major set from all phased chromosome-copy assignments and match the frozen IDs and counts exactly.
- Require `Newick tips == retained accession IDs`, with unique tips and frozen group counts. Tree annotation may contain only the frozen major Hap IDs plus `Other`/`Other diplotypes`.
- Require network, map, and matrix ID sets to equal the major set; require a connected MST with `Hmajor - 1` edges.
- Include every post-QC promoter site in the promoter audit and mark whether it differentiates the major set.
- Verify four metrics x two scopes, distinct broad/local coordinates, non-empty finite windows, standard Weir-Cockerham Fst, no unapproved MAF filter, and callable-mask disclosure.
- Hash every actual scientific input before execution and compare the same allowlist after result QA and after release verification.
- Run programmatic PDF/PNG, text-layer, donor-residue, formal VCF, recursive table README, release manifest, and exact ZIP-member QA. Complete manual full-size, grayscale, protan, deutan, and tritan review before release.
- Reject any PDF containing fonts outside Arial/Times New Roman, Type 3 or unembedded fonts, missing editable text, embedded raster objects, a 1st-percentile Poppler word-box height below the configured final-size floor, or positive-area collisions between y-axis title words and numeric tick-label boxes. Parse each final composite's exact panel-label text operand after all PDF transforms and require every a-d/a-h label to meet `figure_panel_label_pt`; label counts or word-box height alone are insufficient.
- Validate the Chinese manuscript against required database, reference, software-version, parameter, section, per-panel legend, denominator, Source Data, and evidence-boundary fields.
- Reject customer manuscript files containing internal absolute paths; keep those paths only in internal provenance and QA evidence.
- Apply the same boundary to every customer-facing text artifact, including the formal-VCF conversion audit and generated README files. Preserve audit hashes and counts, but replace source-path values by customer-safe basenames before packaging, then scan the complete release and ZIP.

## Release boundary

The customer ZIP root is exactly `figure/`, `manuscript/`, `table/`, and `README.md`. Include exactly two main composite PDFs/PNGs, nested reusable panels, traceable Source Data, the branch-length Newick, and the configured formal SNP+InDel VCF trio. Keep scripts, logs, manifests, QA receipts, contact sheets, environments, and temporary tests internal.

Do not claim selection, domestication origin, introgression, functional causality, or breeding value from the network, tree, centroid map, or nominal-window statistics alone.

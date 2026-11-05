# Evidence audit and design translation

## Source identity and audit trail

- Article: Guo Y, et al. *Benchmarking short-read germline structural variant calling highlights advantages of using ensembles of tools and small impact of graph genome alignment*. Genome Biology (2026), DOI: `10.1186/s13059-026-04219-3`.
- Zotero parent key: `Q4KV4WDR`; PDF attachment key: `84FWEPCI`; Better BibTeX citekey: `guoBenchmarkingShortreadGermline2026`.
- Local source audit: 45-page born-digital PDF; SHA-256 `b90c9792470e741ff4fb08271826c1fafe7412f484abb77560657cbf999d20c3`.
- Extraction: `pypdf` layout extraction, 45/45 pages; main Figures 1–7, Tables 1–3, Results, Discussion, Methods, and data/code statements visually cross-checked against 170-dpi Poppler renders.
- Source status: the PDF is labelled “Article in Press” and an unedited manuscript. Final copy-editing could change pagination or correct errors.
- Code audit: authors' repository `cphgeno/SV-Benchmarking-Germline`, commit `ab05451527695eca56e0fc6e6d936db6a06d1ab7` as inspected on 2026-08-13.
- Missing evidence: the PDF states that supplementary files exist, but they were not embedded as auditable pages in the Zotero attachment. Claims that depend only on supplementary figures/tables are therefore not promoted to production rules.

Evidence labels used below:

- `[原文证据]`: direct methods, values, tables, or figures in the paper.
- `[原文结论]`: authors' stated interpretation.
- `[原文重构]`: reconstruction from the paper's methods, figures, and released code.
- `[外部检索补充]`: current primary documentation or official repository.
- `[专家研判]`: production or rice-transfer decision; not a paper result.

## Study design

`[原文证据]` The main benchmark used four Platinum Pedigree short-read samples (`NA12878`, `NA12879`, `NA12881`, `NA12882`) at about 30x. Their truth sets contained roughly 24,171–24,361 SVs per sample and were dominated by deletions and insertions; each sample contained only 38–45 inversion calls. See Methods and Table 2, PDF pages 30–32.

`[原文证据]` A complementary in-house set comprised 17 samples and 22 manually curated, clinically relevant events: 13 DEL, 6 DUP, and 3 INV. Candidates originated from Manta, CNVnator, DELLY, and LUMPY before IGV review, so this is neither a genome-wide nor caller-neutral truth set. See Results and Methods, PDF pages 16–19 and 33–34.

`[原文证据]` Fourteen callers were compared: Manta 1.6.0, Dysgu 1.6.2, DELLY2 1.1.3, Smoove 0.2.8, LUMPY 0.3.1, Tiddit 3.6.1, PopDel 1.5.0, GRIDSS2 2.13.2, CNVpytor 1.3.1, Octopus 0.7.4, Tardis 1.0.7, SvABA 1.2.0, Wham 1.8.0, and DRAGEN 4.3.13. These are benchmark versions, not current-version recommendations. See Table 3, PDF page 32.

`[原文证据]` Main evaluation used Truvari 4.2.2 with `--typeignore --passonly --pctseq 0` and remaining defaults, with high-confidence BED restriction where specified. No extra post hoc quality filters were applied before the main comparison. See Methods, PDF pages 34–36, and the released `config/pedigree.yaml` / `workflow/rules/truvari.smk`.

`[专家研判]` Because `--typeignore` permits class disagreement and `--pctseq 0` disables insertion-sequence similarity, the primary paper benchmark measures location-level event recovery more strongly than SV-class or inserted-sequence correctness. A production benchmark must add type-aware and sequence-aware views when those claims matter.

## Single-caller findings

`[原文证据]` Across the four pedigree samples, all tools showed higher precision than recall and rankings were stable across samples. DRAGEN had mean recall 0.36, precision 0.87, and F1 0.51. Among open-source callers, Manta and Dysgu each reached mean recall 0.26; Manta, Dysgu, and SvABA had mean F1 values 0.41, 0.37, and 0.35. Smoove, LUMPY, and PopDel showed high precision (0.94, 0.91, 0.90) but low recall. DELLY had mean precision 0.86, recall 0.15, and F1 0.26. See Figure 1 and Results, PDF pages 7–11.

`[原文证据]` Performance varied materially by SVTYPE and size. Deletions were generally easier; insertion recall decreased with size; inversion assessment was underpowered by the small truth-set count. See Figures 2–4 and Results, PDF pages 8–16.

`[原文证据]` In the 22-event in-house set, Manta and Tiddit recovered 21 events, Smoove 20, DRAGEN 19, Dysgu and SvABA 18, LUMPY 18, DELLY 13, and Octopus 0. DELLY recovered 12/13 DEL but 1/6 DUP and 0/3 INV. See Results, Figure 6, and Table 1, PDF pages 17, 19–20.

`[专家研判]` The disagreement between pedigree-wide and curated-event results is evidence against a universal ranking. It does not establish that Octopus, DELLY, or another caller is intrinsically unsuitable; ascertainment and event composition differ.

## Caller complementarity and ensembles

`[原文证据]` DRAGEN and Manta had high call overlap, consistent with related roots. LUMPY and Smoove shared 2,793 calls out of 2,800 and 2,896 calls, respectively. See Results and Figure 3, PDF pages 11–13.

`[专家研判]` Tool count is not independent evidence count. LUMPY plus Smoove must be treated as one algorithmic family for support summaries, even if both callsets are retained for wrapper comparison.

`[原文证据]` Exhaustive unions of up to 10 open-source callers showed a best F1 of 0.4899 (recall 0.397, precision 0.640) for Manta + Dysgu + Octopus + Smoove + LUMPY + PopDel + Tardis. The highest reported recall, 0.429, came from Manta + Dysgu + Octopus + DELLY + LUMPY + PopDel + Tardis, with F1 0.4886. See Results and Figure 5, PDF pages 15–18.

`[原文证据]` Requiring two or more tools to support a call performed worse than union ensembles across the reported metrics; maximum recall was 0.3573. See Results and Figure 5, PDF pages 15–18.

`[原文重构]` The exhaustive-search code does not merge production VCFs. It first uses Truvari-labelled TP/FN sets as a truth-coordinate key and clusters false positives within 50 bp, then computes unions and votes. This leaks benchmark truth into representation harmonization and cannot be run on unknown production calls. See released `workflow/scripts/exhaustive-search-ensemble.py`.

`[原文证据]` A production-like iterative SVDB merge used `--overlap 0.6 --bnd_distance 1000 --no_intra --no_var`. The best iterative F1 was 0.471 at four tools (Dysgu + Octopus + Manta + Tardis); adding SvABA as a fifth tool increased recall to 0.393 but reduced F1 to 0.460. See Results, Figure 5, and Methods, PDF pages 15–18 and 35–36.

`[原文结论]` The authors identify Dysgu, Octopus, Manta, and Tardis as a recurrent core across combination strategies, while emphasizing dependence on standardization, clustering, and the evaluation dataset.

`[专家研判]` Do not install that quartet as the default rice panel. It was selected on one human truth framework; Octopus recovered 0/22 in the separate curated set; and plant reference divergence, repeats, ploidy, and truth ascertainment differ. Use it as a hypothesis for a local pilot only.

## Graph alignment

`[原文证据]` The graph comparison used a Minigraph-Cactus graph built from 88 HPRC haploid assemblies plus GRCh38 and T2T-CHM13, aligned with vg giraffe and surjected for downstream calling. Only `NA12878` was used for the graph-versus-linear caller comparison. See Methods and Results, PDF pages 13–17 and 31–33.

`[原文证据]` Aggregate graph effects were usually comparable or slightly worse, but Dysgu improved substantially and several callers showed smaller positive or negative changes. Some callers had true-positive callset Jaccard overlap below 50% between graph and linear alignments despite small F1 changes. See Figure 4 and Results, PDF pages 14–17.

`[原文结论]` The authors characterize the overall effect of graph alignment as small and caller-dependent.

`[专家研判]` A small average metric change does not justify discarding the graph branch when complementary discovery matters. Report overlap and rescued events, not only F1. Conversely, one human HPRC result is insufficient to claim benefit for a rice graph.

## Frequency filtering and resource findings

`[原文证据]` A Manta frequency database from 1,600 unrelated clinical samples was used to remove events with frequency above 0.01. In `NA12878`, false positives fell from 805 to 518 and true positives from 5,836 to 3,408; precision changed only from 0.868 to 0.879. See Results, PDF pages 17 and 19. The detailed plots are in Additional file 1: Figure S4 and were not visually audited from the Zotero PDF.

`[原文结论]` Frequency information can reduce review burden but is more appropriate for prioritization than strict exclusion.

`[专家研判]` In induced-mutant and breeding studies, preserve the unfiltered layer. Parent/background-panel frequency is evidence, not a causal filter; common alleles may be useful and rare alleles may be unrelated to mutagenesis.

`[原文证据]` Each caller was allocated 40 threads and 80 GB. Dysgu was among the fastest and most resource-efficient; Manta also had short runtime and useful parallelism. SvABA and Octopus used high CPU/time; CNVpytor had the longest wall time and low CPU utilization; GRIDSS reached the 80-GB allocation, so its true peak was censored. See Results and Figure 7, PDF pages 19–21.

`[专家研判]` These resource measurements are hardware-, implementation-, sample-, and coverage-specific. Use them for pilot scheduling order, not fixed cluster requests.

## Critical limitations and stop rules

- `[原文证据]` The principal data are human, approximately 30x, and limited to four related pedigree samples. Graph analysis and some region-restricted analyses use only `NA12878`.
- `[原文证据]` The truth set may favor callers or representations involved in its construction; the authors describe this truth-set/tool-optimization conundrum.
- `[原文证据]` The in-house events were nominated from four callers before manual review, creating caller and event-complexity ascertainment bias.
- `[原文证据]` Inversion counts are too small for strong ranking claims.
- `[专家研判]` Stop and label the result exploratory when confident regions are absent, truth data are reused for tuning and reporting, supplementary-only claims cannot be audited, or graph and linear results do not share a documented coordinate reference.
- `[专家研判]` Do not claim rice sensitivity/specificity, a universal coverage cutoff, or causality from this paper.

## Translation into the skill

| Paper observation | Production rule | Rice-specific consequence |
|---|---|---|
| Union outperformed two-caller voting in this benchmark | Preserve union, supported, and rescued-singleton views | Do not hard-drop singletons before parent/segregation/orthogonal review |
| Caller performance is SVTYPE/size dependent | Select and benchmark by target strata | Include repeat, subpopulation, and assembly-divergence strata |
| LUMPY/Smoove overlap is nearly complete | Count algorithm families, not wrappers | Avoid pseudo-replication in support scores |
| Iterative SVDB ensemble had a local optimum | Tune merge and stopping rules on development truth | Validate on independent lines/events; do not import human optimum |
| Graph mean effect was small but overlap could be low | Keep linear baseline and report callset complementarity | Build/test a rice-representative graph before any production claim |
| Frequency filtering cut both FP and TP | Treat frequency as prioritization | Keep induced and breeding-relevant candidates in an auditable layer |

## Current primary sources checked

- Paper workflow repository: <https://github.com/cphgeno/SV-Benchmarking-Germline>
- Truvari official repository and current command overview: <https://github.com/ACEnglish/truvari>
- Dysgu official repository and paired-end workflow: <https://github.com/kcleal/dysgu>
- SVDB official repository and merge/database documentation: <https://github.com/J35P312/SVDB>
- SURVIVOR official repository: <https://github.com/fritzsedlazeck/SURVIVOR>

The article's pinned versions and commands remain the reproducibility target for reproducing its benchmark. Production runs must capture installed versions and re-check `--help`; current official interfaces can diverge.

#!/usr/bin/env python3
"""Build the customer release tree after result QA; ZIP creation is separate."""
from __future__ import annotations
import argparse,csv,shutil
from pathlib import Path
def rows(p):
 with Path(p).open(newline='') as h:return list(csv.DictReader(h,delimiter='\t'))
def cfg(p):return {r['field']:r['value'] for r in rows(p)}
def cp(s,d):Path(d).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s,d)
def customer_safe_conversion_audit(source,destination):
 """Preserve audit values while replacing workstation paths by basenames."""
 with Path(source).open(newline='') as h:records=list(csv.DictReader(h,delimiter='\t'))
 for record in records:
  if record.get('metric') in {'source_matrix','vcf'}:record['value']=Path(record['value']).name
 with Path(destination).open('w',newline='') as h:
  w=csv.DictWriter(h,fieldnames=['metric','value'],delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(records)
def main():
 a=argparse.ArgumentParser();a.add_argument('--config',required=True);a.add_argument('--project-root',required=True);a.add_argument('--result-dir',required=True);a.add_argument('--release-dir',required=True);x=a.parse_args();c=cfg(x.config);r=Path(x.result_dir);rel=Path(x.release_dir);project=Path(x.project_root).resolve()
 if rel.exists():shutil.rmtree(rel)
 for d in ('figure','manuscript','table/SourceData/VCF','table/SourceData/TSV'): (rel/d).mkdir(parents=True)
 for n in ('Fig1_Haplotype.pdf','Fig1_Haplotype.png'):
  cp(r/'figures'/'Fig1_Haplotype'/n,rel/'figure'/'Fig1_Haplotype'/n)
 for n in ('Fig2_SelectionScan.pdf','Fig2_SelectionScan.png'):
  cp(r/'figures'/'Fig2_SelectionScan'/n,rel/'figure'/'Fig2_SelectionScan'/n)
 for stem in ('var_gene_vat_tab','major_network','all_accession_tree','major_area_map'):
  for ext in ('.pdf','.png'):cp(r/'figures'/'work'/f'{stem}{ext}',rel/'figure'/'Fig1_Haplotype'/'panels'/f'{stem}{ext}')
 for k in ('Pi','TajimaD','Fst','Pi_ratio'):
  for ext in ('.pdf','.png'):cp(r/'figures'/'Fig2_SelectionScan'/'panels'/f'{k}_broad_local{ext}',rel/'figure'/'Fig2_SelectionScan'/'panels'/f'{k}_broad_local{ext}')
 for p in sorted((r/'manuscript').glob('*.md')):cp(p,rel/'manuscript'/p.name)
 # The formal haplotype VCF is copied with its index and conversion audit; never substitute popgen/tree VCFs.
 v=Path(c['formal_haplotype_vcf']); v=v if v.is_absolute() else project/v
 tbi=Path(c['formal_haplotype_vcf_tbi']); tbi=tbi if tbi.is_absolute() else project/tbi
 audit=Path(c['formal_haplotype_vcf_conversion_audit']); audit=audit if audit.is_absolute() else project/audit
 if not v.is_file() or not tbi.is_file() or not audit.is_file(): raise SystemExit('configured formal VCF, tabix index, and conversion audit are all required')
 cp(v,rel/'table/SourceData/VCF'/v.name); cp(tbi,rel/'table/SourceData/VCF'/tbi.name); customer_safe_conversion_audit(audit,rel/'table/SourceData/VCF'/audit.name)
 source_tables=(
  r/'haplotype'/'primary_haplotype_summary.tsv',r/'haplotype'/'primary_haplotype_assignment.tsv',
  r/'plot_data'/'primary_variable_site_summary.tsv',r/'plot_data'/'primary_variable_allele_matrix.tsv',
  r/'plot_data'/'gene_feature_segments.tsv',r/'plot_data'/'promoter_site_audit.tsv',
  r/'plot_data'/'haplotype_carrier_counts_by_population.tsv',r/'plot_data'/'cohort_population_counts.tsv',
  r/'tree'/'primary_haplotype_nodes.tsv',r/'tree'/'major_haplotype_mst_edges.tsv',
  r/'map'/'primary_haplotype_area_centroid_counts.tsv',
  r/'plot_data'/'sample_tree_reference_annotation.tsv',r/'plot_data'/'sample_tree_diplotype_counts.tsv',
  r/'plot_data'/'selection_window_contract.tsv',r/'popgen'/'pi_tidy.tsv',r/'popgen'/'tajimad_tidy.tsv',
  r/'popgen'/'fst_tidy.tsv',r/'popgen'/'pi_ratio_tidy.tsv'
 )
 for p in source_tables:
  cp(p,rel/'table/SourceData/TSV'/p.name)
 cp(r/'tree'/'retained_accession_nj.newick',rel/'table/SourceData/TSV'/f"{c['gene_id']}.retained_accession_IBS_NJ.newick")
 (rel/'README.md').write_text(f"# {c['gene_id']} two-main-figure release\n\nThis package contains exactly two main composites. Major haplotypes are phased chromosome-copy patterns with n >= 30. Geographic points are Original Area centroids, not sampling coordinates. Without a callable mask, Pi and Tajima's D are descriptive nominal-window summaries.\n")
 print(f'[release-v4] tree={rel}')
if __name__=='__main__':main()

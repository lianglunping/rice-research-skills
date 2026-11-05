#!/usr/bin/env python3
import argparse,csv
from pathlib import Path
REQ={'formal_mode','source_result_dir','run_id','release_id','delivery_zip','reference_primary_transcript','png_dpi','popgen_callable_mask','popgen_all_start','popgen_all_end','popgen_filter_start','popgen_filter_end','popgen_maf_filter','tree_ring_gap_fraction','tree_ring_point_size','tree_branch_linewidth','tree_diplotype_min_accessions','frozen_major_haplotype_ids','frozen_major_haplotype_copy_counts','frozen_broad_window','frozen_local_window','formal_haplotype_vcf','formal_haplotype_vcf_tbi','formal_haplotype_vcf_conversion_audit','population_genetics_vcf','tree_snp_vcf','source_required_relpaths','project_required_config_keys','external_required_config_keys','expected_complete_accessions','expected_tree_XI_accessions','expected_tree_GJ_accessions','expected_tree_Or_accessions','expected_tree_Undefined_accessions','figure_final_width_mm','fig1_final_height_mm','fig2_final_height_mm','figure_font_family','figure_min_font_pt','figure_base_font_pt','figure_panel_label_pt','pdf_allowed_fonts','pdf_min_word_bbox_height_pt','pdf_require_editable_text','pdf_reject_type3','pdf_reject_raster','software_python','software_matplotlib','software_r','software_cairo','software_ape','software_ggplot2','software_vcftools','software_plink','software_rapidnj','software_bcftools','software_pypdf'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--project-root',required=True);a=p.parse_args()
 with open(a.config,newline='') as h:c={r['field']:r['value'] for r in csv.DictReader(h,delimiter='\t')}
 bad=REQ-set(c)
 if c.get('formal_mode')!='superrice_reference_two_mainfig_v4' or bad:raise SystemExit(f'bad config: {sorted(bad)}')
 if c['reference_primary_transcript']!=f"{c['gene_id']}.1":raise SystemExit('primary transcript must be frozen explicitly for this mode')
 if c['png_dpi']!='600' or c['popgen_callable_mask'] not in {'unavailable','available'}:raise SystemExit('frozen display/mask contract failed')
 if c['figure_font_family'] not in {'Arial','Times New Roman'} or c['pdf_allowed_fonts']!='Arial,Times New Roman':raise SystemExit('font allowlist contract failed')
 if abs(float(c['figure_final_width_mm'])-180)>1e-6 or abs(float(c['fig1_final_height_mm'])-260)>1e-6 or abs(float(c['fig2_final_height_mm'])-260)>1e-6 or float(c['figure_min_font_pt'])<8.5 or float(c['figure_base_font_pt'])<float(c['figure_min_font_pt']) or float(c['figure_panel_label_pt'])<13 or float(c['pdf_min_word_bbox_height_pt'])<6.0:raise SystemExit('final-size typography contract failed')
 if any(c[k]!='TRUE' for k in ('pdf_require_editable_text','pdf_reject_type3','pdf_reject_raster')):raise SystemExit('editable vector PDF contract failed')
 if any(not c[k].strip() or c[k].startswith('REPLACE_') for k in ('software_python','software_matplotlib','software_r','software_cairo','software_ape','software_ggplot2','software_vcftools','software_plink','software_rapidnj','software_bcftools','software_pypdf')):raise SystemExit('software version registry is incomplete')
 gene=c['gene_id']
 prefix=f'formal_superrice_{gene}_two_mainfig_'
 if not c['run_id'].startswith(prefix):raise SystemExit('run id does not match gene and two-mainfig mode')
 version=c['run_id'][len(prefix):]
 if c['release_id']!=f'release_{c["run_id"]}' or c['delivery_zip']!=f'{gene}_haplotype_two_mainfig_{version}.zip':raise SystemExit('release paths are not version-consistent')
 if int(c['popgen_all_end'])-int(c['popgen_all_start'])<=int(c['popgen_filter_end'])-int(c['popgen_filter_start']):raise SystemExit('broad window must be wider than local window')
 if c['popgen_maf_filter']!='none':raise SystemExit('TajimaD/Pi MAF filter was not approved')
 root=Path(a.project_root)
 for k in ('source_result_dir','formal_haplotype_vcf','formal_haplotype_vcf_tbi','formal_haplotype_vcf_conversion_audit','population_genetics_vcf','tree_snp_vcf'):
  x=Path(c[k]);x=x if x.is_absolute() else root/x
  if not x.exists():raise SystemExit(f'missing frozen path: {k}')
 for k in [x for x in c['project_required_config_keys'].split(',') if x]:
  path=Path(c[k]);path=path if path.is_absolute() else root/path
  if not path.is_file():raise SystemExit(f'missing project input: {k}')
 for k in [x for x in c['external_required_config_keys'].split(',') if x]:
  if not Path(c[k]).is_file():raise SystemExit(f'missing external input: {k}')
 print('PASS\tconfig frozen fields and source schema paths')
if __name__=='__main__':main()

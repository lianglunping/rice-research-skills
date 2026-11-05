#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,sys
from pathlib import Path
STEMS=['Fig1_Haplotype/Fig1_Haplotype','Fig1_Haplotype/panels/var_gene_vat_tab','Fig1_Haplotype/panels/major_network','Fig1_Haplotype/panels/all_accession_tree','Fig1_Haplotype/panels/major_area_map','Fig2_SelectionScan/Fig2_SelectionScan','Fig2_SelectionScan/panels/Pi_broad_local','Fig2_SelectionScan/panels/TajimaD_broad_local','Fig2_SelectionScan/panels/Fst_broad_local','Fig2_SelectionScan/panels/Pi_ratio_broad_local']
def main():
 p=argparse.ArgumentParser();p.add_argument('--result-dir',required=True);p.add_argument('--review');p.add_argument('--template-only',action='store_true');a=p.parse_args();target=Path(a.result_dir)/'summary'/'figure_visual_review_template.tsv';target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists():
   with target.open('w',newline='') as h:w=csv.DictWriter(h,fieldnames=['relative_stem','review_focus','visual_status','action_taken'],delimiter='\t');w.writeheader();w.writerows({'relative_stem':s,'review_focus':'full-size readability; labels; clipping; scientific semantics','visual_status':'PENDING','action_taken':''} for s in STEMS)
 manifest=Path(a.result_dir)/'summary'/'figure_manifest.tsv'
 with manifest.open('w',newline='') as h:
  w=csv.DictWriter(h,fieldnames=['relative_stem','role','parent'],delimiter='\t');w.writeheader()
  for s in STEMS:w.writerow({'relative_stem':s,'role':'main_composite' if s in ('Fig1_Haplotype/Fig1_Haplotype','Fig2_SelectionScan/Fig2_SelectionScan') else 'main_panel','parent':'Fig1' if s.startswith('Fig1') else 'Fig2'})
 if a.template_only:return
 review=Path(a.review) if a.review else target
 with review.open(newline='') as h:rs=list(csv.DictReader(h,delimiter='\t'))
 good=len(rs)==len(STEMS) and {x.get('relative_stem') for x in rs}==set(STEMS) and all(x.get('visual_status') in {'PASS','PASS_AFTER_FIX'} and x.get('action_taken','').strip() for x in rs)
 if not good:print(f'visual-review gate HOLD: complete {target}',file=sys.stderr);raise SystemExit(3)
 out=Path(a.result_dir)/'summary'/'figure_visual_review.tsv';out.write_text(review.read_text())
if __name__=='__main__':main()

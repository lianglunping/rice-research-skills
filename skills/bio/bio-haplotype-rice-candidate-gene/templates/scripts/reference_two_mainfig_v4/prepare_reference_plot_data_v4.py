#!/usr/bin/env python3
"""Create the v4 plotting contract from the A04 derivative only.

This adapter deliberately reads the A04 primary summary/assignment/matrix/map/
tree products and a validated source popgen directory.  It does not consult
legacy figure manifests, supplementary figures, sensitivity products, or any
fixed donor-tree filename.
"""
from __future__ import annotations
import argparse, csv, hashlib, shutil
from pathlib import Path

def rows(p):
    with Path(p).open(newline="") as h: return list(csv.DictReader(h, delimiter="\t"))
def cfg(p): return {r["field"]:r["value"] for r in rows(p)}
def put(p, data, fields=None):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    fields=fields or list(data[0])
    with p.open("w",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields,delimiter="\t",lineterminator="\n",extrasaction="ignore");w.writeheader();w.writerows(data)
def sha(p):
    x=hashlib.sha256()
    with Path(p).open("rb") as h:
        for b in iter(lambda:h.read(1048576),b""):x.update(b)
    return x.hexdigest()
def copy(src,dst):
    Path(dst).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',required=True);ap.add_argument('--project-root',required=True);ap.add_argument('--result-dir',required=True);a=ap.parse_args()
    c=cfg(a.config); result=Path(a.result_dir).resolve(); project=Path(a.project_root).resolve(); source=Path(c['source_result_dir']); source=(source if source.is_absolute() else project/source).resolve()
    if c.get('formal_mode')!='superrice_reference_two_mainfig_v4': raise SystemExit('wrong formal_mode')
    primary=rows(result/'haplotype/primary_haplotype_summary.tsv')
    if not primary: raise SystemExit('A04 primary_haplotype_summary is empty')
    minimum=int(c.get('major_haplotype_min_chromosome_count','30'))
    for r in primary:
        if int(r['haplotype_chromosome_count'])<minimum: raise SystemExit('non-major haplotype in primary summary')
    ids=[r['primary_haplotype_id'] for r in primary]
    plot=result/'plot_data'; plot.mkdir(exist_ok=True)
    # exact set QA identities
    put(plot/'network_major_ids.tsv',[{'haplotype_id':x} for x in ids])
    put(plot/'map_major_ids.tsv',[{'haplotype_id':x} for x in ids])
    put(plot/'matrix_major_ids.tsv',[{'haplotype_id':x} for x in ids])
    # Keep plot data in direct, typed, v10-readable form.
    sites=rows(plot/'primary_variable_site_summary.tsv')
    for i,r in enumerate(sites,1):
        r['display_site_order']=str(i);r['site_label']=r.get('variant_id',f'S{i:02d}');r['highlight_protein_altering']='True' if any(k in r.get('coding_consequence','').lower() for k in ('missense','stop','frameshift')) else 'False';r['functional_label']=r.get('coding_consequence','NA')
    put(plot/'major_haplotype_display_sites.tsv',sites)
    wide=rows(plot/'primary_variable_allele_matrix.tsv')
    for r in wide:
        r['primary_haplotype_id']=r.get('primary_haplotype_id',r.get('haplotype_id',''))
        for s in sites: r.setdefault(s['site_label'],r.get(s['variant_id'],'NA'))
    put(plot/'major_haplotype_allele_matrix.tsv',wide)
    assignments=rows(result/'haplotype/primary_haplotype_assignment.tsv')
    counts=[]
    for h in ids:
        r={'primary_haplotype_id':h,'XI':'0','GJ':'0','Or':'0','Undefined':'0','Total':'0'}
        carriers={x['sample_id'] for x in assignments if x['primary_haplotype_id']==h}
        for g in ('XI','GJ','Or','Undefined'):
            r[g]=str(len({x['sample_id'] for x in assignments if x['primary_haplotype_id']==h and x.get('detailed_group')==g}))
        r['Total']=str(len(carriers));counts.append(r)
    put(plot/'haplotype_carrier_counts_by_population.tsv',counts)
    retention=rows(result/'summary/sample_retention_by_detailed_group.tsv')
    cohort=[{'population_group':r['detailed_group'],'accession_count':r['complete_samples']} for r in retention if r['detailed_group'] in {'XI','GJ','Or','Undefined'}]
    cohort.append({'population_group':'Total','accession_count':str(sum(int(x['accession_count']) for x in cohort))})
    put(plot/'cohort_population_counts.tsv',cohort)
    # A04 retains detailed gene features. Promoter audit is constructed only from its own variable sites.
    features=rows(plot/'gene_feature_segments_detailed.tsv'); put(plot/'gene_feature_segments.tsv',features)
    # Audit every post-QC promoter site, rather than only display/major-variable sites.
    source_variants=rows(source/'haplotype'/f"{c['gene_id']}.superrice_variant_table.tsv")
    major_variable={x['variant_id'] for x in sites}
    promoter=[dict(x,differentiates_primary_haplotypes='True' if x['variant_id'] in major_variable else 'False') for x in source_variants if x.get('feature_class','').lower()=='promoter']
    put(plot/'promoter_site_audit.tsv',promoter, list(promoter[0]) if promoter else ['variant_id','POS','differentiates_primary_haplotypes'])
    nodes=rows(result/'tree/primary_haplotype_nodes.tsv');put(plot/'major_network_nodes.tsv',nodes)
    edges=rows(result/'tree/primary_haplotype_mst_edges.tsv');put(plot/'major_network_edges.tsv',edges)
    put(result/'tree/major_haplotype_mst_edges.tsv',[{'from_haplotype_id':x['hap_a'],'to_haplotype_id':x['hap_b'],'distance':x.get('distance','')} for x in edges])
    maprows=rows(result/'map/primary_haplotype_area_centroid_counts.tsv');put(plot/'hap_map_all_centroid_counts.tsv',maprows)
    # The all-accession tree basename is configuration-derived, never a hard-coded legacy name.
    tree_src=result/'tree'/f"{c['tree_basename']}_1ibs_RapidNJ.newick"
    if not tree_src.exists(): raise SystemExit(f'missing dynamic A04 tree: {tree_src.name}')
    copy(tree_src,result/'tree/retained_accession_nj.newick')
    # Tree annotation must cover every retained accession, not only major-haplotype carriers.
    source_manifest=rows(source/'haplotype'/f"{c['gene_id']}.superrice_sample_manifest_detailed.tsv")
    retained_list=result/'tree'/'retained_accessions.list'
    retained={x.strip() for x in retained_list.read_text().splitlines() if x.strip()} if retained_list.exists() else {x['sample_id'] for x in source_manifest}
    manifest_by_id={x['sample_id']:x for x in source_manifest}
    dip_rows=rows(result/'haplotype/accession_indel_diplotype.tsv')
    dip_by_id={x['sample_id']:x for x in dip_rows}
    raw_diplotypes={}
    for sid in sorted(retained):
        if sid not in manifest_by_id or sid not in dip_by_id: raise SystemExit(f'tree accession missing source or diplotype annotation: {sid}')
        x=dip_by_id[sid]
        copies=[x.get('chromosome1_primary_haplotype_id','') or 'Other',x.get('chromosome2_primary_haplotype_id','') or 'Other']
        copies=sorted(copies,key=lambda value:(value=='Other',value))
        raw_diplotypes[sid]='/'.join(copies)
    threshold=int(c.get('tree_diplotype_min_accessions','30'))
    dip_counts={value:sum(item==value for item in raw_diplotypes.values()) for value in set(raw_diplotypes.values())}
    ann=[]
    for sid in sorted(retained):
        raw=raw_diplotypes[sid]; display=raw if dip_counts[raw]>=threshold else 'Other diplotypes'
        ann.append({'sample_id':sid,'population_group':manifest_by_id[sid].get('detailed_group','Undefined'),'major_diplotype':display,'raw_major_diplotype':raw})
    put(plot/'sample_tree_reference_annotation.tsv',ann)
    put(plot/'sample_tree_diplotype_counts.tsv',[{'major_diplotype':key,'accession_count':value,'displayed_in_tree_ring':'True' if value>=threshold else 'False'} for key,value in sorted(dip_counts.items(),key=lambda item:(-item[1],item[0]))])
    put(result/'tree/retained_accessions.tsv',[{'sample_id':x['sample_id']} for x in ann])
    # Population-genetic inputs are copied from the declared validated base, rather than a v5 figure artifact.
    for name in ('pi_tidy.tsv','tajimad_tidy.tsv','fst_tidy.tsv','pi_ratio_tidy.tsv'):
        copy(source/'popgen'/name,result/'popgen'/name)
    put(result/'summary/plot_data_contract_v4.tsv',[{'key':'major_haplotype_ids','value':','.join(ids)},{'key':'tree_basename','value':c['tree_basename']},{'key':'source_result_dir','value':str(source)}])
    print(f'[prepare-v4] major={len(ids)} sites={len(sites)} tree={tree_src.name}')
if __name__=='__main__': main()

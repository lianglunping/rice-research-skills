#!/usr/bin/env python3
"""Generate recursive customer table documentation from actual delivered files."""
from __future__ import annotations
import argparse,csv,gzip
from pathlib import Path

def rows(path):
 with path.open(newline='') as h:return list(csv.DictReader(h,delimiter='\t'))
def config(path):return {row['field']:row['value'] for row in rows(Path(path))}
def purpose(path):
 if path.is_dir():return '子目录；其 README.md 记录该目录的逐文件和逐字段数据字典。'
 name=path.name
 if name.endswith('.vcf.gz'):return '正式 post-QC SNP+InDel 相位 VCF；这是客户单倍型源 VCF，不是 popgen/tree SNP 子集。'
 if name.endswith('.vcf.gz.tbi'):return '上述 bgzip VCF 的 tabix 索引；不是独立生物学结果表。'
 if name.endswith('.newick'):return '全部 retained accessions 的局部 IBS/RapidNJ 树，含分支长度。'
 if 'conversion_audit' in name:return '正式 VCF 转换、计数、GT hash 和可读性审计。'
 return '两张主图的可追溯 Source Data；字段定义见本 README 对应小节。'
def row_unit(name):
 rules=(('assignment','一条 retained accession 的一条 phased chromosome copy assignment'),('variant','一个 post-QC variant site'),('allele_matrix','一个 major haplotype'),('feature','一个 primary-transcript feature segment'),('promoter','一个 post-QC promoter site'),('carrier_counts','一个 major haplotype'),('cohort','一个 retained population group'),('nodes','一个 major haplotype network node'),('edges','一条 major-haplotype MST edge'),('centroid','一个 Original Area centroid x major haplotype x group aggregation'),('sample_tree_reference','一个 retained accession tree tip'),('diplotype_counts','一个 major-diplotype display category'),('selection_window','一个 metric x scope contract row'),('pi_','一个 population x software-native genomic window'),('tajima','一个 population x software-native genomic window'),('fst_','一个 population pair x software-native genomic window'))
 return next((value for key,value in rules if key in name.lower()),'一个由文件名所述分析单位构成的记录')
def field_definition(name,field):
 f=field.lower();n=name.lower()
 exact={
  'sample_id':'材料唯一标识；一个 retained accession；不允许缺失。','primary_haplotype_id':'major haplotype ID；允许 H001 等已冻结主单倍型值；非主单倍型处为空。','all_haplotype_id':'全量单倍型 ID；不允许缺失。','haplotype_id':'单倍型 ID；不允许缺失。','variant_id':'post-QC 变异唯一标识；不允许缺失。','chrom':'MSU_osa1r7 染色体编号；不允许缺失。','pos':'MSU_osa1r7 的 1-based VCF 坐标，单位 bp；不允许缺失。','ref':'MSU_osa1r7 REF allele；不允许缺失。','alt':'VCF ALT allele 列，可含逗号分隔多等位；不允许缺失。','format':'VCF FORMAT 定义；正式 VCF 中为 GT。','gt':'数字等位索引的 phased genotype，分隔符为 |；缺失基因型为 .|.。','detailed_group':'保留群体标签，允许 XI、GJ、Or、Undefined；不允许缺失。','population_group':'保留群体标签，允许 XI、GJ、Or、Undefined、Total；不允许缺失。','major_diplotype':'树外环显示类别；仅含冻结 major Hap ID、Other 或 Other diplotypes；不允许缺失。','raw_major_diplotype':'将每条非主单倍型 chromosome copy 记为 Other 后的两拷贝组合；不允许缺失。','scope':'显示范围，允许 broad 或 local；不允许缺失。','metric':'统计量或审计指标名称；允许值由该表实际行给出；不允许缺失。','value':'对应 metric 的原始值；单位和允许值由 metric 定义；不允许缺失。','callable_mask':'callable-site mask 状态；本项目为 unavailable；不允许缺失。','interpretation':'证据边界；无 callable mask 时为 nominal-window descriptive summary；不允许缺失。'}
 if f in exact:return exact[f]
 if f in {'bin_start','bin_end','mid','start','end'}:return '软件原生窗口或区段坐标，基于 MSU_osa1r7；单位 bp；缺失值不允许。'
 if f in {'longitude','latitude'}:return 'Original Area 质心经纬度，单位 decimal degrees；不是 accession 采样坐标；映射失败时允许 NA。'
 if 'count' in f or f.endswith('_n') or f=='variant_count':
  denominator='retained accessions' if 'carrier' in f or 'accession' in f or 'cohort' in n else 'phased chromosome copies' if 'chromosome' in f else '该行所述离散对象'
  return f'非负整数计数；计数单位/分母为 {denominator}；零允许，缺失值不允许。'
 if 'frequency' in f or 'rate' in f:return '比例值；分母由字段名所述 retained accessions 或 phased chromosome copies 定义；范围通常为 0-1；分母为零时允许 NA。'
 if f in {'pi','tajima_d','weighted_fst','mean_fst','pi_ratio','log2_pi_ratio'}:return '软件输出的窗口统计量；window 是推断单位；NA 表示该窗口无法估计；无 callable mask 时仅作描述性解释。'
 if f in {'xi','gj','or','undefined','total'}:return '该群体/总计中的 unique carrier accessions 数；分母为相应 retained cohort；零允许，缺失值不允许。'
 if 'sha256' in f:return 'SHA256 十六进制校验值；不允许缺失。'
 if f in {'from_haplotype_id','to_haplotype_id','hap_a','hap_b'}:return 'MST 边端点的 major haplotype ID；不允许缺失。'
 if f=='distance':return '基于全部批准 post-QC 位点模式的 haplotype distance；非负；不允许缺失。'
 if f in {'feature_class','detailed_feature_class'}:return 'primary-transcript 或 promoter 功能区类别；允许值由实际注释表给出；未知时允许 NA。'
 if f in {'ref_alt','coding_consequence','functional_label'}:return '由 MSU_osa1r7 REF/ALT 与 primary transcript 派生的描述性注释；无法注释时允许 NA。'
 if f in {'differentiates_primary_haplotypes','protein_altering','highlight_protein_altering','displayed_in_tree_ring'}:return '布尔标志，允许 True/False；不允许缺失。'
 return '该文件中按原样交付的字段；允许值由实际记录给出；NA 或空字符串仅表示源分析中的 missing/not applicable。'
def table_header(path):
 with path.open(newline='') as h:return next(csv.reader(h,delimiter='\t' if path.suffix=='.tsv' else ','),[])
def vcf_sample_count(path):
 with gzip.open(path,'rt') as h:
  for line in h:
   if line.startswith('#CHROM'):return len(line.rstrip().split('\t'))-9
 raise SystemExit(f'VCF header missing: {path}')
def main():
 p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--table-root',required=True);a=p.parse_args();c=config(a.config);root=Path(a.table_root)
 for directory in [root,*sorted(x for x in root.rglob('*') if x.is_dir())]:
  children=sorted(x for x in directory.iterdir() if x.name!='README.md')
  lines=[f'# {directory.name or "table"}','',f'分析范围：`{c["gene_id"]}`，参考基因组 `{c.get("reference_assembly","MSU_osa1r7")}`。坐标约定：{c.get("coordinate_convention","1-based VCF coordinates")}。','', '## Immediate children','']
  for child in children:lines.append(f'- `{child.name}`：{purpose(child)}')
  for child in children:
   if child.suffix.lower() in {'.tsv','.csv'}:
    header=table_header(child);lines.extend(['',f'## `{child.name}`','',f'行单位：{row_unit(child.name)}。频率/计数分母与坐标单位见逐字段定义；NA/空值仅按逐字段规则使用。','', '| Field | Exact definition |','|---|---|'])
    lines.extend(f'| `{field}` | {field_definition(child.name,field)} |' for field in header)
    if 'conversion_audit' in child.name:
     lines.extend(['','Metric values:',''])
     for record in rows(child):lines.append(f'- `{record["metric"]}`：`{record["value"]}`；该值按上述 `metric/value` 规则原样保留。')
   elif child.name.endswith('.vcf.gz'):
    lines.extend(['',f'## `{child.name}` VCF dictionary','',f'样本数：{vcf_sample_count(child)}；预期记录数：{c["expected_post_qc_variant_count"]}（SNP={c["expected_post_qc_snp_count"]}, InDel={c["expected_post_qc_indel_site_count"]}）。','', '| Field/class | Exact definition |','|---|---|'])
    for field,definition in (
     ('CHROM','MSU_osa1r7 染色体编号。'),('POS','1-based VCF coordinate，单位 bp。'),('ID','变异标识；缺失时为 .。'),('REF','参考等位。'),('ALT','逗号分隔替代等位。'),('QUAL','质量值；未提供时为 .。'),('FILTER','过滤状态。'),('INFO','记录级附加信息；未提供时为 .。'),('FORMAT','样本字段格式；本 VCF 为 GT。'),('GT sample columns','每个 accession 一个样本列；数字 allele index 以 | 相位分隔，.|. 表示缺失。')):
     lines.append(f'| `{field}` | {definition} |')
   elif child.name.endswith('.newick'):
    lines.extend(['',f'## `{child.name}` Newick contract','',f'Tip 单位为 retained accession（n={c["expected_complete_accessions"]}）；基于该 locus 的 {c["tree_expected_snps"]} 个 post-QC SNP-tagged 位点，以 diploid allele-sharing 1-IBS 距离和 RapidNJ 构建。Newick 分支长度可用于该局部矩阵内关系；圆形图按 topology 显示且径向分支不按长度比例。该树不是全基因组系统发育树。'])
   elif child.name.endswith('.tbi'):
    lines.extend(['',f'## `{child.name}`','', 'tabix 索引，仅用于 VCF 随机访问和区域查询；不是独立生物学结果表。'])
  (directory/'README.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':main()

#!/usr/bin/env python3
'''单次遍历完成 (v2, 审计后修复版):
  1) 亲本纯合且差异过滤 (Va vs Vv) — half-call 容错 + 计数器拆分 (M12, M8)
  2) 按池合并 AD/DP -> HighBulk / LowBulk 两样本输出
  3) **REF/ALT allele 按 Va 做 re-polarization** (M2): 若 Va 为 1/1, 交换 AD_REF/AD_ALT,
     让 +ΔSNP 恒等价 "HighBulk 富集 Va 等位"
  4) Pool DP = AD_REF + AD_ALT, 保持与 SNPindex 分母一致性 (M9)
  5) GT=(0,0) 当 alt=0 时, 避免 input.table 假阳性 (m1)
  6) FORMAT/VA 字段标注每个位点 Va 等位 (REF/ALT), 便于审计

用法:
  python parent_filter_and_pool_v2.py <in.vcf.gz> <high_list> <low_list> <Va_sample> <Vv_sample> <out.vcf.gz> [--chrom-regex PATTERN]
'''
import sys, re, argparse
import pysam

ap = argparse.ArgumentParser()
ap.add_argument('in_vcf')
ap.add_argument('high_list')
ap.add_argument('low_list')
ap.add_argument('va_sample', help='抗旱亲本样本名')
ap.add_argument('vv_sample', help='不抗亲本样本名')
ap.add_argument('out_vcf')
ap.add_argument('--min-parent-dp', type=int, default=5)
ap.add_argument('--chrom-regex', default=r'^chr\d+$',
                help='仅保留匹配此正则的染色体。Shell 调用请用单引号!')
ap.add_argument('--no-repolarize', action='store_true',
                help='不做 re-polarization (兼容 v1 行为)')
args = ap.parse_args()

HIGH = [l.strip() for l in open(args.high_list) if l.strip()]
LOW  = [l.strip() for l in open(args.low_list)  if l.strip()]
VA   = args.va_sample
VV   = args.vv_sample
CHROM_RE = re.compile(args.chrom_regex)

print(f'[INFO] HighBulk n={len(HIGH)}  LowBulk n={len(LOW)}', file=sys.stderr)
print(f'[INFO] Parents: Va={VA} (抗旱)  Vv={VV} (不抗)', file=sys.stderr)
print(f'[INFO] chrom filter: {args.chrom_regex}', file=sys.stderr)
print(f'[INFO] re-polarize: {not args.no_repolarize}', file=sys.stderr)

vin = pysam.VariantFile(args.in_vcf)
for s in [VA, VV] + HIGH + LOW:
    if s not in vin.header.samples:
        sys.exit(f'[ERR] sample {s!r} not in VCF')

# 构造新 header (移除 random scaffold contig)
hdr = pysam.VariantHeader()
retained_contigs = 0
for rec in vin.header.records:
    if rec.type == 'CONTIG' and not CHROM_RE.match(rec.get('ID','')):
        continue
    hdr.add_record(rec)
    if rec.type == 'CONTIG':
        retained_contigs += 1
for tag, num, typ, desc in [
    ('GT','1','String','Genotype (0/0 if ad_alt==0, 0/1 otherwise)'),
    ('AD','R','Integer','Pool-summed allelic depths (after re-polarization if enabled)'),
    ('DP','1','Integer','Pool total depth = AD_REF + AD_ALT (v2 consistency fix)'),
    ('GQ','1','Integer','Genotype Quality placeholder=99 (GQ filter is disabled)'),
]:
    if tag not in hdr.formats:
        hdr.formats.add(tag, num, typ, desc)
# INFO 字段标注 Va 的等位方向
if 'VA_HOM' not in hdr.info:
    hdr.info.add('VA_HOM','1','String','Va homozygous allele (REF or ALT) before re-polarization')
if 'POLARIZED' not in hdr.info:
    hdr.info.add('POLARIZED','0','Flag','Whether AD has been re-polarized to Va allele')
hdr.add_sample('HighBulk')
hdr.add_sample('LowBulk')

print(f'[INFO] retained contigs in header: {retained_contigs}', file=sys.stderr)
if retained_contigs == 0:
    sys.exit('[ERR] chrom-regex filtered out all contigs, check pattern vs VCF contig naming')

vout = pysam.VariantFile(args.out_vcf, 'w', header=hdr)

# v2: 拆分 parent_skip 为三个计数器 (M8)
n_in = n_chr_skip = n_indel = n_multi = 0
n_parent_gt_missing = n_parent_dp_low = n_parent_not_homdiff = n_half_call = 0
n_out = 0
n_polarized = 0

def is_hom_ref(gt):
    return gt is not None and len(gt) == 2 and gt[0] == 0 and gt[1] == 0

def is_hom_alt(gt):
    return gt is not None and len(gt) == 2 and gt[0] == 1 and gt[1] == 1

def is_half_call(gt):
    return gt is not None and (len(gt) == 1 or (len(gt) == 2 and (gt[0] is None or gt[1] is None)))

for rec in vin:
    n_in += 1
    if n_in % 500000 == 0:
        print(f'  processed {n_in}  kept {n_out}  polarized {n_polarized}', file=sys.stderr)

    if not CHROM_RE.match(rec.contig):
        n_chr_skip += 1; continue
    if len(rec.alleles) != 2:
        n_multi += 1; continue
    if len(rec.ref) != 1 or len(rec.alts[0]) != 1:
        n_indel += 1; continue

    va = rec.samples[VA]; vv = rec.samples[VV]
    va_gt, vv_gt = va.get('GT'), vv.get('GT')
    va_dp = va.get('DP') or 0
    vv_dp = vv.get('DP') or 0

    # 粒度拆分的 parent_skip 原因
    if va_gt is None or vv_gt is None:
        n_parent_gt_missing += 1; continue
    if is_half_call(va_gt) or is_half_call(vv_gt):
        n_half_call += 1; continue
    if None in va_gt or None in vv_gt:
        n_parent_gt_missing += 1; continue
    if va_dp < args.min_parent_dp or vv_dp < args.min_parent_dp:
        n_parent_dp_low += 1; continue
    # 纯合且差异
    va_is_ref = is_hom_ref(va_gt); va_is_alt = is_hom_alt(va_gt)
    vv_is_ref = is_hom_ref(vv_gt); vv_is_alt = is_hom_alt(vv_gt)
    if not ((va_is_ref and vv_is_alt) or (va_is_alt and vv_is_ref)):
        n_parent_not_homdiff += 1; continue

    # 通过过滤 -> 按池合并 + re-polarization
    va_hom = 'ALT' if va_is_alt else 'REF'
    do_polarize = (not args.no_repolarize) and va_is_ref

    new = vout.new_record(
        contig=rec.contig, start=rec.start, stop=rec.stop,
        alleles=rec.alleles, qual=rec.qual, filter=rec.filter.keys(),
    )
    new.info['VA_HOM'] = va_hom
    if do_polarize:
        new.info['POLARIZED'] = True
        n_polarized += 1

    for pool, samples in [('HighBulk', HIGH), ('LowBulk', LOW)]:
        ad_ref = ad_alt = 0
        for s in samples:
            ss = rec.samples[s]
            ad = ss.get('AD')
            if ad is not None and len(ad) >= 2:
                if ad[0] is not None: ad_ref += ad[0]
                if ad[1] is not None: ad_alt += ad[1]
        # Re-polarize: 若 Va 是 ALT 纯合, 交换 AD 以便 +ΔSNP = Va 富集
        if do_polarize:
            ad_ref, ad_alt = ad_alt, ad_ref
        # Pool DP 重算为 AD 总和, 保持 SNPindex 分母一致 (M9)
        dp = ad_ref + ad_alt
        # GT: alt=0 时改为 0/0 避免 m1 假阳性
        gt_placeholder = (0, 0) if ad_alt == 0 else (0, 1)
        new.samples[pool]['GT'] = gt_placeholder
        new.samples[pool]['AD'] = (ad_ref, ad_alt)
        new.samples[pool]['DP'] = dp
        new.samples[pool]['GQ'] = 99  # GQ filter 已禁用 (M1), 占位仅为 GATK VariantsToTable 需要
    vout.write(new); n_out += 1

vin.close(); vout.close()

parent_skip_total = n_parent_gt_missing + n_parent_dp_low + n_parent_not_homdiff + n_half_call
print(f'[STATS] in={n_in}'
      f' chr_skip={n_chr_skip}'
      f' indel={n_indel}'
      f' multi={n_multi}'
      f' parent_gt_missing={n_parent_gt_missing}'
      f' parent_half_call={n_half_call}'
      f' parent_dp_low={n_parent_dp_low}'
      f' parent_not_homdiff={n_parent_not_homdiff}'
      f' parent_skip_total={parent_skip_total}'
      f' kept={n_out}'
      f' polarized={n_polarized}', file=sys.stderr)
assert n_in == n_chr_skip + n_indel + n_multi + parent_skip_total + n_out, \
    '[CHECK] 统计闭环未通过'
print('[CHECK] 统计闭环通过', file=sys.stderr)

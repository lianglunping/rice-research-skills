#!/usr/bin/env Rscript
# QTLseqr BSA 分析 - 葡萄 5h 失水率 (v2.1, 审计后修复版)
# HighBulk = 抗旱池 (n=20)  LowBulk = 不抗池 (n=20)
# 亲本: Va=抗旱 / Vv=不抗   群体: F2
#
# Usage:
#   Rscript qtlseqr_analysis_v2.R <input.table> <out_dir> <fig_dir> [window=1e6] [refAF=0.20] [suffix=""]
# Examples:
#   Rscript qtlseqr_analysis_v2.R input.table results figures              # 主分析
#   Rscript qtlseqr_analysis_v2.R input.table results figures 5e5 0.20 _w500k
#   Rscript qtlseqr_analysis_v2.R input.table results figures 1e6 0.35 _rf035
#
# Args:
#   input.table   GATK VariantsToTable 输出 (CHROM POS REF ALT HighBulk.AD HighBulk.DP HighBulk.GQ LowBulk.AD LowBulk.DP LowBulk.GQ)
#   out_dir       结果输出目录 (TSV + RDS)
#   fig_dir       图表输出目录 (PDF)
#   window        G'/QTL-seq 滑窗大小 (bp), 默认 1e6
#   refAF         filterSNPs 的 refAlleleFreq, 默认 0.20
#   suffix        输出文件后缀 (如 _w500k _rf035), 默认空
#
# Fixes (v2.1): M10 set.seed / m6 filterSNPs retained 记录 / M9 DP=sum(AD) 假设 / m9 命名统一 / 新增 usage

set.seed(42)  # M10: byte-level 复现 (每个 run 调用时都会重置)

suppressPackageStartupMessages({
  library(QTLseqr)
  library(ggplot2)
  library(dplyr)
})

ARGS <- commandArgs(trailingOnly = TRUE)
TABLE_IN   <- ifelse(length(ARGS)>=1, ARGS[1], 'input.table')
OUT_DIR    <- ifelse(length(ARGS)>=2, ARGS[2], 'results')
FIG_DIR    <- ifelse(length(ARGS)>=3, ARGS[3], 'figures')
# 允许参数化 window & refAF 以做敏感性分析
WINDOW     <- as.numeric(ifelse(length(ARGS)>=4, ARGS[4], 1e6))
REF_AF     <- as.numeric(ifelse(length(ARGS)>=5, ARGS[5], 0.20))
SUFFIX     <- ifelse(length(ARGS)>=6, ARGS[6], '')  # e.g. '_w500k_rf035'

dir.create(OUT_DIR, FALSE, TRUE)
dir.create(FIG_DIR, FALSE, TRUE)

HighBulk <- 'HighBulk'
LowBulk  <- 'LowBulk'
Chroms <- paste0('chr', 1:19)

cat(sprintf('[params] window=%g refAlleleFreq=%g suffix=%s\n', WINDOW, REF_AF, SUFFIX))

cat('[1/6] Import GATK table...\n')
df <- importFromGATK(file = TABLE_IN,
                     highBulk = HighBulk,
                     lowBulk  = LowBulk,
                     chromList = Chroms)
cat('  rows =', nrow(df), '\n')

# ---- 诊断图 ----
pdf(file.path(FIG_DIR, paste0('00_diagnostic', SUFFIX, '.pdf')), width=12, height=8)
print(ggplot(df) + geom_histogram(aes(DP.HIGH+DP.LOW), bins=60) + xlim(0,1500) +
      labs(title='Total depth (HIGH+LOW)'))
print(ggplot(df) + geom_histogram(aes(REF_FRQ), bins=60) +
      labs(title='Reference allele frequency (post re-polarization)'))
print(ggplot(df) + geom_histogram(aes(SNPindex.HIGH), bins=60) +
      labs(title='SNP-index HIGH bulk'))
print(ggplot(df) + geom_histogram(aes(SNPindex.LOW), bins=60) +
      labs(title='SNP-index LOW bulk'))
# 额外: per-sample DP 对等性 proxy
print(ggplot(df, aes(DP.HIGH, DP.LOW)) + geom_hex(bins=60) +
      labs(title='DP equality HIGH vs LOW (pseudo-pool QC, M3)'))
dev.off()

cat('[2/6] filterSNPs (refAlleleFreq=', REF_AF, ', GQ filter disabled, see audit M1)\n')
df_filt <- filterSNPs(SNPset = df,
                      refAlleleFreq  = REF_AF,
                      minTotalDepth  = 40,
                      maxTotalDepth  = 600,
                      minSampleDepth = 15,
                      minGQ          = 0,       # GQ 过滤已禁用; 由 DeepVariant FILTER + DP 过滤承担
                      depthDifference= 100,
                      verbose        = TRUE)
# m6: 显式记录 filterSNPs 保留数
cat(sprintf('[2/6] filterSNPs retained: %d / %d (%.2f%%)\n',
            nrow(df_filt), nrow(df), 100*nrow(df_filt)/nrow(df)))

cat('[3/6] runGprimeAnalysis...\n')
df_Gp <- runGprimeAnalysis(df_filt,
                           windowSize = WINDOW,
                           outlierFilter   = 'deltaSNP',
                           filterThreshold = 0.1)

cat('[4/6] runQTLseqAnalysis F2 bulkSize=c(20,20), replications=10000 (seed=42)...\n')
df_qs <- runQTLseqAnalysis(df_filt,
                           windowSize = WINDOW,
                           popStruc = 'F2',
                           bulkSize = c(20, 20),
                           replications = 10000,
                           intervals = c(95, 99))

# ---- 保存全 SNP 结果 ----
saveRDS(df_Gp, file.path(OUT_DIR, paste0('Gprime_all', SUFFIX, '.rds')))
saveRDS(df_qs, file.path(OUT_DIR, paste0('QTLseq_all', SUFFIX, '.rds')))
write.table(df_Gp, file.path(OUT_DIR, paste0('Gprime_all_snps', SUFFIX, '.tsv')),
            sep='\t', quote=FALSE, row.names=FALSE)
write.table(df_qs, file.path(OUT_DIR, paste0('QTLseq_all_snps', SUFFIX, '.tsv')),
            sep='\t', quote=FALSE, row.names=FALSE)

# ---- 曼哈顿图 ----
cat('[5/6] plotQTLStats...\n')
pdf(file.path(FIG_DIR, paste0('01_Gprime_manhattan', SUFFIX, '.pdf')), width=14, height=6)
print(plotQTLStats(df_Gp, var='Gprime', plotThreshold=TRUE, q=0.01))
dev.off()
pdf(file.path(FIG_DIR, paste0('02_negLog10Pval_manhattan', SUFFIX, '.pdf')), width=14, height=6)
print(plotQTLStats(df_Gp, var='negLog10Pval', plotThreshold=TRUE, q=0.01))
dev.off()
pdf(file.path(FIG_DIR, paste0('03_deltaSNP_manhattan', SUFFIX, '.pdf')), width=14, height=6)
print(plotQTLStats(df_qs, var='deltaSNP', plotIntervals=TRUE))
dev.off()
pdf(file.path(FIG_DIR, paste0('04_nSNPs_per_window', SUFFIX, '.pdf')), width=14, height=6)
print(plotQTLStats(df_Gp, var='nSNPs'))
dev.off()

# ---- 候选区间 ----
cat('[6/6] getQTLTable ...\n')
gp_q001 <- tryCatch(getQTLTable(df_Gp, method='Gprime', alpha=0.01, export=FALSE),
                    error=function(e){message('Gprime q=0.01: 无区间'); NULL})
gp_q005 <- tryCatch(getQTLTable(df_Gp, method='Gprime', alpha=0.05, export=FALSE),
                    error=function(e){message('Gprime q=0.05: 无区间'); NULL})
qs_ci99 <- tryCatch(getQTLTable(df_qs, method='QTLseq', interval=99, export=FALSE),
                    error=function(e){message('QTLseq 99% CI: 无区间'); NULL})
qs_ci95 <- tryCatch(getQTLTable(df_qs, method='QTLseq', interval=95, export=FALSE),
                    error=function(e){message('QTLseq 95% CI: 无区间'); NULL})

# 命名统一 (m9): q00X 用于 Gprime, ci9X 用于 QTLseq
if (!is.null(gp_q001)) write.table(gp_q001, file.path(OUT_DIR, paste0('Gprime_q001_regions', SUFFIX, '.tsv')),
                                    sep='\t', quote=FALSE, row.names=FALSE)
if (!is.null(gp_q005)) write.table(gp_q005, file.path(OUT_DIR, paste0('Gprime_q005_regions', SUFFIX, '.tsv')),
                                    sep='\t', quote=FALSE, row.names=FALSE)
if (!is.null(qs_ci99)) write.table(qs_ci99, file.path(OUT_DIR, paste0('QTLseq_ci99_regions', SUFFIX, '.tsv')),
                                    sep='\t', quote=FALSE, row.names=FALSE)
if (!is.null(qs_ci95)) write.table(qs_ci95, file.path(OUT_DIR, paste0('QTLseq_ci95_regions', SUFFIX, '.tsv')),
                                    sep='\t', quote=FALSE, row.names=FALSE)

cat('\n[DONE] window=', WINDOW, ' refAF=', REF_AF, ' suffix=', SUFFIX, '\n',
    'filterSNPs retained:', nrow(df_filt), '\n',
    'Gprime q=0.01 regions:', ifelse(is.null(gp_q001), 0, nrow(gp_q001)), '\n',
    'Gprime q=0.05 regions:', ifelse(is.null(gp_q005), 0, nrow(gp_q005)), '\n',
    'QTLseq 99% CI regions:', ifelse(is.null(qs_ci99), 0, nrow(qs_ci99)), '\n',
    'QTLseq 95% CI regions:', ifelse(is.null(qs_ci95), 0, nrow(qs_ci95)), '\n',
    sep='')

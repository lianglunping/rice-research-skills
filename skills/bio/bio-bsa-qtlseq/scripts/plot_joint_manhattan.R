#!/usr/bin/env Rscript
# plot_joint_manhattan.R — 多时间点联合曼哈顿图
# Usage: Rscript plot_joint_manhattan.R --t1 t1.rds --t2 t2.rds --out <prefix>

suppressPackageStartupMessages({
    library(optparse)
    library(ggplot2)
    library(dplyr)
})

opt_list <- list(
    make_option('--t1', type='character', help='t1 Gprime_all.rds'),
    make_option('--t2', type='character', help='t2 Gprime_all.rds'),
    make_option('--out', type='character', default='compare_manhattan', help='输出前缀')
)
opt <- parse_args(OptionParser(option_list=opt_list))

t1 <- readRDS(opt$t1); t1$timepoint <- "T1"
t2 <- readRDS(opt$t2); t2$timepoint <- "T2"

combined <- bind_rows(
    t1 %>% select(CHROM, POS, Gprime, deltaSNP, timepoint),
    t2 %>% select(CHROM, POS, Gprime, deltaSNP, timepoint)
)

# Gprime 联合曼哈顿
p <- ggplot(combined, aes(x=POS, y=Gprime, color=timepoint)) +
    geom_point(size=0.5, alpha=0.5) +
    facet_grid(timepoint ~ CHROM, scales='free_x', space='free_x') +
    labs(title="Joint Gprime Manhattan (T1 vs T2)", x="Position", y="G'") +
    theme_minimal() +
    theme(axis.text.x=element_blank(), legend.position='bottom')

ggsave(paste0(opt$out, '.pdf'), p, width=16, height=6)
ggsave(paste0(opt$out, '.png'), p, width=16, height=6, dpi=600)
cat("[OK] joint manhattan 已生成:", opt$out, ".{pdf,png}\n")

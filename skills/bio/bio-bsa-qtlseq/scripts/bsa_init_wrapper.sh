#!/usr/bin/env bash
# bsa_init_wrapper.sh — BSA 参数解析与编排 wrapper
# 可由 Codex 直接执行, 或由项目约定命令传入参数.
set -eo pipefail

SKILL_ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"

CONFIG=""; PROFILE=""; NON_INTERACTIVE=false; RESUME_FROM=""; COMPARE_T1=""; COMPARE_T2=""
while [ $# -gt 0 ]; do
    case "$1" in
        --config) CONFIG="$2"; shift 2;;
        --profile) PROFILE="$2"; shift 2;;
        --non-interactive) NON_INTERACTIVE=true; shift;;
        --resume-from) RESUME_FROM="$2"; shift 2;;
        --compare-timepoints) COMPARE_T1="$2"; COMPARE_T2="$3"; shift 3;;
        *) echo "[ERR] Unknown arg: $1" >&2; exit 2;;
    esac
done

log() { echo "[bsa-init $(date +%T)] $*"; }

# 多时间点对比模式
if [ -n "$COMPARE_T1" ] && [ -n "$COMPARE_T2" ]; then
    log "多时间点对比: $COMPARE_T1 vs $COMPARE_T2"
    bash "$SKILL_ROOT/scripts/compare_timepoints.sh" "$COMPARE_T1" "$COMPARE_T2" "./compare_out/"
    exit $?
fi

# Resume 逻辑
BSA_ROOT="${BSA_ROOT:-$(pwd)}"
if [ -n "$RESUME_FROM" ]; then
    STATE="$BSA_ROOT/state/current_gate"
    [ -f "$STATE" ] || { echo "[ERR] 无 state 可恢复: $STATE" >&2; exit 1; }
    log "[RESUME] 从 $RESUME_FROM 恢复"
    for G in gate1 gate2 gate3 gate4; do
        [ "$G" = "$RESUME_FROM" ] && break
        if [ ! -f "$BSA_ROOT/state/${G}.PASS" ] && [ ! -f "$BSA_ROOT/state/${G}.WARN" ]; then
            echo "[ERR] $G 未 PASS, 无法跳过" >&2; exit 1
        fi
    done
fi

# Config 解析
if [ -z "$CONFIG" ]; then
    if [ "$NON_INTERACTIVE" = true ]; then
        echo "[ERR] --non-interactive 需要 --config" >&2; exit 1
    fi
    log "交互式问答模式 (未实现, 此处需 Codex 引导用户)"
    exit 2
fi

# Schema 校验
log "validate_config"
python "$SKILL_ROOT/scripts/validate_config.py" \
    --config "$CONFIG" \
    ${PROFILE:+--profile $PROFILE} \
    --out "$BSA_ROOT/merged_config.yaml" \
    ${SAMPLES_TSV:+--samples $SAMPLES_TSV} \
    ${PHENO_META:+--phenotype-meta $PHENO_META}
[ $? -eq 0 ] || { echo "[ABORT] schema 校验失败" >&2; exit 1; }

log "配置就绪, 后续步骤由 Codex 按 SKILL.md 编排 gate1-4"
log "参考 SKILL.md §6 状态机"

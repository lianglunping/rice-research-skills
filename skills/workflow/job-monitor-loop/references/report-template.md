# Report Templates

## Normal Check

```markdown
【监控检查】

检查时间：YYYY-MM-DD HH:MM:SS TZ
任务状态：RUNNING/ACTIVE/UNKNOWN
任务标识：job_id/pid/command
RUN_ID：optional
RUN_DIR：optional
HOST：optional
MONITOR_CMD：optional
工作目录：/path/to/workdir
日志证据：/path/to/log，新增至 line N 或 timestamp
输出证据：/path/to/output，size/mtime/checkpoint
wrapper 状态：STATE_terminal_state / state/attempt / LOCK / TMUX / HEARTBEAT_AGE，如适用
判定：正常/未知
当前监控层级：1min/10min/30min
下一次检查：YYYY-MM-DD HH:MM:SS TZ
缺口：如无则写“无明显缺口”
```

## Anomaly Report

````markdown
【异常报告】

异常时间：YYYY-MM-DD HH:MM:SS TZ
任务状态：FAILED/EXITED/STALLED/UNKNOWN
任务标识：job_id/pid/command
RUN_ID：optional
RUN_DIR：optional
HOST：optional
MONITOR_CMD：optional
证据位置：
- 日志：/path/to/log:line 或 timestamp
- 状态：scheduler/ps/exit code
- 输出：/path/to/output，size/mtime
- wrapper：STATE_terminal_state / state/attempt / LOCK / TMUX / HEARTBEAT_AGE，如适用

核心错误摘要：
用 1-3 句概括，不夸大，不补齐未知信息。

最可能原因：
1. 原因 A：证据...
2. 原因 B：证据...

最小修复动作：
1. 非破坏性检查或修复命令...
2. 需要用户批准的动作...

人工重提 gate（如适用）：
- terminal_state=FAILED
- TMUX=gone
- LOCK=released
- 用户明确批准

复现验证方式：
```bash
command --with --same --params
```

监控策略调整：
已重置为 1 分钟检查窗口；连续 3 次正常后再升级到 10 分钟。
````

## Completion Report

```markdown
【任务完成】

完成时间：YYYY-MM-DD HH:MM:SS TZ
任务状态：COMPLETED/SUCCESS
任务标识：job_id/pid/command
RUN_ID：optional
RUN_DIR：optional
HOST：optional
MONITOR_CMD：optional
退出码或调度状态：0/COMPLETED
wrapper 完成证据：STATE_terminal_state=SUCCESS，如适用
关键输出：
- /path/to/output1
- /path/to/output2
日志：/path/to/log
复现信息：
- 命令：...
- 环境：conda env / container / module
- 输入：...
- 输出：...
- 关键版本：...
剩余风险：如无明确风险，写“未发现明显异常；仍建议按项目 QA 流程检查结果完整性。”
```

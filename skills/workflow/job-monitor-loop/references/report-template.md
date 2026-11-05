# Report Templates

Use only fields supported by evidence. These are persistent record templates;
normal unchanged checks remain quiet in chat. Do not invent a second cause when
one root cause is confirmed.

## Normal or Unknown Check

~~~markdown
【监控检查】

检查时间：YYYY-MM-DD HH:MM:SS TZ
授权模式：OBSERVE_ONLY / REPAIR_PREAUTHORIZED / DECISION_REQUIRED
证据判定：normal / unknown
任务状态：RUNNING / ACTIVE / UNKNOWN
任务标识：job_id / pid / command
逻辑 RUN_ID / attempt：optional
RUN_DIR / HOST / MONITOR_CMD：optional
工作目录：/path
日志证据：path + reviewed line/timestamp
输出证据：path + size/mtime/checkpoint
状态证据：terminal/session/lock/heartbeat，如适用
异常证据扫描：未命中；若命中则不得判 normal
当前稳定层级：1min / 10min / 30min / 1h / 3h / 6h
实际检查间隔：min(稳定档位、整体进度上限、ETA 上限、阶段上限)
整体进度及分母：...；证据可靠性：...
预计剩余时间及估计依据：...
监控后端及已核验的定时凭据：...
下一次检查：time
未知原因：仅在判定 unknown 时填写
验收门禁状态：not_started / pending
~~~

## Anomaly Report

~~~markdown
【异常报告】

异常时间：YYYY-MM-DD HH:MM:SS TZ
授权模式：OBSERVE_ONLY / REPAIR_PREAUTHORIZED / DECISION_REQUIRED
证据判定：anomalous
任务状态：FAILED / EXITED / STALLED / UNKNOWN
任务标识：job_id / pid / command
逻辑 RUN_ID / failed attempt：optional
RUN_DIR / HOST / MONITOR_CMD：optional

证据位置：
- 日志：path:line 或 timestamp
- 状态：scheduler/process/exit/wrapper/session/lock/heartbeat
- 输出：path + size/mtime/checkpoint

核心错误摘要：
仅概括有证据的事实。

根因状态：CONFIRMED / HYPOTHESIS

确认根因：
- 有直接证据时，只报告已确认根因；不要为凑数量编造第二原因。

排序假设：
1. 仅在根因未确认时列 1–3 个有证据支持的假设。
2. 每个假设附区分检查。

授权判定：
- 当前允许立即执行：...
- 需要用户决定：...

最小修复或诊断：
- action
- validation

监控策略：
首次异常立即诊断并按已有授权修复；持续同一异常按有限诊断窗口退避。
只有确认恢复或新的已提交 attempt 才重新进入早期稳定窗口。
修复预算模式：FIXED / RENEWABLE；固定或实际资源上限：...
当前批次问题/合计修复次数：...；累计修复次数：...
续期复核与凭据：...；停滞或停止原因：...
下一次检查：...
~~~

## Recovery Report

~~~markdown
【恢复记录】

授权模式：REPAIR_PREAUTHORIZED
逻辑 RUN_ID / RUN_DIR：...
失败 attempt / 新 attempt：...
旧/新 scheduler 或 process ID：...
已保留的失败证据：...
修复预算模式与当前批次：...；累计次数与续期记录：...
确认根因：...
最小修改：文件、依赖、命令及理由
恢复命令：...
科学输入与关键参数是否变化：否
输入不可变证据：...
复验方式：...
恢复后监控层级：1min early window
超出授权事项：无；如有则停止并改为 DECISION_REQUIRED
~~~

## Acceptance Report

只有全部适用门禁通过时使用标题“任务完成”；否则使用“进程结束，
验收待完成”或“任务未通过验收”。

~~~markdown
【任务完成 / 进程结束，验收待完成 / 任务未通过验收】

完成时间：YYYY-MM-DD HH:MM:SS TZ
授权模式：...
任务标识：...
逻辑 RUN_ID / final attempt：...
退出码或调度状态：...
关键输出：
- path

验收门禁：
| Gate | Status | Evidence |
|---|---|---|
| terminal_state | PASS/FAIL/NA | |
| expected_artifacts | PASS/FAIL/NA | |
| semantic_QA | PASS/FAIL/NA | |
| provenance_manifest | PASS/FAIL/NA | |
| input_immutability | PASS/FAIL/NA | |

最终判定：ACCEPTED / COMPLETION_PENDING / NOT_ACCEPTED

复现信息：
- command
- environment
- inputs
- outputs
- versions
- parameters/seed

剩余限制：...
~~~

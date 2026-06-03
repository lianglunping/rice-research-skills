# ab1 文件命名规则

## 标准格式

```
{variant_name}.{variant_name}-{direction_suffix}.{order_id}.{plate_well}.{well}.ab1
```

### 示例

| 文件名 | variant_name | direction |
|--------|-------------|-----------|
| `H1-1.H1-1-F.20504345.P9047D09.F05.ab1` | H1-1 | F（正向）|
| `H1-1.H1-1-R.20504346.P9047D09.F06.ab1` | H1-1 | R（反向）|
| `H1-2.H1-2-FF.20571824.p9087A01.A01.ab1` | H1-2 | F（正向，双F写法）|
| `H1-2.H1-2-RR.20571825.p9087A01.A02.ab1` | H1-2 | R（反向，双R写法）|
| `H56.H56-F.20724308.p9198G10.H06.ab1` | H56 | F |

## 方向解析规则（优先级从高到低）

```python
if primer_field.endswith("-RR") or primer_field.endswith("-RRR"):
    direction = "R"
elif primer_field.endswith("-R"):
    direction = "R"
elif primer_field.endswith("-FF") or primer_field.endswith("-FFF"):
    direction = "F"
elif primer_field.endswith("-F"):
    direction = "F"
else:
    direction = "unknown"
```

`primer_field` = 文件名按 `.` 分割后的第二个字段（index=1）。

## 批次目录结构

每次验证包含三个子目录：

```
一代测序第N次验证/
├── 报告成功/     # 测序质量合格的 ab1 文件
├── 报告取消/     # 测序质量不合格（信号弱、混合峰等），保留备用
└── 拼接序列/     # 序列文件（.seq/.txt），pipeline 不使用此目录
```

- **pipeline 优先使用"报告成功"**中的 ab1
- 如果某变异所有批次的"报告成功"均无数据，才使用"报告取消"中的数据
- `tracy_call = R` 表示该变异完全无 ab1 数据

## variant_name 对应关系

文件名第一字段 (`parts[0]`) 直接对应变异表中的 `name` 列。

常见格式：
- `H31-5`：H31 样本第 5 个变异
- `H56`：有时实验室会省略变异编号（注意检查是否唯一匹配）

## 常见异常情况

| 情况 | 处理方式 |
|------|---------|
| 方向为 unknown | 该 ab1 被加入 ab1_map 但综合判定时会被跳过 |
| 同一变异同批次同方向多个 ab1 | 取 `_call_priority` 最高的，同优先级取 qual 最高的 |
| 文件名字段数 < 3 | 跳过（格式不符）|

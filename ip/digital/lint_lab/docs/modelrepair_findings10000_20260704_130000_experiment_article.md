# 10k SpyGlass Lint 修复实验：no-kb 与 with-kb 对比分析

## 摘要

本次实验把 lint lab 的 SpyGlass violation 规模提升到约 10000 条，并继续采用严格的 live repair 方法对比 no-kb 与 with-kb 两种修复模式。两个修复 session 从同一个 broken RTL 起点出发，分别在独立 work branch 中根据当前 SpyGlass 报告逐轮生成局部 patch，直到 SpyGlass 实际达到 `0 errors / 0 warnings` 为止。

实验结果显示，在本次 10k violation、每轮修复上限放大的条件下，with-kb 没有体现明显优势：no-kb 用 14 轮完成，with-kb 用 15 轮完成；记录的 MCP lint wall time 分别为 568.01s 和 576.69s，差异约 1.5%。两边最终均达到 `0 errors / 0 warnings / 3 infos`。

这个结果说明，对于结构规律较强、tag family 数量有限、且允许大批量局部 patch 的 lint lab 批量修复任务，KB 不是必需条件。KB 的主要价值更可能体现在真实项目中根因复杂、同 tag 多根因、工具规则语义不清、或修复不收敛的场景。

## 实验背景

前几轮小规模实验中，with-kb 在部分配置下比 no-kb 更快完成修复。但那些结果容易受到实验方式影响，例如：

- 是否提前准备了修复后目录；
- 是否允许直接使用 generator clean template；
- 是否把固定模板一次性套到大量模块；
- 是否固定轮数而不是自然清零；
- 是否只统计 lint wall time，而没有统计分析和修改耗时。

为了让对比更接近真实修复过程，本轮实验采用更严格的 live repair 方法：

- no-kb 和 with-kb 只给同一个 broken RTL 起点；
- 不提前准备修复后目录；
- 每轮必须根据上一轮 SpyGlass 报告现场生成 patch；
- 不允许使用 `base_level` 整体替换模块；
- 不允许使用 generator clean template；
- 不允许 whole-module replacement；
- 每轮只能根据当前报告中的具体 `file/line/tag` 做局部修复；
- 同一 tag 下允许不同根因；
- 修复可能引入新 warning 或暴露次级问题；
- 直到 SpyGlass 实际清零才停止。

## 实验设置

本轮实验 run stem 为：

```text
modelrepair_findings10000_20260704_130000
```

运行目录为：

```text
ip/digital/lint_lab/de/run/lint_spyglass/live_compare/modelrepair_findings10000_20260704_130000/seed_20260703
```

两个独立工作分支为：

```text
no_kb_work
with_kb_work
```

生成配置：

| 项目 | 值 |
|---|---:|
| profile | realistic |
| seed | 20260703 |
| variants | 1260 |
| holdouts | 0 |
| RTL size | 约 1.2 MB |
| baseline SpyGlass messages | 10121 |
| baseline actionable violations | 9962 |
| unique tags | 29 |

baseline SpyGlass 结果：

```text
4781 errors / 5333 warnings / 7 infos
```

parser 抽取结果：

```text
9962 actionable violations
9969 parsed findings including info
29 unique tags
```

主要 tag 分布包括：

| tag | count |
|---|---:|
| sim_race02 | 1264 |
| W240 | 1263 |
| W528 | 932 |
| ErrorAnalyzeBBox | 714 |
| W415 | 639 |
| NoAssignX-ML | 521 |
| W398 | 385 |
| InferLatch | 314 |
| W110 | 314 |
| W287b | 314 |
| W336 | 314 |
| ParamWidthMismatch-ML | 312 |
| W442a | 310 |
| bothedges | 310 |
| W123 | 308 |

## 两种修复模式

### no-kb

no-kb worker 的限制为：

- 禁止使用 KB、RAG、wiki、web；
- 禁止读取 with-kb prompt；
- 禁止读取或修改 `with_kb_work`；
- 只能根据当前 SpyGlass 报告和本地 RTL 片段推理修复；
- 使用 `soc-build.soc_lint` 运行 SpyGlass；
- 直到实际 `0 errors / 0 warnings` 停止。

### with-kb

with-kb worker 的限制为：

- 只能使用 prompt 内嵌的 tag-specific KB excerpt；
- 禁止查询额外 `soc-ai-kb`、RAG、wiki、web；
- 禁止读取 no-kb prompt；
- 禁止读取或修改 `no_kb_work`；
- 只能根据当前 SpyGlass 报告和本地 RTL 片段修复；
- 使用 `soc-build.soc_lint` 运行 SpyGlass；
- 直到实际 `0 errors / 0 warnings` 停止。

with-kb prompt 中包含的 KB 摘要只覆盖以下方向：

- `sim_race02 / W415`：多驱动、同周期多次赋值；
- `NoAssignX-ML`：显式 X/Z 赋值和 case x/z pattern；
- `InferLatch`：组合逻辑路径未完全赋值；
- `CombLoop / ErrorAnalyzeBBox / SYNTH_5191`：组合环及综合失败根因方向。

## 每轮修复上限

用户要求本轮在 10000 violation 规模下加大每轮上限，因此本轮配置为：

```text
100-200 modules or 1200-2500 changed lines per round,
unless the current report has fewer local fixes left.
```

需要注意，这个上限是实验中的重要变量。它会显著影响 KB 是否能体现优势。较小上限下，KB 可能通过更准确选择 root cause 和 tag family 来减少试错；较大上限下，no-kb 也可以通过观察报告结构，批量修复大量相似 pattern，从而摊薄 KB 的收益。

## 结果

| arm | rounds | recorded lint time | wall clock | final E/W/I | reached 0/0 |
|---|---:|---:|---:|---:|---|
| no-kb | 14 | 568.01s | 1225s | 0/0/3 | yes |
| with-kb | 15 | 576.69s | ~1500s | 0/0/3 | yes |

对比结论：

- no-kb 少 1 轮；
- no-kb 记录的 lint time 少 8.68s；
- with-kb lint time 比 no-kb 高约 1.5%；
- 两边最终都清到 `0 errors / 0 warnings`；
- 本轮 with-kb 没有体现轮数或速度优势。

## no-kb 修复过程概览

no-kb 共 14 轮。前几轮主要清 error 和大类 warning；中后期逐步压低剩余 warning；最后 3 轮集中清尾部 warning。

关键阶段：

| round | post E/W/I |
|---:|---:|
| 1 | 4185/5081/7 |
| 4 | 3094/4606/7 |
| 7 | 714/3294/7 |
| 8 | 220/2966/12 |
| 11 | 0/2854/11 |
| 12 | 0/14/4 |
| 13 | 0/6/3 |
| 14 | 0/0/3 |

可以看到 no-kb 在第 11 轮已经清掉所有 error，随后主要处理 warning tail。

## with-kb 修复过程概览

with-kb 共 15 个有效轮次。早期两次 broad trial patch 被回退，未计入有效轮数。有效轮次中，前 10 轮主要处理 error、结构性 warning 和大规模重复 tag；第 11 轮后 error 清零，后续集中清 `W240` 类 warning。

关键阶段：

| round | E/W/I |
|---:|---:|
| 1 | 4731/5299/10 |
| 4 | 3449/4661/7 |
| 7 | 1240/2274/7 |
| 10 | 9/863/5 |
| 11 | 0/657/3 |
| 12 | 0/457/3 |
| 13 | 0/257/3 |
| 14 | 0/57/3 |
| 15 | 0/0/3 |

with-kb 同样在第 11 轮清掉 error，但 warning tail 比 no-kb 多用了一轮。

## 为什么 with-kb 没有明显优势

### 1. 每轮上限较大，降低了 KB 的边际收益

本轮允许每轮修复 100-200 个 module。no-kb 虽然没有 KB，但可以通过当前 SpyGlass 报告发现大量相似结构，然后批量 patch。只要这些 pattern 足够规律，no-kb 就能快速形成局部经验。

KB 的价值通常在于缩短 root-cause 判断时间、减少错误方向、避免 waiver 或错误修法。但当每轮可以大批量处理相似问题时，no-kb 可以用“报告驱动 + 局部归纳”的方式追上 with-kb。

### 2. violation 数量大，但 tag family 不算多

本轮有接近 10000 条 actionable violation，但 unique tag 只有 29 个。规模很大并不等于问题类型复杂。大量 violation 聚集在少数 tag 上，例如 `sim_race02`、`W240`、`W528`、`W415`、`NoAssignX-ML` 等。

这种分布有利于 no-kb：一旦识别出某个 tag 在本 RTL 中的常见根因，就可以跨多个 module 批量修复。

### 3. 生成式 lint lab 仍然有结构规律

本次已经避免机械复制，也构造了多种不同 pattern，但 RTL 仍来自同一个 lint lab generator。真实项目中，不同模块通常来自不同作者、不同时期、不同编码风格和不同约束假设；而 generator 输出仍有较强统一结构。

统一结构让 no-kb 更容易从局部报告中学习修复策略。

### 4. with-kb 只拿到有限 prompt KB excerpt

with-kb 并不是完整知识库检索，而是只拿到 prompt 内嵌的一小段 tag-specific KB 摘要。它能给出方向，但不能覆盖所有 tag，也不能知道当前 generator 的 clean 模板或每个变体的具体结构。

因此 with-kb 的帮助主要集中在少数 tag family 上。对于 `W240`、`W528`、`ParamWidthMismatch-ML` 等大量 tail warning，KB excerpt 的直接帮助有限。

### 5. worker 执行路径也会带来波动

with-kb 记录中有两个早期 broad trial patch 被回退，虽然没有计入有效轮次，但实际 wall clock 会受影响。no-kb 的路径在这次实验中更直接，尤其后期 warning tail 收敛更快。

这说明对比结果不仅受 KB 影响，也受 worker 的 patch selection、批处理顺序、回退策略影响。

## 对“是否需要 KB”的判断

对于这类 lint lab 批量修复作业，结论不是“KB 没用”，而是：

```text
KB 不应作为必需条件；更适合作为疑难 tag 和不收敛场景的辅助。
```

具体建议：

| 场景 | 是否建议用 KB |
|---|---|
| 小规模、tag 明确、重复高 | 可不用 KB |
| 大规模、结构规律强、允许大批量 patch | KB 收益有限 |
| 同 tag 多根因、真实项目上下文复杂 | 建议用 KB |
| 新人或不熟 SpyGlass 规则 | 建议用 KB |
| 修复不收敛或反复引入新 warning | 建议查 KB |
| 需要审查解释、规则引用、修法依据 | 建议用 KB |

对当前 lint lab，最佳策略应是：

```text
报告驱动修复为主，KB 作为疑难 tag / 多根因 tag / 不收敛时的辅助。
```

不建议每条 violation 都查 KB，否则会拖慢；也不建议完全禁用 KB，因为真实复杂 case 中 KB 可以避免走错方向。

## 实验计量限制

本轮有一个明确计量缺口：两个 worker 没有一致记录每轮 `analysis_seconds` 和 `edit_seconds`。

具体表现为：

- with-kb JSON 中每轮 `analysis_seconds` 和 `edit_seconds` 为 `null`，但记录了每轮 `lint_seconds`；
- no-kb JSON 记录了每轮 E/W/I 和聚合 lint/wall time，但没有完整记录每轮分析和修改耗时；
- 因此最可靠的对比指标是自然修复轮数和 MCP lint wall time；
- end-to-end wall clock 只能作为参考，不能严格归因。

后续如果要更准确评估 KB 收益，应强制每轮记录：

```text
analysis_seconds
edit_seconds
kb_seconds
lint_seconds
selected_tags
patched_modules
changed_lines
pre/post E/W/I
newly introduced findings
```

并且最好由主调度脚本统一打点，而不是依赖 worker 自行记录。

## 后续实验建议

如果目标是更准确衡量 KB 的价值，可以做以下几组实验：

1. **降低每轮 patch 上限**

   例如限制为每轮 20-50 modules。这样 KB 在选择优先 tag、判断根因方面的价值更容易体现。

2. **提高 tag 多样性和根因多样性**

   不只增加 violation 数量，还要增加不同 tag family、不同根因、跨模块依赖、工具级误导信息。

3. **加入真实 RTL case**

   从真实项目历史 lint 修复中抽取 case，比 generator 更能体现 KB 的项目经验价值。

4. **统一自动计时**

   每轮由外层 harness 统一记录分析、修改、KB 查询、lint 的耗时，避免两个 worker 记录口径不一致。

5. **区分“规则知识收益”和“执行策略收益”**

   with-kb 的优势应体现在更少误修、更少回退、更快定位复杂根因，而不是单纯靠更大 patch 批量。

## 结论

本次 10000 violation strict live repair 对比中：

```text
no-kb:   14 rounds, 568.01s recorded lint time, final 0E/0W/3I
with-kb: 15 rounds, 576.69s recorded lint time, final 0E/0W/3I
```

在每轮修复上限放大的条件下，with-kb 没有显示出速度或轮数优势。原因主要是本轮问题虽然数量大，但 tag family 有限、结构规律较强，no-kb 可以通过当前报告快速归纳并批量修复。

因此，对于当前这种 lint lab 批量修复任务，KB 更适合做辅助，而不是强依赖。真正能体现 KB 价值的场景，应是根因更复杂、规则语义更容易误判、跨模块上下文更多、修复不收敛风险更高的真实 RTL lint 修复任务。

## 关联产物

- Common summary: `ip/digital/lint_lab/docs/modelrepair_findings10000_20260704_130000_common_summary.md`
- no-kb result: `ip/digital/lint_lab/docs/modelrepair_findings10000_20260704_130000_no_kb_result_20260704_151748.md`
- with-kb result: `ip/digital/lint_lab/docs/modelrepair_findings10000_20260704_130000_with_kb_result_20260704_150326.md`
- Comparison summary: `ip/digital/lint_lab/docs/modelrepair_findings10000_20260704_130000_comparison_summary.md`
- Machine-readable comparison: `ip/digital/lint_lab/docs/modelrepair_findings10000_20260704_130000_comparison_summary.json`

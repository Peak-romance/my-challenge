# L3 · 循环层（Loop）

## 职责
把五层缝成一条可重复执行的路径。**只做三件事**：分发、守预算、记账。
业务逻辑一律下沉——否则循环会退化成"什么都干、什么都干不好"的上帝对象（ADR-8）。

## 七节拍

| 节拍 | 动作 | 实现 | 失败处理 |
| --- | --- | --- | --- |
| perceive | 任务规范化、生成 `run_id`、S 层 `turns+1` | `loop.run` 前 30 行 | 空任务抛 `ValueError` |
| recall | K/A 检索 top-5 | `KStar.recall` | 空召回不算失败，记 `recall_miss` |
| plan | 五级优先级选路 | `plan.plan` | 任何规划异常 → 兜底 `answer` |
| act | 技能或工具序列执行 | `skills.run` / `_run_tools` | 见下方"失败分支" |
| observe | 每步 `ms/args/ok/out` 入 trace | `ctx.emit_step` | — |
| reflect | 算 quality、选 1 条教训 | `reflect.evaluate` | 不抛异常，最坏返回 `lesson=None` |
| persist | 写 T、条件写 A、更新 S.focus | `_persist` | 写失败向上抛（记账不可静默丢失） |

## 规划的五个优先级

```
1. @skill-name            显式指定，最高优先级（人明确说了算）
2. 多意图分解             一句话多件事；若该序列已被技能覆盖 → 直接走技能（进化闭环）
3. 记忆意图               记住 / 记待办 / 完成待办 / 查状态（即时生效，不依赖技能）
4. 技能触发词             长度加权的触发词匹配
5. 兜底应答               基于 K/A 召回组织参考；无召回则明确告知"知识缺口"
```

顺序不是拍脑袋：**越具体越靠前**。曾经把"状态查询"放在技能匹配之前，导致 `系统状态` 被
泛化关键词 `状态` 抢走，`self-check` 技能永远不触发——这是实测发现并修正的排序缺陷。

### 多意图分解（本层的核心增量）

```python
"记住：A；记个待办：B"  →  steps = [memory.remember(A), memory.open_loop(B)]
```

- 分割符：`；;`、`然后`、`接着`、`之后`、`. `（句号+空格）。
- **任一段解析不出 → 整体放弃**，退回常规路径。宁可只做对一件事，也不做错一半。
- 若组合后的工具序列已被某技能覆盖 → `kind=skill`，并在 rationale 里写明"进化闭环"。

## 预算与熔断

| 预算 | 默认 | 检查位置 | 命中行为 |
| --- | --- | --- | --- |
| `max_steps` | 30 | 技能每步前 / 工具序列每步前 | 返回 `ok=False`，携带已完成的 outputs |
| `tool_timeout_s` | 20 | `subprocess` / `urllib` | 单步 `ToolError` |
| `run_timeout_s` | 180 | 工具序列每步前 | 中断并收敛 |
| `max_output_chars` | 4000 | `truncate()` | 截断并标注原长 |

## 反思：quality 怎么算

```
success  = 成功步数 / 总步数            （无步骤时按输出是否为空给 1.0 / 0.6）
quality  = success × (输出非空 ? 1 : 0.4) × (有 error ? 0.3 : 1)
```

教训候选按 `importance` 择一入库：

| kind | 触发条件 | importance | action 示例 |
| --- | --- | --- | --- |
| `failure` | 有步骤失败或有 error | 0.85 | 补前置校验或降级路径 |
| `gap` | 兜底应答且无召回 | 0.70 | 同类任务再出现就抽成技能 |
| `weak_skill` | 兜底应答但有召回 | 0.55 | 抽成技能，不要靠记忆应答 |
| `success` | 走技能且 quality=1.0 | 0.40 | 维持 |
| `recall_miss` | 无召回且非兜底 | 0.50 | 事后回填背景知识 |

**每次只写一条**：A 层的价值在信噪比，不在条数。同类同文还会合并加权（`KStar.write_lesson`）。

## 失败分支

| 情形 | 行为 |
| --- | --- |
| 技能 `on_error=abort` 且某步失败 | `ok=False`，output 为空，返回 `partial` 摘要 |
| 技能 `on_error=continue` | 继续执行，失败步以 `[ERROR] ...` 占位进入后续步骤 |
| 工具序列某步失败 | 立即中断，返回已完成部分的拼接输出 |
| 显式技能名不存在 | `ok=False`，error 列出已装载技能 |
| 预算耗尽 | `ok=False`，已完成的输出仍然返回（信息不浪费） |

## 记账（T 层字段）

```json
{"run_id","ts","source","session","task","planner","plan",
 "recall":[{"id","layer","score","text"}],
 "steps":[{"i","id","tool","args","ok","ms","out","err"}],
 "steps_used","output","ok","error","quality","ms","lesson"}
```

这张表就是"可追溯"的全部内容：**想干什么（plan）、依据什么（recall）、实际动了什么（steps）、学到什么（lesson）**。

## 验收
- `python agent.py --demo`：7 个任务，`quality` 全为 1.0
- `t_skill_budget_guard`：`max_steps=1` 时简报技能必须熔断
- `t_end_to_end`：三个任务后 T 层至少 3 条轨迹且字段完整

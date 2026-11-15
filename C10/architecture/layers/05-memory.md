# L5 · 记忆层（KSTAR）

## 职责
跨会话存续。四层不是四种格式，而是**四个不同的问题**。

| 层 | 问题 | 存储 | 生命周期 | 写入权限 |
| --- | --- | --- | --- | --- |
| **K** Knowledge | 什么是稳定成立的？ | `memory/k/knowledge.jsonl` | 长期，随使用加权 | 仅显式调用 |
| **S** State | 此刻在做什么？什么未闭环？ | `memory/s/state.json` | 会话级，频繁覆写 | 循环自动更新 |
| **T** Trajectory | 上次到底发生了什么？ | `memory/t/<date>.jsonl` | 全量，**不可变** | 循环自动追加 |
| **A** Archive (R) | 从那次经历学到什么？ | `memory/a/lessons.jsonl` | 长期，带证据链 | 仅反思模块 |

## 字段契约

### K（`schemas/kstar.schema.json`）
```json
{"id":"k-20261115-xxxxxx","layer":"K","kind":"fact","text":"...","tags":["c10"],
 "source":"run:run-xxx","importance":0.76,"confidence":0.8,
 "created":"...","last_used":"...","use_count":3,"status":"active"}
```
`status`: `active | archived`。`importance` 是**动态权重**，不是创建时的静态标签。

### S
```json
{"session":"default","turns":31,"created":"...","updated":"...",
 "focus":"最近一次任务","last_task":"...",
 "open_loops":[{"id":"loop-...","text":"...","created":"..."}],
 "recent":[{"ts":"...","task":"...","run_id":"..."}]}
```
容量策略：`recent` 保留 10 条、`open_loops` 上限 12 条、同文待办归一化去重。

### T（`schemas/trace.schema.json`）
见 `03-loop.md` 的"记账"节。**只追加，任何路径不得回改**——可追溯性是不可协商的。

### A
```json
{"id":"a-...","layer":"A","kind":"failure|gap|weak_skill|success|recall_miss",
 "text":"...","evidence":"run-20261115-xxxxxx","action":"...",
 "importance":0.85,"created":"...","last_used":"...","use_count":1,"status":"active"}
```
`evidence` 必须指向 T 层 `run_id`。没有证据的"教训"不是教训，是印象。

## 检索（`memory/retrieve.py`）

### 分词
英文按词；中文取**相邻二元组**，并过滤停用词与"全虚词二元组"；整词仅一字时用独字兜底。

```
"长期智能体的记忆系统" → 长期 期智 智能 能体 体的 的记 记忆 忆系 系统
```
**为什么不用单字**：单字会引入大量虚词噪声（的/了/是），实测把无关记忆顶到召回首位。
**为什么过滤停用词**：`一下`、`这个` 这类二元组会让任意两条中文文本"看起来相关"。

### 打分
```
BM25(q, doc) × (0.6 + 0.4 × importance) + 0.35 × 0.5^(age_days/30) + 0.15 × min(1, use_count/10)
```
- BM25 部分：词面相关性（k1=1.2, b=0.6）
- importance：越常用越重要（使用即强化）
- 时间衰减：半衰期 30 天
- use_count：冷启动保护，避免新知识永远排在后面

### 反噪声原则（本层最重要的一条）
**无词面命中的条目一律不进入召回集。**
宁可返回空集（暴露知识缺口，被反思登记为 `recall_miss`），也不用"高重要度但不相关"的记忆填充上下文。
原因：噪声召回是**看起来有依据的错误**，比召回失败更难被发现，也更伤信任。

## 维护作业

| 作业 | 触发 | 规则 |
| --- | --- | --- |
| 强化 | 每次召回命中 | `use_count+1`、`importance+0.02`（上限 1.0） |
| 去重 | 写入 K / A / 待办 | 归一化（去空白+小写）后比对；重复只加权不新增 |
| 衰减 | `--consolidate` | ≥7 天未使用：`importance × 0.97^周数` |
| 归档 | 衰减后 | `importance < 0.15` 且 `use_count ≤ 1` → `status=archived`（保留可捞回，不物理删除） |
| 容错 | 读取时 | JSONL 坏行跳过；`state.json` 损坏 → 重建空态并标记 `_recovered` |

**为什么归档而不是删除**：记忆系统的错误成本不对称——误删一条真知识不可恢复，误留一条噪声只是降低排序。
所以策略永远是"降权 + 归档"，把最终判断权留给检索与人的检索。

## 一致性保证

| 风险 | 手段 |
| --- | --- |
| 半写损坏 | JSONL 追加写；`state.json` 与重写操作用临时文件 + 原子 `replace` |
| 并发写 | 当前单进程设计，未加锁（已知限制，见 AGENT.md §10） |
| 记忆被旁路修改 | 只允许经 `KStar` 访问（不变量 3） |

## 规模与迁移
当前适合 10³–10⁴ 条。迁移触发条件：K 层 > 5,000 条或召回 P95 > 100ms。
迁移方式：实现同签名 `KStar` 子类（`remember / recall / state / append_trace / write_lesson`），
替换 `Agent(memory=...)` 即可，**上层零改动**。

## 验收
- `t_tokenize` / `t_rank_relevance`：分词含目标二元组、无关查询返回空
- `t_kstar_knowledge`：同文去重 + `use_count` 递增
- `t_kstar_lesson`：同类同文教训合并加权
- `t_kstar_decay`：旧条目被归档
- `python agent.py --stats`：四层计数可见

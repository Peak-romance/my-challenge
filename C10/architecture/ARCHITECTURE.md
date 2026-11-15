# ARCHITECTURE · C10 第二大脑

> 本文件面向"要改它的人"，回答三个问题：**层与层之间靠什么耦合？为什么这样设计？改哪里会崩？**
> 如果你只想跑起来，读 `../AGENT.md` 第 0 节即可。

---

## 1. 分层契约（唯一允许的跨层引用）

| 调用方向 | 允许 | 禁止 | 强制手段 |
| --- | --- | --- | --- |
| L1 接口 → L3 循环 | ✅ `Agent.run()` | L1 直接调工具/碰记忆 | 接口层只 import `core.loop` |
| L3 循环 → L2 工具 / L4 技能 / L5 记忆 | ✅ 经 `RunContext` | L3 里内联业务逻辑 | 循环层只有分发、预算、记账 |
| L4 技能 → L2 工具 | ✅ 经技能运行时的 `tools.call` | 技能直接读写文件 | 技能只有声明，没有代码 |
| L2 工具 → L5 记忆 | ✅ 只经 `ctx.memory`（KStar） | 工具直接 open() `memory/*.jsonl` | `KStar` 是唯一入口 |
| L5 记忆 → L2 工具 | ❌ 反向依赖一律禁止 | 记忆层 import 工具层 | 依赖方向单向向下 |
| L3 循环 → L1 接口 | ❌ 只通过返回值 | 循环里 print/读 stdin | `verbose` 回调由接口注入 |

**唯一总线**：`RunContext`（`src/core/types.py`）。它携带 `run_id / task / memory / tools / skills / budget / depth / steps_used / allow_danger / on_step`。
禁止用全局变量或单例传递运行态——那会让"一次运行"变成"一个进程"，测试与并发都无从谈起。

```
                 ┌──────────── RunContext（唯一总线）────────────┐
                 │  run_id · task · budget · steps_used · depth  │
                 └───────────────────────────────────────────────┘
   L1 ──run()──► L3 ──plan──► L4 ──call──► L2 ──read/write──► L5
                 │                                        ▲
                 └────────── recall / persist ────────────┘
```

---

## 2. 运行时序（含失败分支）

```
run(task)
 ├─ S.touch_state(turns+1, focus=task)          # 失败：状态文件损坏 → 自动重建空态
 ├─ K/A.recall(task, k=5)                       # 失败：返回空集（不抛异常，记为 recall_miss）
 ├─ planner.plan(task, ctx, recall)
 │    ├─ @skill  → kind=skill
 │    ├─ 多意图    → 命中既有技能签名？ kind=skill : kind=tools(多步)
 │    ├─ 记忆意图  → kind=tools(单步)
 │    ├─ 触发词    → kind=skill
 │    └─ 兜底      → kind=answer
 ├─ dispatch
 │    ├─ skill : skills.run()  ── 步骤失败且 on_error=abort → 整条失败（返回 partial）
 │    │                          └ 步骤失败且 on_error=continue → 继续，输出含 [ERROR] 占位
 │    └─ tools : 逐步 tools.call() ── 任一步失败 → 中断并携带已完成输出
 ├─ reflect.evaluate() → (quality, 1 条 lesson)
 ├─ persist: T.append_trace(不可变) + A.write_lesson(条件) + S.focus
 └─ return RunResult(output, ok, quality, lesson, ms)
```

**关键设计**：失败不抛到接口层。`run()` 永远返回 `RunResult`（`ok=False` 时带 `error`），
因为"任务失败"本身是要被记忆和复盘的事件，而不是程序异常。

---

## 3. 架构决策记录（ADR）

### ADR-1 记忆用 JSONL 而非 SQLite
- **背景**：记忆需要可读、可 diff、可人工修复、可随仓库分发。
- **决策**：四层各用 JSONL/JSON，线性扫描 + 内存排序。
- **后果**：万条以上检索退化为 O(n)。**迁移触发条件**：K 层 > 5,000 条或召回 P95 > 100ms → 换 SQLite FTS5，接口不变（`KStar.recall` 为唯一入口）。

### ADR-2 技能契约用 JSON，文档用 Markdown
- **背景**：YAML frontmatter 一文件写完更"时髦"，但需要自写 YAML 子集解析器。
- **决策**：`skill.json`（严格校验）+ `SKILL.md`（人读）。装载器只读 JSON。
- **后果**：一个技能两个文件。换来的是"不会因为一个缩进把整条技能链解析成空"。

### ADR-3 默认规则规划器，LLM 作为可选增强
- **背景**：评审者可能没有 API Key；但纯规则的上限明显。
- **决策**：`build_planner()` 按环境变量选择；`LLMPlanner` 任何异常（超时/解析失败/额度）都降级到 `RulePlanner`。
- **后果**：可运行性 100%，智能上限取决于配置。这是**刻意的优先级排序**：跑不起来的"更聪明"等于零分。

### ADR-4 中文检索不引入 embedding
- **背景**：中文分词需要词典（jieba 等），embedding 需要模型。
- **决策**：相邻二元组 + 停用词过滤 + 独字兜底；BM25(k1=1.2,b=0.6) 打分。
- **后果**：同义改写命中率低于向量检索；换来零依赖与可解释（能打印命中词）。旁路方案见 ADR-4 补充：`retrieve.rank` 是唯一排序入口，加向量只需改此函数。

### ADR-5 写入边界 = 项目根，而非独立 workspace
- **背景**：最初设计为"写只允许 `workspace/`，读允许项目根"，实测立刻出现"能读 `src/tools` 却不能写"的割裂，且相对路径基准不一致导致 `巡检 src/tools` 解析到 `workspace/src/tools`（不存在的目录）。
- **决策**：读写同界（项目根），相对路径永远相对项目根。
- **后果**：智能体可以改动自己的代码目录（`danger=1` 全部进 trace，可审计）。边界从"目录隔离"转为"根隔离 + 危险分级 + 轨迹留痕"。

### ADR-6 A 层只由反思写入，且必须带 evidence
- **背景**：教训如果允许随便写，A 层会退化成第二份笔记。
- **决策**：`write_lesson` 必须传 `kind`，`evidence` 指回 T 层 `run_id`；每次运行最多写 1 条（取 importance 最高者）。
- **后果**：A 层条目数 ≈ 运行数的上界，可控；代价是"同一次运行的其他小教训"会被丢弃。

### ADR-7 技能挖掘必须人工上线
- **背景**：自动挖掘能发现重复序列，但不知道序列的**语义边界**。
- **决策**：草案写 `skills/_proposed/`（`status=proposed`，装载器默认跳过），`--promote` 才生效。
- **证据**：草案中的参数是 `<从轨迹补全: xxx>` 占位符，直接 promote 会让技能写出垃圾数据；`tests/test_smoke.py::t_miner` 把这一点固化成断言（验证"可上线"，而非"可直接用"）。

### ADR-8 循环层不写业务逻辑
- **背景**：最容易腐化的地方是 `loop.py`——它离所有能力都近。
- **决策**：`Agent.run` 只做四件事：分发、守预算、记账、返回。任何"具体怎么干"下沉到工具或技能。
- **后果**：新增能力不改循环层；代价是有些一次性逻辑会被迫先抽象成工具（这恰恰是我们想要的约束）。

---

## 4. 失败模式与对策（对照实现）

| 失败模式 | 现象 | 对策 | 代码位置 |
| --- | --- | --- | --- |
| 参数拼错 | 工具静默返回空，上层误判成功 | 严格参数校验，未知参数直接 `ToolError` 列出允许项 | `tools/base.py::Registry._bind` |
| 工具内部异常 | 整个循环崩掉 | 捕获所有异常降级为步骤失败 | `Registry.call` |
| 命令注入 / 越界写 | 破坏系统 | 首命令白名单 + 路径沙箱 + `danger≥2` 需显式授权 | `tools/builtin.py` |
| 步数失控 | 长任务跑飞、上下文爆炸 | `max_steps` / `tool_timeout_s` / `max_output_chars` 三重熔断 | `core/loop.py`、`skills/runtime.py` |
| 技能损坏 | 一个坏技能拖垮全部装载 | 逐个装载 + 告警隔离；损坏项进入 `warnings` | `skills/loader.py::load_all` |
| 记忆污染 | 无关记忆被召回，输出"看起来有依据" | 无词面命中即不召回；停用词过滤；同文去重 | `memory/retrieve.py`、`kstar.py` |
| 状态文件损坏 | 启动即崩 | 捕获异常重建空状态并标记 `_recovered` | `KStar.state` |
| JSONL 坏行 | 整层记忆读取失败 | 逐行容错，跳过坏行 | `KStar._read` |
| 教训灌水 | A 层被同一条反复淹没 | 同类同文合并加权；每次运行最多 1 条 | `reflect.evaluate`、`KStar.write_lesson` |
| 重复待办 | S 层堆积同一件事 | 归一化去重（`_norm` 去空白转小写） | `KStar.add_open_loop` |

---

## 5. 不变量（改代码时必须保持）

1. **T 层只追加**：任何路径都不得修改已写入的轨迹行。
2. **A 层必带 evidence**：无 `run_id` 指向的教训不得入库。
3. **记忆读写只经 KStar**：`memory/` 目录不得被其他模块直接 open。
4. **工具无状态**：同一工具在同样参数下行为不依赖调用历史（记忆工具除外，它显式改状态）。
5. **循环层不 print**：所有输出走 `RunContext.on_step` 回调，由接口层决定呈现方式。
6. **技能不含代码**：技能只有声明式步骤，执行语义完全由工具定义。

---

## 6. 扩展路径（不改内核）

| 想做的事 | 改动点 | 是否需要动 L3 |
| --- | --- | --- |
| 加一个能力 | 写 `src/tools/builtin.py` 一个 `@reg.register` 函数 | 否 |
| 加一个重复任务的封装 | 写 `skills/<name>/skill.json` + `SKILL.md` | 否 |
| 换存储（SQLite/向量） | 实现同签名的 `KStar` 子类，替换 `Agent(memory=...)` | 否 |
| 换规划器 | 实现 `plan(task, ctx, recall) -> Plan` | 否 |
| 加接口（IM / 定时器） | 在 `src/interfaces/` 加一个文件调 `Agent.run` | 否 |
| 加记忆层 | 改 `KStar.recall` 的 layers 参数与写入策略 | 是（需同步 schema 与文档） |

---

## 7. 性能与规模（实测，非估算）

| 场景 | 观测值 | 说明 |
| --- | --- | --- |
| 单步工具调用（纯计算） | 0–1 ms | `time.now` / `format.bullets` |
| 记忆写入（含去重扫描） | 4–20 ms | 与 K+A 条目数线性相关 |
| 召回 top-5（31 条记忆） | < 1 ms | BM25 全量打分 |
| 完整技能（5–7 步） | 10–30 ms | 含 2 次记忆读写 |
| 挖掘（31 条轨迹） | 7 ms | 序列统计 + 文件写入 |
| `self-check`（7 步） | 23 ms | 含一次 dry-run 挖掘 |

**规模上限**：当前实现适合 10³–10⁴ 条记忆 / 10³ 条轨迹。超过时优先改 `KStar.recall`（加索引或向量旁路），其次是轨迹分片归档。

---

## 8. 与常见做法的差异

| 常见做法 | 本系统的做法 | 差异的代价 / 收益 |
| --- | --- | --- |
| 单一对话历史当记忆 | 四层分工，历史只是 T 层的一种 | 更复杂；换来"知识/状态/轨迹/教训"各自可维护 |
| 全量历史塞进上下文 | 只召回 top-5，T 层不进上下文 | 可能漏信息；换来上下文稳定、成本可控 |
| Agent 内联 if-else 编排 | 技能声明式编排 | 前期要多写一层抽象；换来能力可发现、可校验、可挖掘 |
| 记忆"只写不删" | 衰减 + 归档 | 需要调参；换来信噪比不随时间坍塌 |
| 自动挖掘直接上线 | 人工闸门 | 进化有人力成本；换来不会把偶然固化成制度 |

---

_配套阅读：`layers/01-interface.md` ~ `layers/05-memory.md`（逐层深潜）、`schemas/*.json`（数据契约）。_

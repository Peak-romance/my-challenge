# AGENT.md · C10 · 第二大脑（Second Brain）

> **一句话定位**：把"每次对话都从零开始"的助手，改造成**每一次使用都更懂你**的长期智能体。
>
> **交付物入口**：本文件 → `architecture/`（架构） → `AAR/AAR.md`（复盘） → `AI日志/AI日志.md`（AI 使用追溯）
>
> **可运行性**：零第三方依赖，Python 3.10+，`python agent.py --demo` 一条命令跑通全链路。

---

## 0. 30 秒上手

```bash
cd D:\C10

python agent.py --demo                 # 端到端演示：7 个任务，覆盖五层 + KSTAR 四条写入路径
python agent.py "生成今日简报"          # 单次任务
python agent.py                        # 交互模式（REPL）
python agent.py --stats                # 记忆分层统计
python agent.py --mine                 # 从历史轨迹挖掘技能草案
python tests/test_smoke.py             # 自检：12 项契约断言
```

| 命令 | 作用 |
| --- | --- |
| `python agent.py "<任务>"` | 执行一次任务，打印 plan / 逐步 trace / 反思结论 / 输出 |
| `python agent.py` | 交互模式，`?` 查看命令 |
| `--demo` | 完整演示脚本（评审用） |
| `--stats` / `--state` | 查看 KSTAR 分层统计 / S 层工作状态 |
| `--tools` / `--skills` | 查看工具与技能装载情况（含契约校验结果） |
| `--mine` / `--promote <name>` | 挖掘技能草案 / 把草案提升为正式技能 |
| `--consolidate` | 记忆巩固：衰减 + 归档 |
| `--remember "<事实>"` | 直接写入 K 层 |
| `--serve [port]` | 以 HTTP 接口启动（`POST /run`） |
| `--json` | 机器可读输出（含 run_id、召回、质量分） |

---

## 1. 它解决什么问题

通用助手有三个结构性失效模式，只在"长期使用"时才暴露：

| 失效模式 | 表现 | 本系统的设计答案 |
| --- | --- | --- |
| **记忆断裂** | 上次说过的偏好，这次又要说一遍 | KSTAR 四层记忆 + 每轮自动召回（L5） |
| **经验不沉淀** | 同一个坑踩三次，没人记得 | T 层轨迹全量留痕 → A 层教训蒸馏 → K 层事实固化（L5 + L3 反思） |
| **重复劳动不可复用** | 同样的五步操作，每次重新组织 | 声明式技能 + 从轨迹自动挖掘草案（L4） |

因此本系统的核心不是"更会聊天"，而是**三个闭环**：记忆闭环、能力闭环、契约闭环（见第 6 节）。

---

## 2. 五层架构

```
┌──────────────────────────────────────────────────────────────┐
│  L1 接口  CLI · REPL · HTTP · (可扩展: 定时器/IM)              │
│      职责：协议适配。把外部输入规范化为一次 run()，不含业务逻辑   │
├──────────────────────────────────────────────────────────────┤
│  L2 工具  20 个声明式工具（fs / memory / skill / shell / http） │
│      职责：唯一的副作用出口。显式参数契约 + 危险分级 + 沙箱        │
├──────────────────────────────────────────────────────────────┤
│  L3 循环  perceive→recall→plan→act→observe→reflect→persist     │
│      职责：分发、守预算、记账。业务逻辑一律下沉，避免上帝对象      │
├──────────────────────────────────────────────────────────────┤
│  L4 技能  6 个已上线技能 + 自动挖掘器 + 人工上线闸门             │
│      职责：把重复任务固化为可校验、可组合、可演化的契约           │
├──────────────────────────────────────────────────────────────┤
│  L5 记忆  KSTAR 四层：K 知识 · S 状态 · T 轨迹 · A 归档          │
│      职责：跨会话存续。写入有策略、读取有排序、定期有巩固与遗忘     │
└──────────────────────────────────────────────────────────────┘
```

| 层 | 实现位置 | 关键契约 | 失败模式与对策 |
| --- | --- | --- | --- |
| L1 接口 | `src/interfaces/` | 只做输入规范化与输出格式化 | 接口崩溃不影响内核；换接口零改动下层 |
| L2 工具 | `src/tools/base.py`、`builtin.py` | 参数表声明 + `danger` 分级 + 路径沙箱 | 参数错误显式 `ToolError`，绝不静默返回空 |
| L3 循环 | `src/core/loop.py`、`planner.py`、`reflect.py` | 步数/超时/输出三重预算 | 预算耗尽→保留已得信息收敛输出，不中断系统 |
| L4 技能 | `src/skills/`、`skills/`、`src/core/miner.py` | `skill.json` 可执行契约 + `SKILL.md` 人读文档 | 单技能损坏不影响其余装载（隔离装载 + 告警） |
| L5 记忆 | `src/memory/kstar.py`、`retrieve.py` | 四层职责不越界，写入需通过 KStar 单一入口 | 状态损坏自动重建；JSONL 坏行容错跳过 |

**分层的判据**：能不能在不改下层的前提下换掉这一层？五层都通过：
换 CLI 为飞书机器人（只动 L1）、换 BM25 为向量检索（只动 L5）、换规则规划器为 LLM（只动 L3，已有 `LLMPlanner` 实现）。

---

## 3. 一次运行到底发生了什么

真实轨迹（`memory/t/2026-11-15.jsonl` 中的一条，已精简）：

```json
{
  "run_id": "run-20261115-0c640d",
  "task": "记个待办：验证遗忘阈值从 0.15 调到 0.2 的影响",
  "planner": "rule",
  "plan": {"kind": "tools", "rationale": "识别到『待办』意图 → 登记到 S 层未闭环事项"},
  "recall": [{"id": "a-20261115-af0490", "layer": "A", "score": 18.99}],
  "steps": [{"i": 1, "tool": "memory.open_loop", "ok": true, "ms": 0,
             "out": "已登记未闭环事项: 验证遗忘阈值从 0.15 调到 0.2 的影响"}],
  "ok": true, "quality": 1.0, "ms": 32, "lesson": null
}
```

节拍：

1. **perceive**：任务规范化，`run_id` 生成，S 层 `turns+1`。
2. **recall**：K/A 两路检索（BM25 × 重要度 + 时间衰减 + 使用频率），命中即强化。
3. **plan**：`@技能` → 多意图分解 → 记忆意图 → 技能触发词 → 兜底应答，五级优先级。
4. **act**：技能或工具序列执行，每步检查预算、记录 `ms/args/ok/out`。
5. **reflect**：算 `quality`（成功率 × 输出非空 × 无错误），沉淀**至多一条**最高价值教训。
6. **persist**：写 T 层轨迹（不可变）、条件写 A 层、更新 S 层焦点。
7. **respond**：输出 + 一份可回放的执行记录。

终端里看到的样子：

```
[run] run-20261115-38405e · source=cli · session=default
[recall] 5 条 (K:C10 采用五层架构…, A:任务『记个待办…』…)
[plan] skill `memorize-loop` — 该组合已被技能覆盖 → 走技能（进化闭环）
  [1] memory.remember      ok       4ms
  [2] memory.open_loop     ok       8ms  已登记未闭环事项: 给 memorize-loop 补一条回归用例
[reflect] quality=1.00 steps=2/2 lesson=success
```

---

## 4. KSTAR 四层记忆（L5 核心）

### 4.1 四层分工

| 层 | 名称 | 回答的问题 | 存储 | 生命周期 | 容量策略 |
| --- | --- | --- | --- | --- | --- |
| **K** | Knowledge 知识 | "关于这个世界/这个人，什么是稳定成立的？" | `memory/k/knowledge.jsonl` | 长期，随使用加权 | 去重 + 衰减 + 归档 |
| **S** | State 状态 | "此刻我们在做什么？什么还没闭环？" | `memory/s/state.json` | 会话级，频繁覆写 | 最近 10 条 / 待办 12 条上限 |
| **T** | Trajectory 轨迹 | "上次到底发生了什么？" | `memory/t/YYYY-MM-DD.jsonl` | 全量追加，**不可变** | 按天分片，只追加 |
| **A** | Archive 归档（R=Reflection） | "从那次经历里学到了什么？" | `memory/a/lessons.jsonl` | 长期，带证据链 | 同类同文合并加权 |

四层的判据是**回答的问题不同**，不是"数据格式不同"。这决定了它们的写入权限也不同：

- K 只能被**显式调用**写入（`memory.remember` / `capture-note` / `memorize-loop`），不允许系统"顺手猜一条"。
- S 每轮自动更新，但只允许结构化字段（turns / focus / open_loops / recent），不接受自由文本堆积。
- T **只追加**，任何情况不得回改——可追溯性是不可协商的。
- A 只能由反思模块写入，且**必须带 `evidence`（指回 T 层的 run_id）**，否则视为无根之谈。

### 4.2 写入 / 读取 / 巩固 / 遗忘

| 动作 | 触发时机 | 规则 |
| --- | --- | --- |
| 写入 K | 显式 `remember`、技能捕获 | 同文去重（重复只升 `importance` 与 `use_count`，不重复膨胀） |
| 写入 S | 每轮运行 | `turns+1`、`focus` 跟随、`recent` 保留 10 条、未闭环去重 |
| 写入 T | 每轮运行 | 全量字段：plan / recall / steps / quality / lesson / ms |
| 写入 A | 反思阶段（每次至多 1 条） | `kind + text + evidence + action` 四要素齐全 |
| 读取 | 每轮开始 | K/A 混合检索 top-5；S 直读；T 不进上下文（只用于回放与挖掘） |
| 巩固 | `--consolidate` | 7 天未使用按周衰减 0.97；`importance < 0.15` 且仅用过 1 次 → `archived`（保留可捞回） |
| 强化 | 每次召回命中 | `use_count+1`、`importance+0.02`——**越用越准**，这是"第二大脑"与"文件柜"的区别 |

检索排序公式（`retrieve.rank`）：

```
final = BM25(q, doc) × (0.6 + 0.4 × importance) + 0.35 × 0.5^(age/30) + 0.15 × min(1, use_count/10)
```

**无词面命中的条目一律不进入召回集**。宁可返回空（暴露知识缺口，会被反思登记为 `recall_miss`），也不用"高重要度但不相关"的记忆污染上下文——噪声召回比召回失败更危险，因为它看起来是"有依据的"。

### 4.3 为什么不用向量库

引入 embedding 会让"可运行"退化为"需先装模型/联网"。本实现对中文采用**相邻二元组 + 停用词过滤 + 独字兜底**的切分，在几十到几千条记忆的量级上召回质量与向量检索差距可忽略，且换来两个工程收益：零依赖、**可解释**（能打印命中词，复盘时能回答"为什么没检索到"）。规模上限与迁移路径写在 `architecture/ARCHITECTURE.md` 的 ADR-4。

### 4.4 一个真实的记忆诞生链

```
几次相同的组合指令（记住 + 记待办，达到 support 阈值 2）
   → T 层留下 3 条相同工具序列的轨迹
   → 挖掘器：support=2 达阈值 → 生成草案 skills/_proposed/auto-memory-remember-memory-open-loop/
   → 人工确认语义、补 triggers/inputs → 上线为 skills/memorize-loop/
   → 此后再出现同样的组合指令，规划器直接走技能（trace 中出现 "进化闭环" 字样）
```

这条链的每一环都有实物：`logs/mining-report.md`（挖掘报告）、`skills/_proposed/*`（草案）、`skills/memorize-loop/`（上线技能）、`memory/t/*.jsonl`（前后对比的轨迹）。

---

## 5. 技能体系（L4）

### 5.1 双文件契约

```
skills/<name>/
├── skill.json   ← 机器读：步骤 / 参数 / 错误策略 / 输出模板（严格校验）
└── SKILL.md     ← 人读：解决什么问题、契约表、设计取舍、已知边界
```

为什么不用 YAML frontmatter：YAML 子集解析器是 bug 温床（缩进、块标量、引号转义）。机器要严格校验的契约用 JSON 零歧义；人和 LLM 读文档用 Markdown。**两者共存，各司其职。**

### 5.2 已上线技能

| 技能 | 触发场景 | 步骤 | 错误策略 | 设计要点 |
| --- | --- | --- | --- | --- |
| `daily-brief` | 简报 / 日报 / 今天要做什么 | 5 | continue | 聚合型任务，单源缺失不该整份失败 |
| `repo-audit` | 巡检 / 审计 / 检查目录 | 2 | continue | 纯只读，可对任意目录反复执行 |
| `capture-note` | 记录一下 / 捕获 / 记一笔 | 3 | abort | 原子双写：K 层 + `workspace/inbox.md` |
| `weekly-review` | 复盘 / 周报 / 回顾 | 7 | continue | 复盘锚在 T 层真实数据，不靠印象 |
| `self-check` | 自检 / 体检 / 系统状态 | 7 | continue | 把"静默腐化"变成一条命令 |
| `memorize-loop` | 记住 + 记待办（组合） | 2 | abort | **由挖掘器发现、人工确认上线** |

### 5.3 新增一个技能（3 步）

```bash
mkdir skills/my-skill
# 1) 写 skill.json：name / description / triggers / inputs / steps / output / on_error
# 2) 写 SKILL.md：这个技能解决什么、契约表、边界
# 3) python agent.py --skills   # 装载 + 契约校验（工具是否存在、id 是否重复、输出是否为空）
```

### 5.4 技能是可组合的

`skill.run` 工具允许技能调用技能，带深度保护（`depth > 3` 中止）。这让"原子技能 → 复合技能"成为可能，而不需要把步骤复制粘贴。

---

## 6. 进化机制（为什么它是"基础设施"而不是"项目"）

三个闭环，每个都有可观测的信号与动作：

| 闭环 | 信号 | 触发 | 动作 | 证据 |
| --- | --- | --- | --- | --- |
| **记忆闭环** | 召回命中 / 未命中 | 每次运行 | 命中即强化；未命中记 `recall_miss` | `memory/k/*.jsonl` 的 `use_count` 递增 |
| **能力闭环** | 相同工具序列重复 ≥2 次 | `--mine` / `self-check` 内置挖掘 | 生成草案 → 人工确认 → 上线 → 下次直接走技能 | `logs/mining-report.md`、`skills/_proposed/`、`skills/memorize-loop/` |
| **契约闭环** | 技能引用了不存在的工具 / 输入缺失 | 每次运行前装载 + 自检 | 契约问题在 `--skills` 与 `self-check` 中显性暴露 | `self-check` 输出的「契约校验」段 |

**为什么挖掘器必须有人工闸门**：自动生成的只是"曾经这样干过"，不等于"应该这样干"。草案里的参数是 `<从轨迹补全>` 占位符——直接 `promote` 会写出垃圾数据（这一点在 `tests/test_smoke.py::t_miner` 里被显式验证为"可上线"而非"可直接用"）。把未确认的行为序列直接固化为能力，等于把偶然固化成制度。

---

## 7. 预算、安全与可审计

### 7.1 三重预算（`src/config.py: Budget`）

| 预算 | 默认 | 命中后的行为 |
| --- | --- | --- |
| `max_steps` | 30 | 终止并保留已得信息收敛输出 |
| `tool_timeout_s` | 20 | 单工具 `subprocess` 超时 → `ToolError` |
| `max_output_chars` | 4000 | 单步输出截断并标注原长 |

### 7.2 安全边界

| 项 | 策略 |
| --- | --- |
| 路径沙箱 | 相对路径一律相对**项目根 C10/** 解析；绝对路径越出项目根一律拒绝（读、写同界，避免"读得到写不进"的割裂） |
| 危险分级 | `danger 0` 只读 / `1` 写 / `2` 执行；`danger≥2` 需显式 `--danger` 授权 |
| 命令白名单 | `shell.run` 首命令必须在白名单内（python / git / ls / grep…），其余拒绝 |
| 记忆写入 | 只经 `KStar` 单一入口，业务代码不得直接读写 `memory/` 下的文件 |

### 7.3 可审计性

每条轨迹固定包含：`run_id / ts / source / task / planner / plan / recall(含分数) / steps(含 args 与 ms) / ok / quality / ms / lesson`。
这使事后能回答三个问题：**它当时想干什么（plan）、依据什么（recall）、实际动了什么（steps）。**

---

## 8. 目录结构

```
D:\C10\
├── AGENT.md                    ← 本文件（评审入口）
├── agent.py                    ← 启动器（24 行，只做路径注入）
├── src\                        ← 内核 2,587 行，零第三方依赖
│   ├── config.py               路径 / 预算 / 安全边界（唯一配置源）
│   ├── core\                   L3 循环层
│   │   ├── loop.py             Agent.run：分发 / 守卫 / 记账
│   │   ├── planner.py          规则规划器 + 可选 LLM 规划器 + 多意图分解
│   │   ├── reflect.py          quality 计算 + 教训结构化
│   │   ├── miner.py            技能挖掘器 + 人工上线闸门
│   │   └── types.py            RunContext / Plan / RunResult
│   ├── interfaces\             L1 接口层（cli.py / http_api.py）
│   ├── tools\                  L2 工具层（base.py 契约 / builtin.py 20 个工具）
│   ├── skills\                 L4 装载与运行时（loader.py / runtime.py）
│   └── memory\                 L5 记忆（kstar.py / retrieve.py）
├── skills\                     ← 技能库：6 个已上线 + _proposed 草案
├── memory\                     ← KSTAR 四层实际数据（k/ s/ t/ a/；t/ 为逐日轨迹）
├── architecture\               ← 架构交付物
│   ├── ARCHITECTURE.md         分层契约 / ADR / 失败模式 / 扩展路径
│   ├── architecture.html       一页可视化（浏览器直接打开）
│   ├── layers\01..05.md        逐层深潜
│   └── schemas\                三个 JSON Schema（kstar / skill / trace）
├── AAR\AAR.md                  ← 复盘交付物
├── AI日志\AI日志.md             ← AI 使用日志
├── tests\test_smoke.py         ← 12 项契约断言（临时目录隔离）
├── logs\                       运行证据：demo-run.txt / test-report.txt / mining-report.md
└── workspace\                  智能体的工作区（inbox.md 等产物）
```

---

## 9. 自检与验证（可复现）

```bash
python tests/test_smoke.py        # 12 passed, 0 failed
python agent.py --demo            # 7 个任务全部 quality=1.0
python agent.py --skills          # 6 个技能，0 个契约问题
python agent.py --stats           # K/S/T/A 四层计数
```

**交付时快照**（2026-11-15 14:20）：

| 指标 | 值 |
| --- | --- |
| 工具数 | 20 |
| 技能数 | 6（+1 个未上线草案作为进化证据） |
| 内核代码 | 2,587 行（`src/`）+ 230 行测试 |
| 累计运行轨迹 | 39 条（`memory/t/2026-11-15.jsonl`） |
| K 层知识 / A 层教训 | 7 条 / 16 条 |
| 测试结果 | 12 / 12 通过 |
| 单次任务平均耗时 | 30–60 ms（无网络工具时） |

测试覆盖的是**契约**而非行数：沙箱越界必须拒绝、危险工具必须网关拦截、同文记忆必须去重、
技能损坏必须隔离、预算必须熔断、进化闭环必须真的改变规划路径。

---

## 10. 设计取舍与已知限制

### 已做的取舍

| 取舍 | 选择 | 理由 | 代价 |
| --- | --- | --- | --- |
| 记忆存储 | JSONL + 线性扫描 | 零依赖、可 diff、可人为查看 | 万条以上需要迁移到 SQLite FTS |
| 规划器 | 规则为主，LLM 可选 | 无 Key 也能跑通全链路 | 离线时语义理解能力有限（复杂任务落到"知识缺口"） |
| 技能格式 | JSON 契约 + MD 文档 | 校验严格、无解析歧义 | 不能用 frontmatter 一文件写完 |
| 写权限 | 项目根为界 | 语义一致（相对路径永远同一基准） | 不能管理项目根以外的文件 |
| 自动挖掘 | 必须人工确认上线 | 防止把偶然固化成制度 | 进化不是零人力 |

### 已知限制（诚实清单）

1. **离线规划器不懂语义**：复杂、隐晦的指令会落到"未匹配技能"的兜底路径，只能靠记忆给出参考，不能自主拆解。配 `C10_LLM_BASE_URL` / `C10_LLM_API_KEY` 可切换 `LLMPlanner`（失败自动降级）。
2. **检索是词面匹配**：同义改写（"记忆分层" vs "分层记忆"）能命中，但跨表述（"归档" vs "冷存储"）会漏。这是不用 embedding 的必然代价。
3. **技能不能写代码**：技能是"声明式编排"，不是"生成程序"。真正的代码生成需要 LLM 规划器 + 代码工具。
4. **单进程无锁**：并发调用 `--serve` 时记忆写入未加锁，适合单用户而非多租户。
5. **A 层会积累近义教训**：已做同文合并，但表述不同、语义相同的教训仍会并存（当前 16 条中有若干近义项）。长期需要"教训聚类"。
6. **挖掘器的签名只认工具名**：参数差异被忽略，可能把"看似相同实则不同"的序列合并。

---

## 11. 评分维度自检映射

| 评分项 | 分值 | 本交付物的对应证据 |
| --- | --- | --- |
| `systemArchitecture` 系统架构 | 25 | 五层清晰分层且每层可独立替换（第 2 节 + `architecture/ARCHITECTURE.md` 的分层契约表与 8 条 ADR）；预算/沙箱/危险分级构成完整运行边界（第 7 节）；`architecture/architecture.html` 一页可视化 |
| `memorySystem` 记忆系统 | 20 | KSTAR 四层定义明确、职责不重叠、写入权限各异（第 4 节）；去重/衰减/归档/强化四类维护策略；三层 JSON Schema（`architecture/schemas/`）；检索公式与"无命中即返回空"的反噪声原则 |
| `artifactCompleteness` 产物完整性 | 15 | 可运行代码（零依赖）+ 6 技能 + 12 项测试 + 演示脚本 + 证据日志；`python agent.py --demo` 一条命令复现全部结论（第 9 节） |
| `aiUsage` AI 使用质量 | 20 | `AI日志/AI日志.md`：阶段化记录、提示词策略、AI 产出的 7 处错误与人工纠正、采纳率统计、逐条可追溯的命令/文件 |
| `reflectionQuality` 复盘质量 | 20 | `AAR/AAR.md`：预期 vs 实际、7 个真实缺陷的"现象→根因→修复→验证"、4 组取舍的对称陈述、量化指标、3 条重做方案、5 条可迁移经验 |

---

## 12. 附录

### 环境变量（全部可选）

| 变量 | 作用 | 默认 |
| --- | --- | --- |
| `C10_ROOT` | 覆盖项目根（测试隔离用） | `D:\C10` |
| `C10_LLM_BASE_URL` | OpenAI 兼容接口地址 | 空（走规则规划器） |
| `C10_LLM_API_KEY` | 接口密钥 | 空 |
| `C10_LLM_MODEL` | 模型名 | `gpt-4o-mini` |

### 扩展路线（按性价比排序）

1. **教训聚类**：把 A 层近义教训合并成"主题教训"，提升复盘信噪比。
2. **向量旁路**：K 层超过 5,000 条时加一层可选 embedding 召回，BM25 作兜底。
3. **定时巩固**：用系统计划任务每日跑 `--consolidate` + `--mine`，把"定期"变成"自动"。
4. **多接口**：把 L1 扩成飞书/企微机器人，验证"换接口零改动下层"的主张。
5. **技能版本迁移**：技能 `version` 字段目前只做展示，可扩展为"步骤变更检测 + 回归提示"。

---

_本文件是系统的一部分，不是系统的说明书：修改架构时同步修改它，否则它会变成下一份"过期文档"。_

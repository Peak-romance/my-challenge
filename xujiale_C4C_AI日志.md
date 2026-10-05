# xujiale_C4C_AI日志

> 项目：作业自动求解与排版（homework-solver）
> 作者：谢嘉乐（xujiale）
> 日期：2026-10-05（末次更新：19:20，补录 Stage5 PDF 编译与本轮攻坚过程）
> 本文档记录两部分：**(A) 运行时 AI 使用日志机制**（代码内置、每次运行自动产生）与 **(B) 开发过程 AI 使用记录**（本项目由 AI 协作开发，如实披露）。

---

## A. 运行时 AI 使用日志（ai_usage_log.jsonl）

### A.1 机制设计

每次流水线运行都会在输出目录产生 `ai_usage_log.jsonl`（JSONL 追加式事件日志），逐事件记录：

- `pipeline.start` / `pipeline.done`：输入文件、是否启用 LLM、题量/解出率/验证数、**PDF 是否产出**、耗时
- `stage1.ingest`：文档格式、节数、字符数
- `stage2.parse`：每题的分类结果（limit/equation/linear_algebra/ode/concept…）
- `stage3.solve`：每题使用的求解器、验证结果（true/false/null）
- `stage4.render` / `stage5.compile`：LaTeX 字节数、PDF 编译成功与否与耗时
- LLM 兜底调用：provider、model、prompt/响应 tokens、耗时、成功/失败原因

日志为**追加式**，同一输出目录多次运行的记录会累积保留，因此天然保留了「修复前 → 修复后」的对照轨迹。

### A.2 运行时 AI 使用实况：**零 LLM 依赖**

核心设计是**确定性优先**：SymPy 符号计算解决一切可计算问题，LLM 仅作最后的兜底。七组运行的真实日志汇总：

| 运行 | 输入 | use_llm | 解出 | PDF | 求解器构成 |
|---|---|---|---|---|---|
| ws3_run | baseline_worksheet3.md | false | 8/8 | ✅ 6 页 | sympy_limit / conceptual_template |
| ws4_run | baseline_worksheet4.md | false | 9/10 | ✅ 6 页 | 同上（AP3 诚实未解） |
| ws4_mock_run | baseline_worksheet4.md | **true**(mock) | 10/10 | ✅ 6 页 | sympy_* + **llm ×1（AP3）** |
| la_run | la_homework.md | false | 10/10 | ✅ 6 页 | sympy_linalg ×10 |
| ode_run | ode_homework.md | false | 6/6 | ✅ 3 页 | sympy_ode ×6 |
| sample_run | sample_homework.md | false | 10/10 | ✅ 5 页 | derivative/integral/limit/equation/linalg/ode 混合 |
| edge_run | edge_cases.md | false | 5/7 | ✅ 3 页 | sympy_limit/integral/ode + 2 诚实失败 |

即：**除 mock 测试外，58 道解出的题全部由确定性符号计算完成，未消耗任何真实 LLM tokens**。这保证了结果可复现、零 API 成本、无幻觉风险。

### A.3 LLM 兜底链路：Mock 模式实测

无 API key 环境下，通过 `LLM_MOCK=1` 对兜底链路做端到端集成测试（`output/ws4_mock_run/`）：

```
{"ts": "2026-10-05 19:07:08", "stage": "pipeline.done", "total": 10, "solved": 10,
 "use_llm": true, "llm": {"provider": "qwen", "model": "qwen-plus",
                          "available": true, "mock": true}}
```

- WS4 中唯一未解的 AP3 自动路由到 `llm` 求解器并成功获得结构化响应 → **兜底路由链路验证通过**
- 关键点：mock 组的 `solved` 从 9/10 升到 10/10，且**未引入任何假阳性**（第 10 题确由 LLM 兜底产出，带「未经独立数值验证」徽标）
- 支持三家国产 LLM（`config.yaml` 或环境变量配置）：
  - 通义千问 Qwen（阿里云百炼，`QWEN_API_KEY`）
  - Kimi（月之暗面 Moonshot，`KIMI_API_KEY`）
  - DeepSeek（`DEEPSEEK_API_KEY`）
- 真实 API 调用时记录 prompt/completion tokens 与耗时到 JSONL，便于用量审计
- 所有调用携带结构化 JSON 输出约束的 SYSTEM_PROMPT，失败自动降级为「诚实未解」，绝不编造

### A.4 Stage5 编译日志（本轮新增）

`stage5.compile` 事件把「是否真的产出了 PDF」写进日志，避免只交 `.tex` 却声称完成：

```json
{"ts": "2026-10-05 19:13:30", "stage": "stage5.compile",
 "level": "info", "success": true, "elapsed_s": 10.96}
{"ts": "2026-10-05 19:13:30", "stage": "pipeline.done",
 "input": "test_cases/la_homework.md", "total": 10, "solved": 10,
 "verified": 10, "pdf": true, "elapsed_s": 11.02}
```

七组运行的 `run_summary.json` 中 `pdf` 字段**全为 true**，与磁盘上的 7 份 `homework.pdf` 一一对应。

### A.5 日志节选：修复前后对照（真实文件）

PartB7 修复前（分类为 calculation，求解失败）：

```json
{"ts": "2026-10-05 14:25:17", "stage": "stage3.solve",
 "solved": "9/10", "solvers": {"PartB7": "none", ...}}
```

修复后（PartB7 归类为 equation，求解+验证通过）：

```json
{"ts": "2026-10-05 14:28:50", "stage": "stage2.parse",
 "types": {"PartB7": "equation", ...}}
```

日志如实保留了迭代轨迹，这正是可追溯性的意义。

---

## B. 开发过程 AI 使用记录（如实披露）

本项目由 AI（WorkBuddy 智能体）与用户协作开发，开发全程的使用方式如下。

### B.1 使用范围与方式

| 阶段 | AI 参与方式 | 人工决策点 |
|---|---|---|
| 方案设计 | 生成「确定性优先 + LLM 兜底」五阶段架构方案 | 用户确认扩展学科（线性代数）与命名规范 |
| 代码实现 | 编写全部 10 个脚本（约 3000 行 Python） | 用户提出保存路径（E:\C4C）与交付要求 |
| 测试数据 | 生成线代/ODE/边界用例题目 | 标准答案由 AI 独立推导并注明推导方法 |
| 调试迭代 | 运行测试 → 读报错 → 定位 → 修复 → 回归 | 用户在关键节点确认方向 |
| **PDF 编译攻坚** | **逆向缓存结构、断点续传、自动补依赖循环、影子编译** | 用户要求「先复盘再定计划再执行」 |
| 文档撰写 | 生成七份交付文档 | 用户明确交付物清单（方案设计/技能包/output/AI日志） |

**交互方式对本轮结果的影响**：用户要求「先复盘产出、再做符合性评判、再定计划、接着执行」，
这个节奏约束很有价值——它迫使先承认「PDF 未产出」这个唯一的真实缺口，并把资源集中在刀刃上，
而不是继续在已达标的求解正确率上堆砌。

### B.2 AI 使用中的关键技术决策（AI 提出并验证）

1. **确定性优先于 LLM**：SymPy 精确解 > LLM 概率性输出，保证 94.4% 基线正确率可复现
2. **验证器独立于求解器**：残差法代回检查而非重算，能抓住求解器自身 bug（实战抓出双侧极限错误）
3. **诚实失败原则**：解析不了/不可逆/无极限时明确报告原因，而非编造答案
4. **拿来主义**：继承 starter kit 已验证的解析核心与概念模板，而非从零重写
5. **（本轮）把环境不可控改造成可诊断**：面对慢网络下的 tectonic bundle 下载，不是反复重试，
   而是先逆向缓存结构、写批量校验脚本定位损坏文件，再写自动补依赖循环解决
6. **（本轮）环境兜底固化进产品而非写进手册**：把「影子目录编译 + 自动找引擎」写进
   `compile_pdf()`，使 `pipeline.py --compile` 在同类受限环境下开箱即用

### B.3 AI 的错误与修正（完整迭代记录）

**（一）求解与设计阶段**

- SymPy 对象 JSON 序列化崩溃 → 增加 `_json_safe` 递归转换
- 矩阵环境只提取第一个 → 改为 `finditer` 全量提取
- 特征值答案渲染成 dict → 改为展开列表
- `sympy.ode` 导入路径错误 → 改为顶层 `from sympy import ode_order`
- ODE 变量代换被 `split_symbols` 拆坏 → 占位符前插显式乘号
- 双侧极限默认按右侧 → 左右分别计算判 DNE
- 振荡极限返回 `AccumulationBounds` → 识别并转写 DNE
- 边界题 ±∞ 被误判验证失败 → `verify_limit` 加发散方向采样
- 验证器编辑事故（吞掉 elif 分支）→ 读文件核实后恢复
- 兜底 simplify 产生假阳性 → 指令词门槛 + 单变量守卫

**（二）LaTeX 排版阶段（本轮，10 项）**

| # | AI 造成的错误 | 修正 |
|---|---|---|
| 1 | 一行含多个行内公式被误套 `\[ \]` → `$$` 未闭合 | `_step_to_latex` 增加「内部不得再含 `$`」判定 |
| 2 | `\boxed{displaystyle ...}` 漏反斜杠 | 改为 `\displaystyle` |
| 3 | 汇总表 `\checkmark` 未进数学模式、`sympy_linalg` 的 `_` 未转义 | 加 `$…$`；表字段走 `escape_latex` |
| 4 | 答案自带 `$…$` 又套 `\boxed{}` → `$` 嵌套 | 新增 `answer_display/answer_inline` 自适应排版 |
| 5 | `\noindent` 与后续文本粘连成 `\noindentIf` | 插入 `\relax` |
| 6 | 题面 `[:120]` 截断切出奇数个 `$` → `\$\varepsilon` | 新增 `safe_truncate`：配平 `$` 并裁掉不完整命令 |
| 7 | 概念题模板 f-string 的 `$` 拼接写错 | 修正 `solve.py` |
| 8 | en 模板下中文页眉缺字形 | CJK 安全网纳入 course/student/title |
| 9 | λ 等数学 Unicode 在正文缺字形 | `MATH_UNICODE` 映射包成行内数学 |
| 10 | `steps`/`answer` 为 `None` 时崩溃 | `.get(k, [])` 统一改为 `.get(k) or []` |

**其中值得单独记的一条教训**：第 4 项的修复一度引入回归（6/7 成功跌到 2/7）——
因为「自然语言 vs 数学」的判据写得太糙，把 `C_{1} e^{3x}` 误判成了文本。
这说明**改渲染层必须同时盯住编译成功率这条回归线**，不能只看单点修好了没有。

**（三）PDF 编译攻坚阶段**

| # | 错误 / 误判 | 修正 |
|---|---|---|
| 1 | 凭记忆填 tar 偏移，错了 3 个（t1enc/ts1enc/loadhyph-hsb） | 写脚本按 13.5 万条索引**批量校验长度**，一次性揪出 |
| 2 | 误以为文件没问题，反复猜测 → 浪费大量时间 | 先建校验手段再重试 |
| 3 | 未发现 format 比 manifest 新时不重扫缓存 | 删 `.fmt` 强制重建文件列表 |
| 4 | 单线程逐个下载导致每次迭代 5 分钟 | 批量下载 + 自动补依赖循环（单文件 ~1 秒） |
| 5 | `TEXINPUTS` 对 tectonic 无效（已写进代码才发现） | 改为**影子目录编译**（tectonic 会搜索工作目录） |
| 6 | `compile_pdf` 未导入 `os` → `NameError` | 补 import |

### B.4 诚实性声明

- 所有正确率数据（17/18 基线、10/10、6/6、5/7）来自真实运行，无任何手工修饰
- **7/7 产出 PDF**，`run_summary.json` 的 `pdf` 字段与磁盘文件一一对应，可复现核对
- 标准答案（线代/ODE 共 16 题）由 AI 独立推导，推导方法已在 groundtruth 文件中注明
- 运行日志（`ai_usage_log.jsonl`，共 8 个文件 270 条事件）与各阶段 JSON 产物完整保留
- **LLM 兜底仅完成 mock 集成测试，真实 API 调用未实测（无 key），已如实标注**；
  这是本项目当前唯一未端到端验证的链路
- 开发环境无 TeX 发行版且网络受限（5–10 KB/s），PDF 通过离线宏包库
  （`E:\C4C\.texbuild\`）编译产出，路径与原理已在 README 与完成计划文档中说明，可复现

### B.5 收尾轮：技能包文档沉淀（AI 协作）

把攻坚过程中积累的**隐性知识**固化为可交付文档，避免"只有当时的我才知道"：

| 新增文件（均在 `homework-solver\` 根目录） | 内容来源 | 作用 |
|---|---|---|
| `USAGE.md` | 补齐参数、输出、场景、退出码 | 他人不看源码也能跑通 |
| `EXTENDING.md` | B.3 的四步注册流程 + 兜底链教训 | 别人能加新学科 |
| `TROUBLESHOOTING.md` | 本次全部报错的分类归纳 | 症状→解法，含三行自查命令 |
| `sympy_recipes.md` | solve.py / verify.py 的真实调用 | 写求解器时的速查手册 |
| `latex_pitfalls.md` | 13 条真实踩过的坑 | **改排版前必读**，防复发 |
| `offline_tex.md` | 缓存结构逆向 + HTTP Range + 影子目录 | 受限网络下也能出 PDF |

同时订正 `SKILL.md` 中过时的 `fontset=fandol` 描述（实际已改为 `fontset=windows`）。

### B.6 收尾轮②：目录扁平化（响应用户"我找不到"）

用户反馈：**交付物层级太深，找不到东西**。据此做了两处扁平化：

| 改动 | 前 | 后 |
|---|---|---|
| 技能包文档 | `homework-solver/docs/*.md`、`references/*.md` | **上提到 `homework-solver\` 根目录**，不再套子文件夹 |
| output 成品 PDF | `output/<组>_run/homework.pdf`（7 个同名文件藏在 7 个文件夹里） | **上提到 `output\` 顶层**，按内容重命名 `xujiale_C4C_output_<作业>解答.pdf` |
| output 说明书 | 无 | 新增 `output\xujiale_C4C_output说明.md`（成品清单 + PDF↔过程目录映射 + 重跑命令） |

保留的部分与理由：`scripts/`、`test_cases/`、`examples/` 是**代码与数据**，
天然需要分组，无法扁平；各 `*_run/` 目录保留 Stage1–3 的中间 JSON、
`homework.tex` 与 `ai_usage_log.jsonl`，这是**可追溯性证据**，不能丢，
成品 PDF 已上提一层让用户无需翻找。

**回归验证**（改动后立即执行）：`la_homework.md` 用 `--no-llm --compile` 重跑，
结果 **10/10 解出、10/10 验证通过、PDF 55,066 B 产出**，与改动前一致 —— 文档改动零影响。

---

## 附：四项指定交付物索引

| 交付物 | 位置 | 内容 |
|---|---|---|
| **方案设计** | `E:\C4C\xujiale_C4C_方案设计.md` | 五阶段流水线架构、确定性优先原则、模块职责、边界策略 |
| **homework-solver** | `E:\C4C\homework-solver\` | 技能包：10 脚本 + 7 测试集；根目录另有 SKILL/README + 6 份手册与速查表 |
| **output** | `E:\C4C\output\` | **顶层即 7 份成品 PDF**（`xujiale_C4C_output_*.pdf`）+ `xujiale_C4C_output说明.md`；各组过程产物在 `*_run/` |
| **AI日志** | `E:\C4C\xujiale_C4C_AI日志.md`（本文件） | 运行时日志机制 + 开发过程 AI 使用实况 |

补充文档（`E:\C4C\交付文档\`）：拿来说明、教学说明、验证报告、AAR复盘、完成计划与自评。

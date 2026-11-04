# C8 AI 使用日志（AI Usage Log）

> 交付物位置：`D:\C8\AI日志\AI日志.md`
> 说明：本项目使用 **WorkBuddy（AI 助手）** 作为唯一 AI 工具完成全部分析、诊断、执行与文档撰写。本日志记录每一阶段"用 AI 做了什么、怎么用、产出如何被人工/客观校验"，确保 AI 使用**恰当、有效、可追溯**。

---

## 使用总览

| 维度 | 情况 |
| --- | --- |
| AI 工具 | WorkBuddy（对话式 AI + 工具调用：Bash / Read / Edit / AskUserQuestion / 后台任务） |
| 用途 | 代码勘察、环境诊断、依赖安装、测试执行、证据抓取、四份交付物撰写 |
| 是否替代人决策 | 否。所有修复（版本升降、改哪个文件）均由 AI 提出方案，经"客观测试"验证后才采纳 |
| 可追溯性 | 每步均有命令、文件路径、测试输出落盘（见 `拿来说明/`） |

---

## 阶段化日志

### [T0] 需求澄清（22:48）
- **AI 动作**：用 `AskUserQuestion` 向用户确认两件事——真实项目来源、是否先建骨架。
- **提示词策略**：把"真实需求必须来自用户"作为硬约束，给出 3 个选项（用户提供 / AI 设计 / 基于 D 盘已有文件）。
- **用户决策**：选"**D 盘闲置平台代码**" + "**现在就建好骨架**"。
- **产出**：创建 `D:\C8\{proposal, AAR_W, AI日志, 拿来说明\}` 四目录。
- **校验**：目录创建成功（`ls` 确认）。

### [T1] 代码勘察（22:52）
- **AI 动作**：读取 `README.md`、`docker-compose.yml`，并用 `ls -R` 探查 `backend/frontend/database/tools` 结构。
- **提示词策略**：先读最高层文档与编排文件，再下钻到目录树，建立"这是什么项目"的整体认知。
- **关键判断**：判定这是"公共资产闲置平台"全栈应用，README 声称 91 断言全过；真实问题 = **让它在本机真实跑通**。
- **校验**：结构与 README 描述一致，无矛盾。

### [T2] 环境核查（22:55）
- **AI 动作**：执行探测命令：`python --version` / `pip --version` / `node --version` / `docker`（缺失）/ 依赖探测。
- **提示词策略**：把"能不能跑"拆成"解释器 / 包管理器 / 容器 / 依赖"四个独立信号分别取证。
- **发现**：无 Docker；后端依赖（fastapi/uvicorn/pydantic…）全部未装；只有 sqlite3 是标准库。
- **校验**：探测输出明确，结论可靠。

### [T3] 依赖安装 · 第 1 次失败（23:0x）
- **AI 动作**：`pip install -r backend/requirements.txt`。
- **结果**：失败。`ERROR: No matching distribution found for pydantic-core==2.27.2`。
- **根因（AI 推断）**：`pydantic==2.10.4` 锁定 `pydantic-core==2.27.2`，该版本无 Python 3.13（cp313）轮子。
- **校验**：错误信息直接支撑推断，无需二次猜测。

### [T4] 依赖安装 · 第 2–3 次失败（23:0x）
- **AI 动作**：放宽 pydantic 版本后重试；改用 `nohup ... &` 后台运行。
- **结果**：一次空输出被 SIGTERM（nohup 被任务框架误杀），一次镜像源返回截断 JSON（`JSONDecodeError: Unterminated string`）。
- **AI 反思**：卡死源于镜像对大依赖树不稳定 + `uvicorn[standard]` 放大依赖树 + `&` 误杀。

### [T5] 双 Python 诊断（23:1x）★关键转折
- **AI 动作**：执行 `which python` / `which pip` / `pip show pydantic` / `python -m pip show pydantic`。
- **发现**：`python` → WorkBuddy 管理的 `3.13.12`；裸 `pip` → 另一处 `3.13.14`。两者**不是同一解释器**，所以裸 `pip install` 的包装不进 `python`。
- **修复策略**：全程改用 `python -m pip install`。
- **校验**：`pip show pydantic`（3.13.14 有）vs `python -m pip show pydantic`（3.13.12 无）形成铁证。

### [T6] 依赖安装 · 成功（23:1x）
- **AI 动作**：`python -m pip install fastapi==0.115.6 uvicorn==0.34.0 SQLAlchemy==2.0.36 "pydantic==2.11.9" ...`
- **结果**：`Successfully installed ... pydantic-2.11.9 pydantic-core-2.33.2 ...`。
- **校验**：`python -c "import fastapi,uvicorn,sqlalchemy,pydantic,..."` → `ALL IMPORT OK, pydantic 2.11.9`。

### [T7] 端到端冒烟测试（23:2x）
- **AI 动作**：`python tools/smoke_test.py`（后台 + 日志 `D:\C8\smoke.log`）。
- **结果**：**通过 91，失败 0**（登录→发布→浏览→搜索→认领扣减→归零下架→流转→交接单→我的记录→管理员五模块→统计→权限→导出鉴权→docx/pdf 导出→修正→撤销认领→跨部门发布→部门启用规则）。
- **校验**：日志原文落盘（`拿来说明/smoke_test_result.txt`）。

### [T8] 前端静态校验（23:2x）
- **AI 动作**：`python tools/check_dom_refs.py` + `node tools/check_js.js`。
- **结果**：DOM/API 引用一致性通过；14/14 JS 块语法通过。
- **校验**：输出落盘（`拿来说明/frontend_checks.txt`）。

### [T9] 真实运行证据抓取（23:2x）
- **AI 动作**：编写脚本——启动后端（8011 端口，独立 DB）→ 轮询 `/api/health` → curl 登录/学院/物资/统计/日志 → 导出 `handover.docx`/`handover.pdf` → 落盘到 `拿来说明/live/evidence/`。
- **结果**：后端 2 秒就绪；生成 `health.json / colleges.json / assets.json / stats.json / logs_claim.json`，以及真实文件 `handover.docx`（PK 头，37 KB）、`handover.pdf`（%PDF 头，79 KB）。
- **校验**：`head -c 8` 显示 `PK` / `%PDF-`，证明是真实有效文件而非空壳。

### [T10] 根因修复（23:2x）
- **AI 动作**：先 `cp requirements.txt requirements.txt.bak`（备份），再 `Edit` 将 `pydantic==2.10.4` 改为 `pydantic==2.11.9  # 兼容 Python 3.13...`。
- **策略**：最小改动、可回滚（保留 `.bak`）、行内注释写清原因，使后续 `pip install -r` 在 3.13 可直接成功。
- **校验**：编辑成功；逻辑上消除了 T3 的失败根因。

### [T11] 交付物撰写（23:3x）
- **AI 动作**：撰写 `proposal.md` / `AAR_W.md` / `AI日志.md`（本文件）/ `拿来说明/README.md`。
- **策略**：proposal 定义需求与可量化验收；AAR 做深度复盘（见其内容）；日志强调可追溯。
- **校验**：四份交付物均落盘，目录结构符合要求。

---

## AI 使用评价（自我复盘）

- **恰当性**：AI 承担了"环境侦探 + 测试执行 + 文档生成"，未替代用户做业务决策；需求来源由用户拍板。
- **有效性**：5 次安装尝试中，前 4 次失败均由 AI 从报错中定位根因并迭代，最终全绿——AI 在"从失败到修复"的闭环中价值最大。
- **可追溯性**：每个阶段都有命令、文件路径、测试输出；关键证据（smoke.log、导出文件、静态检查）全部落盘于 `拿来说明/`。
- **改进点**：若在第 1 步就让 AI 执行"环境对齐检查"（解释器/包管理器同源 + 目标标签轮子存在性），可省去 T3–T5 约两轮返工。这已写入 AAR §6 改进方案 1。

---

## 关键产物索引（均在 D:\C8\）

| 产物 | 路径 |
| --- | --- |
| 提案 | `proposal/proposal.md` |
| 复盘 | `AAR_W/AAR_W.md` |
| AI 日志 | `AI日志/AI日志.md` |
| 冒烟测试输出 | `拿来说明/smoke_test_result.txt` |
| 前端静态检查 | `拿来说明/frontend_checks.txt` |
| 真实 API/导出证据 | `拿来说明/live/evidence/*`（json + docx + pdf） |
| 根因修复备份 | `D:\闲置平台代码\backend\requirements.txt.bak` |

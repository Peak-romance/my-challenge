# AI 使用日志（AI Usage Log）

> 记录本次 C6 挑战中 **WorkBuddy（AI 助手）** 的参与方式、关键决策与可追溯操作链路，证明 AI 的运用是**恰当、有效、可追溯**的，而非“黑箱代写”。

## 一、总体协作模式

| 维度 | 说明 |
| --- | --- |
| 角色 | 用户定方向（C6 挑战、交付物落 D:/C6、采用 D 盘现有「公共资产闲置平台」代码）；AI 负责方案落地、环境搭建、问题诊断、发布与文档生成 |
| 工作模式 | Agent 模式（AI 直接执行：写文件、跑命令、诊断、发布），关键分叉点用 AskUserQuestion 对齐 |
| 主要工具 | AskUserQuestion（方向确认）、Write/Edit（写代码与文档）、Bash（环境校验/安装/启动/测试）、TaskCreate/Update（进度追踪）、workbuddy_sites_deploy（发布）、gh/git（仓库） |

## 二、关键决策链路（可追溯）

### 1. 产品取向确认（AskUserQuestion）
- **触发**：D:/C6 已存在一个 Next.js「聚光 Lumen」旧交付物，而用户指明“代码在 D 盘闲置平台代码里面”，二者取向冲突。
- **AI 动作**：提出单一决定性问题——「C6 以哪个产品作为最终交付物」。
- **用户决策**：**闲置平台（公共资产闲置平台）**，交付物放入 D:/C6，旧 C6 文件先备份不删除。
- **价值**：避免把精力投错产品；直接对齐 `artifactCompleteness` 与 `productQuality`。

### 2. 运行环境校验（客观事实先行）
- **AI 动作**：`node -v / python -V / docker -v / git --version` 实测。
- **结论**：Node v22.22.2、Python 3.13.14、git 2.55.0 可用；**Docker 未安装**。
- **决策**：放弃 docker-compose 路径，采用**免 Docker 的 Python 虚拟环境 + serve.py** 方式，确保本机与发布环境都能跑。

### 3. 依赖安装诊断与修复（体现 AI 有效性）
- **问题**：首用清华镜像 `pip install -r backend/requirements.txt` 报 `Could not find a version that satisfies the requirement fastapi==0.115.6 (from versions: none)`——镜像节点异常/不可达。
- **诊断过程**：先确认官方 PyPI 可达（`pip install fastapi==0.115.6` 从 pypi.org 秒过），判定是**镜像源故障而非依赖本身问题**。
- **修复**：改用官方源 `pip install -i https://pypi.org/simple ...`，43 秒装完，全部导入正常。
- **价值**：没有在“镜像失败”上盲目重试或降级方案，靠一次可达性探测定位根因。

### 4. 种子数据库污染诊断与修复
- **现象**：启动后发现多出一条 `asset_no="2"/床` 资产与一条额外认领记录，与 README 描述的规范种子（4 条物资 + 1 条认领）不符。
- **根因**：`database/data/app.db` 是 **10/19 遗留的手动测试数据**（含 `JJ202610190002` 等），`main.py` 仅在用户表为空时注入种子，故未触发重注。
- **修复**：停止后端 → 删除 `database/data/app.db` 与 `uploads/` → 重启后端 → 自动注入规范种子（验证：4 资产 / 3 上架 + 1 下架 / 1 认领 / 交接单 `JJ202611040001`）。
- **价值**：保证 demo 与文档、仓库完全一致、可复现，避免交付物出现“来历不明”的脏数据。

### 5. 发布适配：单端口编排器 `serve.py`
- **约束**：发布沙箱只暴露**单一 `$PORT`** 且需绑定 `0.0.0.0`；原 `dev_server.py` 硬编码 `127.0.0.1:3000` 且前后端是两个独立进程，无法直接发布。
- **AI 动作**：编写 `serve.py`——对外仅一个端口，内部在回环 8000 拉起 FastAPI（`subprocess` + `PYTHONPATH=backend`），并在同一端口托管前端静态页、把 `/api`、`/uploads` 反向代理到后端。
- **验证**：本地以 `PORT=3000` 启动，`/api/health`、登录、资产列表、前端 `index.html` 全部 200，确认单端口形态可用后再发布。

### 6. 发布与仓库（交付 app 链接 / repo 链接）
- **发布**：`workbuddy_sites_deploy`（directory=`D:/闲置平台代码`，language=python，`startCmd=python serve.py`）→ **发布成功，`verified:true`**。
- **外网复验**：`/api/health` 返回 `ok`、登录返回真实 JWT、`user1/孙悦/智能制造学院·实训中心` 信息正确。
- **仓库**：`git init -b main` → 提交干净源码（`.gitignore` 已排除 `.venv`、`database/data`、`.env`、`logs`）→ `gh repo create c6-idle-asset-platform --public --source . --push`（账号 Peak-romance，已登录）→ 推送成功。

## 三、操作时间线（摘要）

| 阶段 | 动作 | 产出 |
| --- | --- | --- |
| T0 | 环境校验 | Node/Python/git 可用；Docker 缺失 |
| T1 | 方向确认 | AskUserQuestion → 锁定“闲置平台”为产品 |
| T2 | 依赖安装 | 清华镜像失败 → 切官方 PyPI，43s 装完 |
| T3 | 启动验证 | 后端 8000 + 前端 3000 起；发现种子库污染 |
| T4 | 数据修复 | 重置为规范种子（4 资产 / 1 认领） |
| T5 | 功能验证 | `tools/smoke_test.py` → **91/91 断言通过** |
| T6 | 发布适配 | 编写 `serve.py`（单端口编排）并本地验证 |
| T7 | 发布 | `workbuddy_sites_deploy` 成功，`verified:true` |
| T8 | 仓库 | git 初始化 + gh 创建并推送公开仓库 |
| T9 | 交付物 | D:/C6 下生成 README/AI日志/复盘AAR/demo/LINKS + 可运行源码副本 `app/`；旧 C6 备份至 `_archive_lumen` |

## 四、AI 使用的“恰当性”自评

- **恰当**：方向确认、环境诊断、单端口编排、发布与推送由 AI 承担；用户保留产品取向与最终验收权。
- **有效**：镜像故障一次探测定位、种子污染一次诊断重置、发布适配一次成型，没有在无效路径上空转。
- **可追溯**：本日志 + Git 提交历史 + README（含 app/repo 链接）+ 冒烟测试共同构成完整证据链。
- **可改进**：首装应直接用官方源或国内可用镜像并先探活，可省去一次镜像失败；见 `复盘AAR.md`。

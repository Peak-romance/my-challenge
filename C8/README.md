# C8 · Real-World Project Execution（真实项目落地）

> C1–C7 是在证明你"会"，C8 是在证明你"能做成"。
> 本目录（仓库内 `C8/`）是本次挑战的完整交付物集合。

## 挑战目标
- 明确真实需求与验收标准
- 在真实约束下完成交付
- 建立交付-反馈-迭代闭环
- 复盘真实项目与练习的差异

## 交付物（四份）
| 交付物 | 位置 | 说明 |
|--------|------|------|
| **proposal** | [`proposal/proposal.md`](proposal/proposal.md) | 真实需求、范围、真实约束、可量化验收标准（AC1–AC7）、交付-反馈-迭代闭环 |
| **AAR_W** | [`AAR_W/AAR_W.md`](AAR_W/AAR_W.md) | 事后复盘：预期 vs 实际、真实约束差异、问题解决深度、与练习的具体差异、可落地改进方案 |
| **AI日志** | [`AI日志/AI日志.md`](AI日志/AI日志.md) | 全阶段 AI 工具使用可追溯记录（提示词策略、决策、人工/客观校验、产物索引） |
| **拿来说明** | [`拿来说明/README.md`](拿来说明/README.md) | 物证包说明 + 独立复现步骤 |

## 真实项目对象
把 D 盘上"闲置"的全栈应用 **「公共资产闲置平台」**（FastAPI + SQLite 后端 / 原生 HTML+Tailwind 前端 / docker 编排）作为真实项目，在真实约束下让它真正跑通并达到文档声称的可验收状态，并产出可独立复现的证据链。

## 客观验收证据（详见 `拿来说明/`）
- 端到端冒烟测试：**91 / 91 断言通过，0 失败**（`拿来说明/smoke_test_result.txt`）
- 前端 DOM/API 静态一致性：通过；JS 语法块 **14 / 14 通过**（`拿来说明/frontend_checks.txt`）
- 真实启动后端导出：`/api/health = 200`，导出真实 `handover.docx`（37 KB）、`handover.pdf`（79 KB）（`拿来说明/live/evidence/`）
- 真实 API 响应物证：`health.json` / `colleges.json` / `assets.json` / `stats.json` / `logs_claim.json`

## 暴露的真实约束（文档未写）
1. **版本锁 × 运行时不兼容**：原 `requirements.txt` 锁 `pydantic==2.10.4`，其 `pydantic-core==2.27.2` 在 Python 3.13 无对应轮子 → 已修复为 `2.11.9`（原文件备份为 `.bak`）。
2. **双 Python 解释器错位**：`python` 与裸 `pip` 指向不同解释器 → 统一用 `python -m pip` 安装。
3. 镜像源对大依赖树偶发卡死/截断 → 分批/重试安装。

## 如何独立复现
详见 [`拿来说明/README.md`](拿来说明/README.md)，核心步骤：
```bash
cd <项目>/backend
python -m pip install -r requirements.txt        # 已修正 pydantic 锁版本
DATABASE_PATH=app.db python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
python ../tools/smoke_test.py                      # 期望 91/91 通过
```

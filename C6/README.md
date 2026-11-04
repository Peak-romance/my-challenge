# C6 Web Application 挑战 · 交付物总览

> 本目录为 **C6 Web Application** 挑战的交付物包。产品为**真实可运行**的全栈 Web 应用「公共资产闲置平台」，不是 demo。

## 一、四项交付物（按挑战要求）

| 交付项 | 内容 | 位置 / 链接 |
| --- | --- | --- |
| **app 链接** | 已发布上线的在线应用 | https://idle-asset-platform.app.workbuddy.host/?sharecode=SLUWH4EXLI |
| **demo** | 在线可体验的演示 + 演示指引文档 | 应用链接即 demo；演示脚本见 [`demo.md`](./demo.md) |
| **repo 链接** | GitHub 仓库（完整源码、可独立运行） | https://github.com/Peak-romance/c6-idle-asset-platform |
| **AI 日志** | AI 协作与决策追溯 | [`AI日志.md`](./AI日志.md) |

> 配套：**复盘 AAR** 见 [`复盘AAR.md`](./复盘AAR.md)；本包内还含一份**可独立运行的源码副本** `app/`（与仓库一致，开箱即跑）。

## 二、产品简介：公共资产闲置平台

部门用户在平台上以「发布者 + 领取者」双重身份发布与认领真实闲置资产；管理员在后台管组织架构、核验图片、留痕与统计；平台作为共享池集中展示与流转。

**技术栈**：FastAPI + SQLite（后端）／ 原生 HTML + Tailwind CDN（前端，无构建）／ 图片本地存储 ／ JWT 登录 ／ `serve.py` 单端口编排（便于发布与云托管）。

**核心能力**
- 部门用户：登录、学院/部门两级联动发布物资（多图上传 + 真实性校验 + 水印）、浏览与多维搜索、认领（数量自动扣减、归零自动下架）、交接单（服务端真实导出 Word/PDF）、我的记录。
- 平台管理员：组织机构（学院/部门）管理、用户与工号管理、物资管理（修正异常/强制下架/图片核验驳回/撤销认领）、日志中心（只可查看与导出，不可删除）、统计报表。
- 公共共享池：全部上架物资集中展示、搜索、数量流转、流转记录公开。

**质量证据**：端到端冒烟测试 **91 / 91 项断言通过**（`tools/smoke_test.py`，可复现）；图片真实性校验（文件头/可解码/内容指纹查重/分辨率体积门槛）；交接单服务端导出 `python-docx` + `reportlab`。

## 三、本地运行（可独立使用）

本包内 `app/` 为完整源码副本，按以下任一方式运行：

```bash
# 方式一：免 Docker 一键脚本（推荐本机验收）
cd app
python -m venv .venv && .venv/Scripts/python.exe -m pip install -r backend/requirements.txt
# Windows 双击 start.bat；或 Linux/macOS 执行 ./start.sh
# 前端 http://localhost:3000  后端 http://localhost:8000/docs

# 方式二：单端口 serve.py（适合发布 / 云托管，对外仅一个端口）
cd app
pip install -r backend/requirements.txt
python serve.py        # http://localhost:3000
```

演示账号（口令均为 `123456`）：

| 账号 | 角色 | 所属组织 |
| --- | --- | --- |
| `user1` | 部门用户 | 智能制造学院 / 实训中心（工号 20156） |
| `user2` | 部门用户 | 信息技术学院 / 网络运维部（工号 30208） |
| `admin1` | 平台管理员 | 不参与发布与认领 |

## 四、与评分标准的对应关系

| 评分标准 | 权重 | 本交付物如何满足 |
| --- | --- | --- |
| **productQuality** 产品完成度 | 25 | 功能闭环（发布→浏览→搜索→认领→交接单→记录→管理→统计），角色完整，体验一致；91 项端到端断言覆盖 |
| **technicalExecution** 技术实现 | 20 | 合理分层（路由/模型/鉴权/导出/图片工具分离）；真实关系型数据库 + 事务；单端口编排适配发布；种子数据可复现 |
| **artifactCompleteness** 产物完整性 | 15 | 四项交付物齐全；在线 app 可访问；仓库可独立 clone 运行；本包含可运行源码副本；演示账号与脚本齐备 |
| **aiUsage** AI 使用质量 | 20 | 见 [`AI日志.md`](./AI日志.md)：方向确认、关键诊断（镜像源失败→切官方源、种子库污染→重置）、发布与推送均可追溯 |
| **reflectionQuality** 复盘质量 | 20 | 见 [`复盘AAR.md`](./复盘AAR.md)：目标→结果→差异根因→洞察→改进方案，含可复用 Playbook |

## 五、目录说明

```
D:/C6/
├── README.md        # 本文件：交付物总览与评分映射
├── AI日志.md        # AI 协作与决策追溯（对应 aiUsage）
├── 复盘AAR.md       # After-Action Review（对应 reflectionQuality）
├── demo.md          # 演示脚本与验收要点
├── LINKS.md         # 四项交付物链接汇总
├── app/             # 可独立运行的完整产品源码副本（= GitHub 仓库）
└── _archive_lumen/  # 本目录历史遗留内容（聚光 Lumen）备份，未删除
```

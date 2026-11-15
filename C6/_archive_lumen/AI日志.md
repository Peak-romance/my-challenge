# AI 使用日志（AI Usage Log）

> 记录本次 C6 挑战中 WorkBuddy（AI 助手）的参与方式、关键决策与可追溯的操作链路。
> 目标：证明 AI 工具的运用是**恰当、有效、可追溯**的，而非“黑箱代写”。

---

## 一、总体协作模式

| 维度 | 说明 |
| --- | --- |
| 角色 | 我（用户）定方向，AI 负责方案落地、代码实现、问题诊断与文档生成 |
| 工作模式 | Agent 模式（AI 直接执行、写文件、跑命令），配合阶段性规划 |
| 主要工具 | AskUserQuestion（确认方向）、Write/Edit（写代码）、Bash（环境校验与安装）、TaskCreate/Update（进度追踪）、show（结构沟通） |

## 二、关键决策链路（可追溯）

### 1. 需求澄清（AskUserQuestion）
- **触发**：挑战只给了“构建真实可运行产品”，方向不明。
- **AI 动作**：提出 4 个决定性问题（产品方向 / 技术栈 / 部署方式 / 仓库策略）。
- **用户决策**：内容社区平台 · Next.js 全栈 · WorkBuddy 发布 · 本地 git 后推送。
- **价值**：避免做出方向错误的成品，直接对齐评分标准（productQuality / artifactCompleteness）。

### 2. 技术选型决策（node:sqlite 而非 Prisma）
- **问题**：默认 npm registry 延迟 ~10s/请求，且发布环境需保证“可独立运行”。
- **AI 分析**：Prisma 需下载查询引擎二进制、better-sqlite3 需原生编译，在受限网络/只读文件系统下有失败风险。
- **决策**：采用 Node 22 内置 `node:sqlite`（真实关系型库，零依赖、零编译）。
- **验证动作**：`node -e` 实测 `DatabaseSync` 可用后落子。
- **文件**：`src/lib/db.ts`、`src/lib/schema.sql`。

### 3. 架构落地
- 数据层：`schema.sql`（DDL 单一事实来源）+ `db.ts`（单例连接、WAL、外键级联）+ `models.ts`（仓储层）。
- 认证：`auth.ts`（scrypt 哈希 + jose JWT + httpOnly Cookie）。
- 表现层：Server Components 直读 DB（SSR 信息流），REST API 处理写操作，客户端组件负责点赞/收藏/评论/关注等交互。
- 共生成：11 个 API 路由、14 个组件、13 个页面、1 个种子脚本、2 份交付文档。

### 4. 问题诊断与修复（体现 AI 有效性）
| 问题 | 诊断过程 | 修复 |
| --- | --- | --- |
| `npm install` 21 分钟无产物 | Bash 检查 `node_modules` 为空 → 判定卡在依赖解析（高延迟） | 切换 `registry.npmmirror.com`（2.5s vs 12s），安装重启 |
| `settings/route.ts` 导入错误 | 把 `publicUser` 误从 `@/lib/auth` 导入 | Edit 修正为从 `@/lib/models` 导入 |
| 组件误引 `node:sqlite` 风险 | `timeAgo` 放在 `db.ts` 中，组件引用会拖入原生模块 | 抽到独立 `format.ts`，组件只引纯函数 |

## 三、操作时间线（摘要）

| 阶段 | 动作 | 产出 |
| --- | --- | --- |
| T0 | 环境校验 | 确认 Node v22.22.2 / npm 10.9.7 / D 盘可写 / node:sqlite 可用 |
| T1 | 脚手架 | package.json、tsconfig、next.config、tailwind、postcss、globals.css |
| T2 | 数据层 | schema.sql、db.ts、types.ts、auth.ts、models.ts |
| T3 | API 层 | auth / posts / comments / likes / bookmarks / follows / settings 共 11 路由 |
| T4 | 组件层 | 14 个组件（含 8 个客户端交互组件） |
| T5 | 页面层 | 13 个页面（信息流、详情、编辑、主页、登录注册、搜索、收藏、设置、404） |
| T6 | 数据 & 文档 | seed.mjs（演示数据）、README.md、AI日志.md、复盘AAR.md |
| T7 | 验证 & 交付 | 本地 build/seed/run → git init → 发布应用 → 汇总至 D:/C6 |

## 四、AI 使用的“恰当性”自评

- **恰当**：方向确认、技术权衡、样板代码、问题诊断由 AI 承担，用户保留关键决策权。
- **有效**：把“可能卡死安装”的隐患在 21 分钟时诊断并换源解决，避免空转。
- **可追溯**：本日志 + Git 提交历史 + README 共同构成完整证据链。
- **可改进**：早期若直接默认使用国内镜像可省去 21 分钟；见复盘 AAR。

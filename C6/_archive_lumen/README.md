# 聚光 Lumen · 技术内容社区

> C6 Web Application Challenge 交付物 —— 一个**真实可运行**的全栈内容社区，不是 demo。

聚光 Lumen 是一个技术内容社区：用户可以注册登录、发布 Markdown 文章、浏览信息流、点赞、收藏、评论、关注作者，并通过标签与搜索发现内容。

## 技术栈

| 层级 | 选型 | 说明 |
| --- | --- | --- |
| 框架 | **Next.js 14 (App Router)** + TypeScript | Server Components 直读数据，REST API 处理写操作 |
| 数据库 | **node:sqlite**（Node 22 内置） | 真实关系型数据库，**零额外依赖、零原生编译** |
| 认证 | Node `crypto.scrypt` + `jose` JWT | 密码加盐哈希，会话存于 httpOnly Cookie |
| 样式 | Tailwind CSS | 响应式、组件化的轻量 UI |
| 内容 | react-markdown + remark-gfm | 用户文章支持 Markdown 渲染 |

### 为什么用 node:sqlite
在「可独立运行、可部署、可评分」的约束下，node:sqlite 提供了真实 SQL 能力（外键、事务、索引、级联删除），同时避免了 SQLite 原生绑定或 Prisma 引擎下载在网络受限环境下的安装风险，最大化**产物完整性**与**可运行性**。

## 功能清单

- 用户系统：注册 / 登录 / 登出 / 个人资料编辑（昵称、简介、头像色）
- 内容创作：发布 / 编辑 / 删除 Markdown 文章（标题、摘要、封面 Emoji、标签）
- 内容消费：首页信息流（最新 / 热门 / 关注）、文章详情、Markdown 渲染、阅读量
- 互动：点赞、收藏、评论（含删除）、关注 / 取关作者
- 发现：全文搜索、标签筛选、相关文章推荐、个人主页

## 本地运行

```bash
# 1. 安装依赖（需 Node >= 22.5）
npm install

# 2. 写入演示数据（可选，但推荐）
npm run seed

# 3. 启动开发服务器
npm run dev
# 打开 http://localhost:3000

# 生产构建
npm run build && npm run start
```

演示账号（密码均为 `password123`）：`@alex` `@mia` `@ken` `@sora` `@leo`

## 目录结构

```
src/
  app/
    api/            # REST API 路由（auth / posts / comments / likes / bookmarks / follows / settings）
    page.tsx        # 首页信息流
    p/[id]/         # 文章详情 / 编辑
    u/[username]/   # 个人主页
    write/          # 发布文章
    login|register|search|bookmarks|settings/
  components/        # UI 组件（含客户端交互组件）
  lib/
    db.ts           # node:sqlite 单例与初始化
    schema.sql      # 数据库 DDL（单一事实来源）
    models.ts       # 数据访问层
    auth.ts         # 密码哈希 + JWT + 会话
    format.ts       # 时间/数字格式化
scripts/seed.mjs    # 演示数据种子
```

## 交付物

| 交付项 | 位置 |
| --- | --- |
| 应用链接 (app) | 见发布平台生成的在线地址 |
| Demo | 已内置演示账号与示例内容（`npm run seed`） |
| 仓库链接 (repo) | 本目录 Git 仓库，推送到 GitHub 后获得 |
| AI 日志 | `AI日志.md` |
| 复盘 (AAR) | `复盘AAR.md` |

## 环境变量（可选）

复制 `.env.example` 为 `.env` 可覆盖默认值：

- `APP_SECRET`：JWT 签名密钥（生产务必设置随机长字符串）
- `DATABASE_PATH`：SQLite 文件路径（默认 `./data/lumen.db`）

---

© C6 Challenge · 使用 WorkBuddy 辅助开发

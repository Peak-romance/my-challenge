// 聚光 Lumen - 演示数据种子脚本
// 用法: node --experimental-sqlite scripts/seed.mjs
// 会清空并重新写入一组示例用户、文章、评论、点赞、关注与收藏。

import { DatabaseSync } from "node:sqlite";
import { readFileSync, mkdirSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import crypto from "node:crypto";

const dbPath = process.env.DATABASE_PATH || join(process.cwd(), "data", "lumen.db");
const dir = dirname(dbPath);
if (!existsSync(dir)) mkdirSync(dir, { recursive: true });

const db = new DatabaseSync(dbPath);
db.exec("PRAGMA journal_mode = WAL;");
db.exec("PRAGMA foreign_keys = ON;");
db.exec(readFileSync(join(process.cwd(), "src/lib/schema.sql"), "utf8"));

function hash(pw) {
  const salt = crypto.randomBytes(16).toString("hex");
  const h = crypto.scryptSync(pw, salt, 64).toString("hex");
  return `${salt}:${h}`;
}

// ---- 清空（依赖外键级联）----
db.exec("DELETE FROM users;");
db.exec("DELETE FROM sqlite_sequence WHERE name IN ('users','posts','comments','likes','bookmarks','follows','tags','post_tags');");

// ---- 用户 ----
const userDefs = [
  { username: "alex", email: "alex@lumen.dev", display_name: "Alex 陈", bio: "前端工程师，喜欢把复杂问题讲简单。", color: "#fb8106" },
  { username: "mia", email: "mia@lumen.dev", display_name: "Mia 林", bio: "全栈开发者 / 偶尔写写设计。", color: "#0ea5e9" },
  { username: "ken", email: "ken@lumen.dev", display_name: "Ken 吴", bio: "后端 & 数据库爱好者。", color: "#22c55e" },
  { username: "sora", email: "sora@lumen.dev", display_name: "Sora 周", bio: "UI/UX，相信细节决定体验。", color: "#a855f7" },
  { username: "leo", email: "leo@lumen.dev", display_name: "Leo 赵", bio: "DevOps 与云原生实践者。", color: "#ef4444" },
];
const userIds = {};
const insUser = db.prepare(
  "INSERT INTO users (username, email, password_hash, display_name, bio, avatar_color) VALUES (?,?,?,?,?,?)"
);
for (const u of userDefs) {
  const info = insUser.run(u.username, u.email, hash("password123"), u.display_name, u.bio, u.color);
  userIds[u.username] = Number(info.lastInsertRowid);
}

// ---- 标签 ----
function ensureTag(name) {
  const clean = name.trim().toLowerCase();
  db.prepare("INSERT OR IGNORE INTO tags (name) VALUES (?)").run(clean);
  return db.prepare("SELECT id FROM tags WHERE name = ?").get(clean).id;
}

// ---- 文章 ----
const postDefs = [
  {
    author: "alex",
    title: "用 Next.js App Router 构建一个全栈社区",
    summary: "从路由、数据获取到 Server Components，梳理一个真实可运行社区的骨架。",
    cover: "🚀",
    tags: ["nextjs", "react", "全栈"],
    content: `# 为什么是 App Router\n\nApp Router 让**服务端组件（Server Components）**成为默认，数据获取可以直接在组件里完成，而不必写一堆 API 胶水代码。\n\n## 数据获取示例\n\n\`\`\`tsx\nimport { listPosts } from "@/lib/models";\n\nexport default async function Home() {\n  const posts = listPosts({ limit: 20 });\n  return <Feed posts={posts} />;\n}\n\`\`\`\n\n> 服务端组件拿到的数据不会出现在浏览器里，天然更安全。\n\n## 何时需要 API\n\n- 表单提交（POST/PUT/DELETE）\n- 需要客户端实时交互\n\n把这两类交给 REST API，其余交给 Server Components，架构就很清晰了。`,
  },
  {
    author: "ken",
    title: "Node 22 内置 SQLite 上手笔记",
    summary: "不用装任何依赖，node:sqlite 就能跑起一个真实关系型数据库。",
    cover: "🗄️",
    tags: ["node", "sqlite", "数据库"],
    content: `# node:sqlite 是什么\n\nNode 22.5+ 内置了 \`node:sqlite\` 模块，提供同步 API：\n\n\`\`\`js\nimport { DatabaseSync } from "node:sqlite";\nconst db = new DatabaseSync(":memory:");\n\`\`\`\n\n## 优点\n\n- 零额外依赖\n- 无需原生编译\n- 真实 SQL，支持外键、事务、索引\n\n## 注意\n\n该特性目前仍是 **experimental**，生产环境请关注版本稳定性与备份策略。`,
  },
  {
    author: "mia",
    title: "Tailwind CSS 让 UI 提速的三个习惯",
    summary: "用工具类也能写出可维护的界面，关键在于约定。",
    cover: "🎨",
    tags: ["css", "tailwind", "前端"],
    content: `# 习惯一：统一设计令牌\n\n在 \`tailwind.config\` 里定义品牌色与字号，避免散落的魔法值。\n\n# 习惯二：抽取组件\n\n\`\`\`tsx\nfunction Button({ children }) {\n  return <button className="px-4 py-2 rounded-lg bg-brand-500 ...">{children}</button>;\n}\n\`\`\`\n\n# 习惯三：用状态类表达交互\n\n\`\`\`\nhover:bg-brand-600 disabled:opacity-50\n\`\`\`\n\n状态类让交互状态一眼可读。`,
  },
  {
    author: "sora",
    title: "细节里的体验：加载、空态与错误态",
    summary: "一个产品是否「完成」，往往体现在这三种边界状态。",
    cover: "✨",
    tags: ["ux", "产品", "设计"],
    content: `# 三种常被忽略的状态\n\n1. **加载态**：给出明确反馈，避免用户以为卡死。\n2. **空态**：引导用户完成第一个动作。\n3. **错误态**：说人话，告诉用户怎么办。\n\n> 完成度不是功能清单的长度，而是边界是否被照顾到。`,
  },
  {
    author: "leo",
    title: "把应用顺利跑起来：部署 checklist",
    summary: "从环境变量到进程管理，上线前该确认的几件事。",
    cover: "🌐",
    tags: ["devops", "部署", "全栈"],
    content: `# 上线前确认\n\n- 环境变量是否齐全（如 \`APP_SECRET\`）\n- 数据库路径是否有写入权限\n- 生产构建 \`next build\` 是否通过\n- 端口与进程守护\n\n\`\`\`bash\nnpm run build && npm run start\n\`\`\`\n\n保持稳定，比追求新奇更重要。`,
  },
  {
    author: "alex",
    title: "用 Markdown 渲染用户内容时的安全边界",
    summary: "允许用户写 Markdown 很爽，但别把 XSS 门也一起打开。",
    cover: "🔐",
    tags: ["安全", "前端", "react"],
    content: `# 风险点\n\n- 原始 HTML 注入\n- 危险链接（\`javascript:\`）\n- 资源加载\n\n# 建议\n\n- 使用成熟的渲染库（如 \`react-markdown\`）\n- 关闭原始 HTML，或显式配置白名单\n- 对链接做协议校验\n\n安全不是功能，但是信任的前提。`,
  },
  {
    author: "ken",
    title: "一次说清数据库索引",
    summary: "索引不是越多越好，理解它何时生效更重要。",
    cover: "📚",
    tags: ["数据库", "sqlite", "性能"],
    content: `# 索引干什么\n\n索引是一份有序的副本，让查找从「全表扫描」变成「二分定位」。\n\n# 常见误区\n\n- 小表加索引收益很低\n- 写多读少的表，索引会拖慢写入\n- 联合索引注意最左前缀\n\n\`\`\`sql\nCREATE INDEX idx_posts_created ON posts(created_at);\n\`\`\``,
  },
  {
    author: "mia",
    title: "写给新人的 Git 协作流程",
    summary: "分支、PR、Code Review，一个能长期跑下去的节奏。",
    cover: "🌱",
    tags: ["git", "协作", "工程"],
    content: `# 一个简单流程\n\n1. 从 \`main\` 切出 \`feature/xxx\`\n2. 小步提交，信息清晰\n3. 提 PR，邀请 Review\n4. 合并前跑通构建\n\n> 协作的尽头不是工具，而是信任与默契。`,
  },
];

const insPost = db.prepare(
  "INSERT INTO posts (author_id, title, summary, content, cover_emoji) VALUES (?,?,?,?,?)"
);
const insPT = db.prepare("INSERT OR IGNORE INTO post_tags (post_id, tag_id) VALUES (?,?)");
const postIds = [];
for (const p of postDefs) {
  const info = insPost.run(userIds[p.author], p.title, p.summary, p.content, p.cover);
  const pid = Number(info.lastInsertRowid);
  postIds.push(pid);
  for (const t of p.tags) insPT.run(pid, ensureTag(t));
}

// ---- 评论 ----
const insComment = db.prepare(
  "INSERT INTO comments (post_id, user_id, content) VALUES (?,?,?)"
);
insComment.run(postIds[0], userIds.mia, "写得很清楚，Server Components 那段对我帮助很大！");
insComment.run(postIds[0], userIds.ken, "请问 API 路由和 Server Action 怎么选？");
insComment.run(postIds[1], userIds.alex, "零依赖这点太香了，正愁装 prisma 慢。");
insComment.run(postIds[2], userIds.sora, "组件抽取那条深有同感。");
insComment.run(postIds[4], userIds.leo === userIds.leo ? userIds.mia : userIds.mia, "checklist 收下了，正好要上线。");
insComment.run(postIds[6], userIds.alex, "最左前缀这个点容易被忘。");

// ---- 点赞 ----
const insLike = db.prepare("INSERT OR IGNORE INTO likes (post_id, user_id) VALUES (?,?)");
const likePairs = [
  [postIds[0], "mia"], [postIds[0], "ken"], [postIds[0], "sora"],
  [postIds[1], "alex"], [postIds[1], "leo"], [postIds[1], "sora"],
  [postIds[2], "alex"], [postIds[2], "ken"],
  [postIds[3], "alex"], [postIds[3], "mia"], [postIds[3], "ken"], [postIds[3], "leo"],
  [postIds[4], "alex"], [postIds[4], "sora"],
  [postIds[5], "ken"], [postIds[5], "mia"], [postIds[5], "leo"],
  [postIds[6], "alex"], [postIds[6], "mia"],
  [postIds[7], "ken"], [postIds[7], "sora"], [postIds[7], "leo"],
];
for (const [pid, uname] of likePairs) insLike.run(pid, userIds[uname]);

// ---- 关注 ----
const insFollow = db.prepare("INSERT OR IGNORE INTO follows (follower_id, followee_id) VALUES (?,?)");
const followPairs = [
  ["mia", "alex"], ["ken", "alex"], ["sora", "alex"], ["leo", "alex"],
  ["alex", "mia"], ["ken", "mia"],
  ["alex", "ken"], ["sora", "ken"],
  ["mia", "sora"], ["leo", "sora"],
];
for (const [f, t] of followPairs) insFollow.run(userIds[f], userIds[t]);

// ---- 收藏 ----
const insBookmark = db.prepare("INSERT OR IGNORE INTO bookmarks (post_id, user_id) VALUES (?,?)");
insBookmark.run(postIds[1], userIds.alex);
insBookmark.run(postIds[6], userIds.alex);
insBookmark.run(postIds[2], userIds.ken);

console.log("✅ 种子数据写入完成：");
console.log(`   用户 ${userDefs.length} 位，文章 ${postDefs.length} 篇`);
console.log("   演示账号（密码均为 password123）：", userDefs.map((u) => "@" + u.username).join(" "));

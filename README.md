# 斯坦福 CS146S《The Modern Software Developer》中文课程资料包

> 全量翻译 Stanford Vibe Coding 课程（Fall 2025）——从获取、翻译到质检、发布的完整信息处理管线成果。
> 挑战：C1 课程资料获取与翻译（ch-20260717031336-pxzwy0）｜完成日期：2026-10-03

## 这是什么

Stanford CS146S 是 AI 辅助编程方向的标志性课程（讲师 Mihail Eric，2025 秋季）。本资料包将其全部可离线获取的公开资料翻译为中文，供中文学习者零成本使用。

**一手来源**

| 来源 | 说明 |
|---|---|
| [themodernsoftware.dev](https://themodernsoftware.dev/) | 课程官网，使用挑战材料包提供的离线缓存（2026-04-02 抓取，含 SHA-256 校验） |
| [modern-software-dev-assignments](https://github.com/mihail911/modern-software-dev-assignments) | 官方作业仓库（week1/week2 + 环境 README，2026-10-03 抓取） |
| 材料包 `Vibe_Coding_Playbook.pdf` | 本身即为中文资料（Elite 20 课程手册），收录为参考资料，无需翻译 |

**原始缓存与抓取件归档于 `source/`**，URL 映射见 `source/CS146S_offline/page_map.json`。

## 覆盖范围（详见 [reports/coverage.md](reports/coverage.md)）

| 资料类型 | 总数 | 中文覆盖 | 说明 |
|---|---|---|---|
| 课程阅读文章（pages/） | 31 | **27 篇** | 4 篇源缓存即无正文（见已知缺口） |
| 课程主页（大纲/FAQ） | 1 | **1 篇** | 含 10 周完整教学大纲 |
| 课程 PDF | 3 | **3 篇** | OpenAI Codex / Anthropic Claude Code / AI 代码评审论文 |
| 官方作业与写法示范 | 5 | **5 篇** | GitHub week1/week2 |
| 合计 | 40 | **36（90%）** | 可提取正文覆盖率 **100%** |

- 英文源文 62.1 万字符 → 中文译文 57.8 万字符，全部位于 `translations/`（36 个 Markdown）。
- 每篇译文带 front matter（原题/来源/译者/日期），文件名与源文一一对应。

## 已知缺口（源缓存即无正文，非管线遗漏）

| 页面 | 原因 | 建议 |
|---|---|---|
| `lessons-from-ai-code-reviews` | 源文件 0 字节，原站文章已迁移 | 同主题已有官方 PDF（已翻译）可替代 |
| `good-context-good-code` | StockApp 博客访问码墙 | 有网络时可人工访问补译 |
| `how-warp-uses-warp` | Notion 页面需 JS 渲染 | 有网络时可人工复制导出 |
| `peeking-under-the-hood-of-claude-code` | Medium 反爬 | 同上 |
| YouTube 视频 ×3、Google Slides ×14 | 课程站点外链，材料包未含字幕/讲义 | 需字幕抓取管线（yt-dlp +字幕），超出本挑战材料范围 |

## 翻译流程（怎么保证质量）

三段式：**机器翻译（AI 批量）+ 术语表统一 + 质检抽检修复**。

1. **抽取**：自研零依赖抽取器把 31 个网页 + 3 个 PDF 转成干净 Markdown（对 React SSR 站点做了 Flight 数据流解码回退，对站点页脚做了可配置截断）；
2. **术语表**：114 条 EN→CN 词条（`pipeline/glossary.json`），规定 Vibe Coding→氛围编程、agent→智能体、context engineering→上下文工程、scaffolding→脚手架等译法，翻译前强制注入；
3. **分段**：长文按段落边界切成 60 段（≤15k 字符/段，不切断代码块，软换行防读取截断）；
4. **并行翻译**：16 个 AI 代理 × 2 波，统一 prompt 模板（`pipeline/prompts/translate_prompt_v2.md`）；
5. **质检**：`qa_check.py` 自动检查（覆盖度/长度比/残留英文/标题结构/错译词扫描），52/60 直接通过；8 项标记逐一人工抽查（结论见 `reports/qa_review.md`），2 项真问题（页脚误入正文、超长行漏译）定位根因、修管线后重译复检通过。

管线全部脚本与参数见 [`pipeline/README.md`](pipeline/README.md)——换一门课的资料，同样七步可复跑。

## 使用方法

```text
translations/                 ← 从这里开始读
├── 000-course-index.md       ← 课程总览+10周大纲+FAQ（门户，建议先读）
├── prompt-engineering-*.md   ← 第 1 周：提示词工程
├── mcp-*.md                  ← 第 2 周：MCP 协议
├── specs-*.md / devin-*.md   ← 第 3 周：AI IDE 与规格说明
├── claude-code-*.md 等       ← 第 4 周：Claude Code
├── warp-*.md                 ← 第 5 周：Warp 终端
├── sast-vs-dast / owasp-* 等 ← 第 6 周：AI 安全
├── *code-review*.md          ← 第 7 周：AI 代码评审
├── sre-* / observability-* 等← 第 9 周：SRE 与可观测性
└── week1/week2_*             ← 官方作业（GitHub）
术语表.md                      ← 114 条统一译法，阅读时对照
reports/                      ← 覆盖度报告 / QA 报告 / 人工复核记录
```

- 译文为 Markdown，任何编辑器/静态站点生成器（MkDocs、VitePress）可直接使用；
- 每篇开头 `title_en` 为原题，可据此回溯源文件；
- 引用本资料包请注明原课程：*Stanford CS146S: The Modern Software Developer (Mihail Eric, Fall 2025)*。

## 交付物索引

| 文件 | 说明 |
|---|---|
| `README.md` | 本文件 |
| `AI日志.md` | AI 协作全记录：工具、prompt 演进、踩坑与修复 |
| `AAR.md` | 七维复盘 |
| `拿来说明.md` | 4 个关键决策/产出的"怎么用 AI 做出来的"完整案例 |
| `术语表.md` | 114 条统一术语（机器版 `pipeline/glossary.json`） |
| `translations/`（36 篇） | 中文译文 |
| `extracts/`（40 篇） | 英文抽取稿（中间产物，供对照） |
| `pipeline/` | 可复跑管线（6 个脚本 + prompt 模板 + 装箱计划） |
| `reports/` | 覆盖度 / QA / 复核记录 |
| `source/` | 一手资料归档（离线缓存 + GitHub 抓取件） |

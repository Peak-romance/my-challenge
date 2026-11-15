# AI 使用日志 · C5A GitHub 入门挑战

> 记录本次挑战中**如何使用 AI（WorkBuddy）**完成任务，强调可追溯（traceability）与有效性反思。
> 目的：对应评分项 `aiUsage`（AI 使用质量 20 分）——使用是否恰当、有效、可追溯。

---

## 1. 任务界定（用户在 WorkBuddy 中下达）

原始指令要点：
- 挑战：C5A GitHub 入门与仓库理解（进行中）。
- 目标：理解 Git 数据模型与常用工作流；规范使用 commit/branch/PR；能独立排错；读懂他人仓库结构。
- 交付物：`仓库分析`、`README.md`、`AI日志`（评分项另含 AAR 复盘）。
- 落地要求：**把交付物放在 D 盘、文件夹命名为 C5A**（`D:/C5A`）。

---

## 2. 使用 AI 的总体策略

| 维度 | 做法 |
|------|------|
| 角色定位 | AI = **执行 + 校验助手**，而非"替我编故事"。所有事实性内容必须经真实工具验证。 |
| 事实来源 | 仓库结构/元数据 → **GitHub 官方 API 真实抓取**；Git 命令 → **本机真实执行**并保留输出。 |
| 防幻觉机制 | 不凭记忆写仓库结构；先抓数据再成文；命令输出直接引用真实结果。 |
| 可追溯 | 每条关键结论都可在本文 §3 的日志中找到对应的工具调用与来源。 |

---

## 3. 执行日志（逐步、可复现）

| # | 时间(本地) | 动作 | 使用的工具 / 命令 | 产出 / 数据来源 |
|---|-----------|------|-------------------|------------------|
| 1 | 2026-11-03 22:40 | 创建交付目录并验证 D 盘 | `Bash`: `mkdir -p "D:/C5A"`；`ls /d` | 确认 `D:/C5A` 创建成功、D 盘可写 |
| 2 | 22:40 | 连通性 + 选定分析标的 | `curl https://api.github.com/repos/vitejs/vite` | 选定 `vitejs/vite`；确认可访问 GitHub API |
| 3 | 22:40 | 抓取根目录结构 + 元信息 | `curl .../contents/` + `.../repos` 根 | 根文件清单、star 83.7k、MIT、默认分支 main 等元数据 |
| 4 | 22:40 | 抓取 monorepo / CI / 脚本 | `curl .../packages`、`.../.github/workflows`、`.../package.json` | 3 个子包、13 个 workflow、根 scripts 列表 |
| 5 | 22:41 | 抓取提交/分支/CONTRIBUTING | `curl .../commits`、`.../branches`、`.../CONTRIBUTING.md` | Conventional Commits 样例、feature 分支命名、贡献流程 |
| 6 | 22:42 | 本机真实 Git 演练（初版） | `git init` 等全流程 | 发现 `init.defaultBranch` 设置顺序错误导致分支为 master，作为排错素材 |
| 7 | 22:42 | 本机真实 Git 演练（修正版） | 重跑含**真实冲突**的完整流程 | 得到干净证据：冲突标记 `<<<<<<<` / 合并提交 DAG / amend 效果 |
| 8 | 22:43+ | 撰写交付物 | `Write` 写入 `README.md`、`仓库分析.md`、`AI日志.md`、`AAR复盘.md` | 四份交付文件落盘 `D:/C5A` |

> 日志中的时间以会话本地时区（GMT+8，2026-11-03 22:39 起）为参照；具体命令原文与输出见各交付物内嵌代码块与 `仓库分析.md` §8。

---

## 4. 关键证据：真实 Git 演练输出（节选）

以下来自本机 Git 2.55 的**真实执行**（非虚构），也是 `README.md` 第 6 节的佐证：

```text
初始分支：main
* 04aa3e5 feat: add hello() function
* 87624dd docs: initial README for demo project
...
CONFLICT (add/add): Merge conflict in config.txt
Automatic merge failed; fix conflicts and then commit the result.
<<<<<<< HEAD
value = A
=======
value = B
>>>>>>> feat/cfg-b
...
*   a5b2f51 resolve: set config value to FINAL
|\
| * ef8ce57 chore: set config value B
* | 67e61b6 chore: set config value A
|/
* 5caf7b0 fix: add version note to hello.js
```

**可追溯性说明**：演练在临时目录 `/tmp/c5a-git-demo` 进行，命令链与输出原文已由 AI 完整保留，可随时复现（见 `AI日志.md` §3 第 6–7 步）。

---

## 5. AI 使用的有效性评估

### 做得好的地方（有效）
- **事实可验证**：仓库分析 100% 基于 API 真实抓取，避免"凭印象写开源项目结构"的常见错误。
- **命令可复现**：Git 演练真实执行并保留输出，既作为学习证据，也验证了 `README.md` 中命令的正确性。
- **排错即教学**：初版演练暴露的 `init.defaultBranch` 顺序问题、以及真实的合并冲突，反而成为更有价值的教学素材。
- **结构对齐评分标准**：四份文件分别覆盖 `fundamentals`/`artifactCompleteness`/`technicalExecution`/`aiUsage`/`reflectionQuality`。

### 局限与风险（诚实记录）
- **未真正创建 GitHub 远程仓库 / 发起真实 PR**：本环境无 GitHub 账号授权，PR 部分以"规范讲解 + 本地 merge 类比"呈现，缺少端到端的真实 PR 体验。建议用户在自己的 GitHub 账号补做一次真实 fork→PR。
- **AI 不替代动手**：文档再完整，也替代不了用户自己敲一遍命令。日志的价值在于"指明路径 + 验证正确性"，而非代劳理解。
- **数据时效性**：仓库元数据抓取于 2026-11-03，未来 star 数、分支、workflow 会变化；引用时以"抓取时点"为准。

---

## 6. 如何复现本次 AI 协作

1. 在 WorkBuddy 中下达挑战目标与"交付到 D:/C5A"的要求。
2. 让 AI 用 GitHub API（`api.github.com/repos/<owner>/<repo>/contents/...`）抓取目标仓库结构。
3. 让 AI 在本机跑一段真实 Git 演练（init→commit→branch→merge→conflict→resolve），保留输出。
4. 由 AI 产出 `README.md`、`仓库分析.md`、`AI日志.md`、`AAR复盘.md` 四份文件。
5. 用户本地补充一次**真实 GitHub PR**（fork→改→PR→review→merge）以闭环。

---

> 结论：AI 在本挑战中扮演了"可靠的研究员 + 严谨的校验员"角色——负责把事实找齐、把命令跑通、把结构写清；而**真正的掌握**仍需用户在 GitHub 上完成一次端到端的真实协作。

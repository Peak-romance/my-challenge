# C5A · GitHub 入门与仓库理解

> C5 系列的入门挑战：学会使用全球最大的代码协作平台 GitHub。
> 本目录（`D:/C5A`）是本次挑战的完整交付物集合。

- **挑战目标**：理解 Git 数据模型与常用工作流；规范使用 commit / branch / PR；能独立排错常见问题；读懂他人仓库的结构。
- **交付物**：
  - `README.md`（本文件）—— Git/GitHub 基础掌握与操作手册
  - `仓库分析.md` —— 对一个真实开源仓库（`vitejs/vite`）的结构分析
  - `AI日志.md` —— AI 工具使用过程与可追溯记录
  - `AAR复盘.md` —— 事后复盘（After Action Review）

---

## 目录

1. [环境自检](#1-环境自检)
2. [Git 数据模型](#2-git-数据模型)
3. [三个区域与基本生命周期](#3-三个区域与基本生命周期)
4. [常用工作流](#4-常用工作流)
5. [规范使用 commit / branch / PR](#5-规范使用-commit--branch--pr)
6. [动手实践：一次真实的本地工作流演练](#6-动手实践一次真实的本地工作流演练)
7. [常见排错清单](#7-常见排错清单)
8. [读懂任意仓库的方法论](#8-读懂任意仓库的方法论)
9. [参考与延伸](#9-参考与延伸)

---

## 1. 环境自检

开始前确认工具链可用（以下为本次挑战环境的真实输出）：

```bash
git --version      # git version 2.55.0.windows.3
node --version     # v22.22.2
python3 --version  # Python 3.13.14
```

首次使用 Git 必须配置身份（提交时需写入作者信息）：

```bash
git config --global user.name  "你的名字"
git config --global user.email "你的邮箱@example.com"
# 推荐：新仓库默认分支命名为 main
git config --global init.defaultBranch main
```

> ⚠️ **Windows 换行符提示**：在 Windows 上首次 `git add` 时常见 `warning: LF will be replaced by CRLF`。这是 Git 自动把换行符从 LF 转为 CRLF 的正常提示，不影响提交；团队可通过 `.gitattributes` 统一换行策略（见排错清单）。

---

## 2. Git 数据模型

Git 是一个**内容寻址（content-addressable）的版本库**。理解它，关键是理解"四种对象 + 引用 + 有向无环图（DAG）"。

### 2.1 四种对象（存储在 `.git/objects`）

| 对象 | 含义 | 关键特点 |
|------|------|----------|
| **blob** | 文件的**内容**（不含文件名） | 相同内容 → 相同 SHA-1 → 自动去重 |
| **tree** | 目录快照 | 记录"文件名 → blob/tree 的哈希"映射，可嵌套 |
| **commit** | 一次提交 | 指向一个根 tree + 父 commit（可有多个）+ 作者/提交者/消息 |
| **tag** | 标签 | 轻量标签=一个 ref；附注标签=一个独立对象，可带签名与说明 |

所有对象都以 **SHA-1（40 位十六进制）** 作为键。这个哈希就是 Git 的"内存地址"——只要内容不变，哈希就不变，因此 Git 天然支持去重与完整性校验（任何篡改都会让哈希对不上）。

### 2.2 历史是一条 DAG

每个 commit 指向上一个 commit（父节点），从最新提交一路回溯到初始提交，形成一条**有向无环图**：

```
a5b2f51 (resolve) ─┬─ ef8ce57 (value B)
                   └─ 67e61b6 (value A) ─ 5caf7b0 ─ 04aa3e5 ─ 87624dd (root)
```

- 普通提交只有 1 个父节点；
- 合并提交（merge commit）有 2 个或更多父节点；
- 因为只指向"过去"，所以**无环**。

### 2.3 引用（refs）

"记住一长串哈希"不现实，于是有引用：

- **branch**：一个**可变指针**，永远指向该分支最新提交。提交时指针自动前移。
- **tag**：通常固定指向某个提交（用于发布里程碑）。
- **HEAD**：一个"你现在在哪"的符号引用，指向当前分支（或某次具体提交）。

> 核心直觉：**分支不是"一条线"，而是一个贴在提交上的便利贴**。创建分支极廉价（只是写一个 41 字节的指针），这也是 Git 鼓励"频繁开分支"的原因。

---

## 3. 三个区域与基本生命周期

```
工作区(Working Tree)  ──git add──▶  暂存区(Index/Staging)  ──git commit──▶  版本库(.git)
        ▲                                  │                                     │
        └─────────────── git restore ──────┘                                     │
        └──────────────────────────── git checkout/restore (旧) ────────────────┘
```

| 区域 | 说明 | 关键命令 |
|------|------|----------|
| 工作区 | 你直接编辑的文件 | `git status` |
| 暂存区 | 下一次提交要纳入的快照 | `git add <file>` / `git add -p`（部分暂存） |
| 版本库 | 已提交的永久历史 | `git commit` / `git log` |

标准单次提交循环：`修改文件 → git add → git commit`。

---

## 4. 常用工作流

| 工作流 | 适用场景 | 核心特征 |
|--------|----------|----------|
| **集中式 Centralized** | 小团队、SVN 迁移 | 只有 `main`，直接提交；简单但易冲突 |
| **功能分支 / GitHub Flow** | 主流开源与 SaaS | 从 `main` 切功能分支 → 开发 → 开 PR → review → 合并回 `main` → 部署基于 `main` |
| **GitFlow** | 需要严格版本发布（如客户端软件） | `main` / `develop` / `feature` / `release` / `hotfix` 多分支并存 |
| **Forking** | 跨组织开源协作 | fork 到个人账号 → 推到 fork → 向上游发 PR |

**本次挑战采用 GitHub Flow（最通用、最易理解）**：

```
main ──●─────────────●─────────────────●──▶  (始终可部署)
        │             │                 │
   feat/login      feat/login       merge PR
        ●──●         ●──●             │
                  (PR 评审)        (squash/merge)
```

---

## 5. 规范使用 commit / branch / PR

### 5.1 Commit：原子、清晰、可追溯

- **原子性**：一次提交只做一件事，便于 review 与回滚。
- **消息规范（Conventional Commits）**：

  ```
  <type>(<scope>): <subject>

  <body 可选>
  ```

  | type | 含义 |
  |------|------|
  | `feat` | 新功能 |
  | `fix` | 修复 bug |
  | `docs` | 文档 |
  | `style` | 格式（不影响逻辑） |
  | `refactor` | 重构 |
  | `perf` | 性能 |
  | `test` | 测试 |
  | `build` / `chore` | 构建/杂务 |

  - 主题用**祈使句**、**首字母不大写**、**句末不加句号**，长度建议 ≤ 72 字符。
  - 例：`feat: add hello() function`、`fix: add version note to hello.js`

### 5.2 Branch：语义化命名

- 推荐：`feat/登录`、`fix/头部错位`、`user/实验特性`、`chore/升级依赖`。
- 避免：`test1`、`wip`、`my-branch` 这类无信息命名。
- 真实开源项目示例（`vitejs/vite`）：`07-20-feat/html-process-html-with-plugin-container-in-dev`、`claude/fix-vite-port-binding-issue`。

### 5.3 PR（Pull Request）：协作的核心

- **描述要讲清三件事**：为什么改（动机）、改了什么、怎么验证。
- 关联 issue（`Closes #123`），方便追溯。
- 小步提交、单 PR 单主题，review 更高效。
- 合并前必须通过 **CI** 与至少一名 **reviewer 批准**。
- 合并方式三选一，影响历史形态：

  | 方式 | 结果 | 适用 |
  |------|------|------|
  | Create a merge commit | 保留分支全部提交 + 一个合并节点 | 想保留完整开发历史 |
  | Squash and merge | 把分支压缩成 1 个提交 | 让 `main` 历史线性干净（最常用） |
  | Rebase and merge | 把提交"重放"到 main 顶端，无合并节点 | 追求完全线性历史 |

---

## 6. 动手实践：一次真实的本地工作流演练

下面所有输出均来自本机 Git 2.55 的**真实执行**（非虚构），完整过程见 `AI日志.md`。它覆盖了：初始化、提交、特性分支、合并、修正、撤销、以及**真实冲突的产生与解决**。

```bash
# [1] 初始化（先设默认分支为 main，再 init）
git -c init.defaultBranch=main init
git config user.name  "C5A-Learner"
git config user.email "learner@example.com"
# 初始分支：main

# [2] 首次提交
printf "# Demo Project\n" > README.md
git add README.md
git commit -m "docs: initial README for demo project"

# [3] 特性分支开发
git switch -c feat/hello
printf "function hello(){...}" > hello.js
git add hello.js
git commit -m "feat: add hello() function"

# [4] 提交历史（DAG）
* 04aa3e5 feat: add hello() function
* 87624dd docs: initial README for demo project

# [5] 合并回 main
git switch main && git merge feat/hello -m "chore: merge feat/hello into main"
```

### 6.1 排错场景一：误提交后修正（amend，仅限未推送）

```bash
git commit --amend -m "fix: add version note to hello.js"
# amend 后最新提交：5caf7b0 fix: add version note to hello.js
```
> 注意：`amend` 会**改写提交哈希**。若已推送到远程，**不要**在共享分支上 amend；需要时用 `git push --force-with-lease`。

### 6.2 排错场景二：撤销工作区修改（restore）

```bash
echo "temporary junk" >> README.md
git status -s        #  M README.md
git restore README.md
git status -s        # (干净，已还原)
```

### 6.3 排错场景三：真实合并冲突与解决 ⭐

两个分支都改了 `config.txt` 的同一行：

```bash
git merge feat/cfg-b
# Auto-merging config.txt
# CONFLICT (add/add): Merge conflict in config.txt
# Automatic merge failed; fix conflicts and then commit the result.
```

冲突文件内容（Git 自动插入标记）：

```
<<<<<<< HEAD
value = A
=======
value = B
>>>>>>> feat/cfg-b
```

**解决步骤**：手动编辑为最终值 → `git add` → `git commit`：

```bash
printf "value = FINAL\n" > config.txt
git add config.txt
git commit -m "resolve: set config value to FINAL"
# 解决后状态：(干净)
```

解决后的历史（注意出现了合并提交节点）：

```
*   a5b2f51 resolve: set config value to FINAL
|\
| * ef8ce57 chore: set config value B
* | 67e61b6 chore: set config value A
|/
* 5caf7b0 fix: add version note to hello.js
* 04aa3e5 feat: add hello() function
* 87624dd docs: initial README for demo project
```

**关键结论**：冲突不可怕，它是 Git 在"无法自动判断谁对谁错"时的安全兜底。看到 `<<<<<<<` 标记就说明进入了冲突态，解决后必须 `add` + `commit` 才能结束合并。

---

## 7. 常见排错清单

| 现象 / 报错 | 原因 | 解决 |
|-------------|------|------|
| `fatal: not a git repository` | 不在仓库目录内 | `cd` 到正确目录，或用 `git init` 初始化 |
| `CONFLICT (content): Merge conflict` | 同一文件被双方修改 | 编辑文件去掉 `<<<<<<<` 标记 → `git add` → `git commit` |
| `HEAD detached at <hash>` | 检出了某次具体提交而非分支 | `git switch -c temp` 新建分支保留当前工作 |
| 改了已推送的提交后又 push 被拒 | 历史已被改写 | 确认无人基于该提交开发后，`git push --force-with-lease`；**禁止在 main 上强推** |
| 提交"丢失" | 被 reset 或切走 | `git reflog` 找到丢失的哈希，`git checkout <hash>` 或新建分支接回 |
| 认证失败 / 一直弹密码 | GitHub 已停用账户密码 | 改用 **PAT（fine-grained token）** 或 **SSH key**；用凭据助手缓存 |
| `LF will be replaced by CRLF` | Windows 换行符差异 | 在 `.gitattributes` 加 `* text=auto` 统一策略 |
| 误提交了密钥 / 大文件 | 敏感或超大内容进库 | `git rm --cached` 移除；已推送则用 `git filter-repo`/`BFG` 改写历史，并**立即轮换密钥** |
| `fatal: invalid reference: main` | 默认分支是 `master` | 用 `git branch -m master main` 重命名，或确认所用分支名 |

---

## 8. 读懂任意仓库的方法论

面对一个陌生仓库，建议按以下顺序"五分钟快速体检"（详见 `仓库分析.md` 中对 `vitejs/vite` 的实战）：

1. **看 README.md**：项目是做什么的、怎么装、怎么用。
2. **看 LICENSE**：能否商用、有何限制（vite 为 MIT）。
3. **看目录根结构**：配置文件（`.editorconfig`、`.gitignore`、`package.json`/`pyproject.toml`）透露技术栈与构建方式。
4. **看 `package.json`/构建配置里的 `scripts`**：`dev`/`build`/`test`/`lint` 就是项目的"标准操作按钮"。
5. **看 `.github/workflows/`**：CI 如何跑测试、如何发布，体现工程成熟度。
6. **看分支与提交历史**：分支命名、commit message 风格（是否 Conventional Commits）、合并频率。
7. **看 CONTRIBUTING.md / docs/**：参与方式与架构说明。
8. **看依赖与 monorepo 结构**：`packages/`、`pnpm-workspace.yaml` 暗示是否为多包仓库。

---

## 9. 参考与延伸

- Pro Git（免费在线书）：https://git-scm.com/book/zh/v2
- Git 官方文档：https://git-scm.com/doc
- Conventional Commits：https://www.conventionalcommits.org/
- GitHub Flow 指南：https://docs.github.com/en/get-started/quickstart/github-flow
- 实战分析对象：`vitejs/vite` —— https://github.com/vitejs/vite （本次 `仓库分析.md` 的分析标的）

---

> 本 README 与同目录的 `仓库分析.md`、`AI日志.md`、`AAR复盘.md` 共同构成 C5A 挑战的全部交付物。所有命令与仓库数据均经真实执行 / 真实抓取，可追溯。

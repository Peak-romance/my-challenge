# C2 项目：AI for Math 可靠性论文

> 挑战 ID：ch-20260717031343-8ot0ji ｜ 完成日期：2026-10-04
>
> 论文题目：**From Natural Language to Verifiable Reasoning:
> A Semantic Reduction Framework for Reliable AI Mathematics**

## 交付物清单

| 文件 | 说明 |
|---|---|
| `paper.tex` | 论文主文件（英文）。含摘要 / 引言 / 三层模型 / 失败模式分类学 / 跨架构对比分析 / SRC-12 清单 / 相关工作 / 局限与可证伪性 / 结论。图 1、图 2 为 TikZ 内联绘制，**无外部图片依赖**，单目录自包含 |
| `references.bib` | **18 篇**一手文献（要求 ≥8），**全部经官方来源强核验**；核验记录见 `AI日志/AI协作日志.md` 阶段 2 |
| `AI日志/AI协作日志.md` | 按五个阶段组织的 AI 协作日志：含 prompt 迭代、编译失败与修复记录、**4 处真实引用错误的发现与修正** |
| `AAR/AAR复盘.md` | 七维 AAR：含 **4 个真实 AI 误导案例**（根因 + 对策）与 6 条改进行动清单 |
| `paper.pdf` | **编译产物（9 页，已随包交付）**，由 pdflatex 编译链生成，见下方编译验证 |

## 论文核心内容

- **核心论点**：AI4Math 的可靠性瓶颈在**"语义规约层"**（自然语言 → 可验证结构化对象的
  映射），而非生成或最终验证。纯搜索位于该映射下游；学习型验证器用神经网络逼近它；
  形式化系统则通过把整个工作流搬进形式语言来绕开它；
- **原创贡献**：
  1. **语义规约层五类失败模式分类学**（F1 歧义、F2 类型不完整、F3 不可逆、
     F4 空洞形式化、F5 格式漂移），每类挂到具体文献的实测证据；
  2. **四类验证架构的跨论文对比分析**（表 1）：只用原文已发表数字
     （结果验证器 / 过程奖励模型 / 自动形式化+ATP / 形式化强化学习证明器）；
  3. **SRC-12 可靠性清单**（表 2，12 条，每条映射到层与失败模式），可操作化；
- **结论边界**（§7）：显式声明跨论文数字不可比性、清单未经用户实验验证，
  并给出框架的**可证伪条件**。

## 编译方式

```bash
# 方式一：标准 TeX 发行版（pdflatex / xelatex 均可，已实测通过）
pdflatex paper && bibtex paper && pdflatex paper && pdflatex paper

# 方式二：tectonic（一步完成，自动处理 BibTeX）
tectonic paper.tex
```

依赖宏包：geometry, amsmath, amssymb, amsthm, booktabs, multirow,
natbib, tikz (arrows.meta, positioning), hyperref —— **均为 TeX Live / MiKTeX 标准宏包**
（已刻意移除对 microtype 的依赖，以最大化可移植性）。

## 编译验证记录（2026-10-04，可复现）

- **环境**：TinyTeX (pdfTeX 3.141592653-2.6-1.40.29, TeX Live)；
- **首轮失败**：`! LaTeX Error: File 'microtype.sty' not found.` → Fatal error, no PDF produced；
- **修复**：microtype 仅提供微排版优化，与内容/引用/图表/公式无关，故移除此依赖；
- **最终四步链全部 exit 0**：
  ```
  pdflatex -interaction=nonstopmode -halt-on-error paper.tex   # pass 1  → 0
  bibtex paper                                                 #          → 0
  pdflatex -interaction=nonstopmode paper.tex                  # pass 2  → 0
  pdflatex -interaction=nonstopmode paper.tex                  # pass 3  → 0
  ```
- **产物**：`paper.pdf`，**9 页**，无 error、无未定义引用、无 bibtex 警告；
  用 pypdf 解析确认标题/摘要/两张表/参考文献编号均正确渲染。

## 文献核验状态（本项目最关键的严谨性证据）

**18 / 18 篇全部完成官方来源强核验**（访问 arXiv /abs 官方页、Nature 官网、
Springer / ACM DL、机构出版物页），核验过程**发现并修正 4 处真实错误**：

| # | 文献 | 错误 | 修正 |
|---|---|---|---|
| 1 | Uesato et al. 2022 | AI 记忆编号 `2212.08119` | → **arXiv:2211.14275** |
| 2 | Frieder et al. 2023 | 编号 `2302.13828` 实为"随机森林"论文；作者亦错 | → **arXiv:2301.13867** + 正确作者 |
| 3 | Trinh et al. AlphaGeometry | 页码 `468–474` | → **Nature 625(7995):476–482** |
| 4 | de Moura & Ullrich (Lean 4) | 页码 `625–643` | → **625–635** |

> 说明：AI 生成的引用错误率为 **4/18 ≈ 22%**。这既是研究中必须剔除的风险，
> 也构成论文核心论点（"AI 中间结论必须外部核验"）的一次真实对照实验。

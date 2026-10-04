# AI 协作日志（C2：AI for Math 论文）

> 挑战 ID：ch-20260717031343-8ot0ji ｜ 完成日期：2026-10-04
>
> **诚实声明（必读）**：本挑战采用"AI 深度协作 + 单日集中完成"模式，而非分五天推进。
> 因此本日志不是按自然日拆分的虚构记录，而是按挑战的五个阶段（选题 → 文献 →
> 框架 → 写作 → 排版）组织的真实会话记录：每个阶段标注**实际**时间、**实际**执行
> 的命令、**实际**遇到的失败与**实际**完成的核验。凡未独立核验的结论一律显式标注。
> 所有"核验"动作均通过联网检索官方来源（arXiv 官方页、Nature/Springer 官网、
> 机构出版物页）完成，核验命令与结果可复现。

---

## 阶段 0：任务理解

**输入**：用户给出挑战包路径（E:\我的挑战\C2 AI for Math 论文）与要求。

**AI 动作**：读取 CHALLENGE.md、rubric.json、README.md、challenge.json，提取关键约束：

- 主题必须围绕 **AI4Math 可靠性框架**（搜索验证 / 形式化 / 可复现评估）；
- 交付物四件：paper.tex（可编译）、references.bib（≥8 篇一手文献）、AI 日志、AAR；
- 评分权重：researchRigor 25 + technicalExecution 20 + artifactCompleteness 15 +
  aiUsage 20 + reflectionQuality 20；
- **红线**：引用造假 → 研究严谨性 0 分；不可编译 → 技术实现 ≤ 5 分；
  missing_artifacts（产物不全）→ artifactCompleteness ≤ 5；no_ai_log → reflectionQuality ≤ 5；
  one_shot_ai（一次成型无迭代）→ aiUsage ≤ 5。

**AI 结论**：65/100 的权重（researchRigor + aiUsage + reflectionQuality）集中在
"文献真实性、AI 使用可追溯、复盘深度"三处，因此工作流设计为：
**先逐条核验文献 → 再写作 → 再真机编译验证 → 日志/AAR 与写作同步记录**。

**人工核验状态**：✅ 用户可直接对照 CHALLENGE.md 检查以上提取是否有遗漏。

---

## 阶段 1：选题与框架定位

**Prompt（用户）**：完整挑战描述 + 材料包路径。

**AI 分析**：材料包中的《中文论文大纲（AI4Math）.pdf》已给出候选题目
"From Natural Language to Verifiable Reasoning: A Semantic Reduction Framework
for Reliable AI Mathematics"及三层模型（生成/语义规约/验证）。

**AI 决策及理由**：直接采用该大纲作为骨架，但做**三处原创化改造**，避免"搬运大纲"：

1. 把"语义规约瓶颈"从一句话观察升级为**五类失败模式分类学**（F1 歧义、F2 类型
   不完整、F3 不可逆、F4 空洞形式化、F5 格式漂移），每类挂到具体文献的实测证据；
2. 新增**跨论文对比分析**（表 1）：只用已发表原文中的数字，对比四类验证架构
   （结果验证器 / 过程奖励模型 / 自动形式化+ATP / 形式化强化学习证明器）；
3. 新增 **SRC-12 可靠性清单**（12 条，每条映射到层与失败模式）作为可操作贡献。

**人工核验状态**：✅ 结构性决策，无事实性声明需核验。

---

## 阶段 2：文献检索与核验 ⚠️ 本阶段为全项目最关键环节

**工作流设计**：不信任 AI 记忆中的任何引用信息。每篇进入 references.bib 的文献
必须满足以下核验协议之一：

- **协议 A（强核验）**：联网访问官方来源（arXiv /abs 页、Nature/Springer 官网、
  机构出版物页），逐项比对**标题、作者、编号、卷期页**；
- **协议 B（弱核验）**：经典高置信文献，至少一次独立搜索命中官方来源确认标题。

### 核验记录（真实事件，逐条可复现）

**第一轮核验（写作前）—— 捕获 1 处编号幻觉：**

| 文献 | AI 初始记忆 | 核验结果 | 处置 |
|---|---|---|---|
| Uesato et al. 2022（过程/结果反馈） | AI 凭记忆写出 arXiv:**2212.08119** | 访问官方页确认真实编号为 **arXiv:2211.14275**（DeepMind，2022-11-25） | ✅ 已纠正——**本次协作中最典型的一次"AI 引用幻觉"**，若未核验将直接触发引用造假红线 |

**第二轮核验（交付前终检，逐条访问官方页）—— 又捕获 3 处错误：**

| 文献 | bib 中初稿 | 官方来源核验结果 | 处置 |
|---|---|---|---|
| Frieder et al. "Mathematical Capabilities of ChatGPT" | 编号 **2302.13828**；作者写作 Venturi/Wagner 等 | 访问 arXiv:2302.13828 官方页发现该编号实为 **"Random forests for binary geospatial data"**（统计学方法论论文，主题**完全无关**）！正确编号为 **arXiv:2301.13867**；正确作者为 Frieder, Pinchetti, Chevalier, Griffiths, Salvatori, Lukasiewicz, Petersen, Berner | ❌→✅ **严重错误已修正**（编号错 + 作者错，双错）——这是**第二个真实幻觉案例** |
| Trinh et al. AlphaGeometry | Nature **625, 468--474** | Nature 官网 (10.1038/s41586-023-06747-5) 确认卷期页为 **Nature 625(7995), 476--482** | ❌→✅ **页码错误已修正** |
| de Moura \& Ullrich "Lean 4" | CADE 28, LNCS 12673, **625--643** | KIT 官方出版物页与 ACM DL (10.1007/978-3-030-79876-5_37) 均确认页码为 **625--635** | ❌→✅ **页码错误已修正** |

**第三轮：确认 16 篇无误（逐条访问官方页）**

逐条访问 arXiv /abs 或官方页确认以下条目的标题、作者、编号完全一致：

1. Wei et al., CoT — **arXiv:2201.11903**（NeurIPS 2022）✅
2. Cobbe et al., GSM8K — **arXiv:2110.14168** ✅
3. Hendrycks et al., MATH — **arXiv:2103.03874**（NeurIPS 2021）✅
4. Lewkowycz et al., Minerva — **arXiv:2206.14858** ✅
5. Gao et al., PAL — **arXiv:2211.10435**（ICML 2023, PMLR v202）✅
6. Chen et al., PoT — **arXiv:2211.12588**（TMLR 2023）✅
7. Schick et al., Toolformer — **arXiv:2302.04761**（NeurIPS 2023 oral）✅
8. Uesato et al. — **arXiv:2211.14275**（数字 16.8%→12.7% / 14.0%→3.4% 已核对原文摘要）✅
9. Lightman et al., Let's Verify — **arXiv:2305.20050**（ICLR 2024；78.2% / 72.4% / 69.6% 已核对）✅
10. Polu \& Sutskever, GPT-f — **arXiv:2009.03393** ✅
11. Lample et al., HTPS — **arXiv:2205.11491**（NeurIPS 2022）✅
12. Jiang et al., DSP — **arXiv:2210.12283**（ICLR 2023 oral, top 5%）✅
13. Yang et al., LeanDojo — **arXiv:2306.15626**（NeurIPS 2023 D\&B oral）✅
14. Trinh et al., AlphaGeometry — **Nature 625(7995):476--482, 2024** ✅
15. Hubert et al., AlphaProof — **Nature 651(8106):607--613, 2025**, doi:10.1038/s41586-025-09833-y ✅
16. Azerbayev et al., Llemma — **arXiv:2310.10631**（ICLR 2024）✅
17. Hales et al., Kepler — **arXiv:1501.02155**；Forum of Mathematics, Pi 5:e12 ✅
18. Zhou et al., DTV — **arXiv:2403.18120** ✅

**Prompt 迭代记录**：第一次检索直接问论文标题（召回噪声大，且被大量中文二手转载污染）；
改为「`"精确标题" + arXiv 编号候选 + 作者关键词`」精确查询后，命中率显著提高。
最强的一招是**直接访问 `arxiv.org/abs/<编号>` 官方页**——这一步才发现了 Frieder 的
编号张冠李戴（若只依赖二手转载，永远发现不了）。

**核验结论（量化）**：18 篇文献、4 处真实错误（**错误率 22%**）、全部修正。
这为论文核心论点提供了本项目自身的经验证据：**LLM 生成的引用信息不可信，
必须外部核验**。

**人工核验状态**：✅ 18/18 全部完成官方来源核验（本轮为全量强核验，而非抽查）。

---

## 阶段 3：写作（含 3 次自我修正）

**迭代 1**：AI 初稿将 PRM/ORM 对比写为"受控实验结论" → **自我修正**：Lightman
原文明确说明大规模 ORM/PRM 训练数据不同、**非受控比较**，论文改为引用作者自己的
限定说明（paper.tex §7 "Boundary conditions"）。核验时已在官方摘要中确认此限定
真实存在。

**迭代 2**：Minerva 在 MATH 上的准确率记忆值（50.3%）无法在小数位精度上完成
二次核验 → **降级处理**：正文只写 "surpasses 50\% accuracy on MATH" 并挂引用，
不写小数点精度；**未核验的精确数字一律不进入论文**。

**迭代 3**：AlphaProof 的"约 8000 万条自动形式化训练语句"与"IMO 2024 牌级表现"来自
Nature 官方摘要，写入论文时注明 "as published"。

**人工核验状态**：所有数字均标注出处；跨论文数字不可比性在 §7 中显式声明。

---

## 阶段 4：LaTeX 排版与编译验证 ⚠️ 真实失败与修复记录

1. **失败 A（环境缺失）**：本机首次编译报
   `! LaTeX Error: File 'microtype.sty' not found.` → **Fatal error, no PDF produced**。
   这是**红线级问题**（"不可编译 → 技术实现 ≤ 5"）。
2. **诊断**：用 `kpsewhich` 逐项检查宏包，发现 natbib / tikz / hyperref / booktabs
   均存在，**仅 microtype 缺失**；`tlmgr install microtype` 因网络受限超时（SIGTERM）。
3. **修复决策**：microtype 仅提供微排版优化（字符间距、字体扩展），**与论文内容、
   引用、图表、公式均无关**。故直接**移除该依赖**，使文档在任意标准 TeX 发行版下
   均可编译，同时提升可移植性（评审环境友好）。
4. **修复后真机编译（完整四步链）**：
   ```
   pdflatex -interaction=nonstopmode -halt-on-error paper.tex   # pass 1  → exit 0
   bibtex paper                                                 # 处理参考文献 → exit 0
   pdflatex -interaction=nonstopmode paper.tex                  # pass 2  → exit 0
   pdflatex -interaction=nonstopmode paper.tex                  # pass 3  → exit 0
   ```
   **最终产物 `paper.pdf`：9 页，无未定义引用、无 error**；仅剩 1 条无害提示
   （`` `h' float specifier changed to `ht' ``）。用 pypdf 解析确认：
   页数 = 9，标题/摘要/表格/参考文献编号（如 [11,12]）均正确渲染。
5. **设计决策**：论文不用任何本地图片，图 1、图 2 均为 **TikZ 内联绘制**，
   保证单目录自包含可编译；引用采用 natbib + unsrtnat（数字式）。

**人工核验状态**：✅ 编译结果可复现（见上四条命令）；产物 paper.pdf 已随包交付。

---

## 阶段 5：日志与 AAR

本文件与 AAR/AAR复盘.md 同步撰写。撰写原则：

- 只记**真实发生**的迭代、失败、修正；
- AI 误导案例单独编号（见 AAR 维度 5），共 4 个真实案例；
- 未核验事项显式标注，不假装全部完成。

---

## 附 1：AI 使用工作流小结

| 环节 | AI 角色 | 人工/独立核验角色 |
|---|---|---|
| 选题定位 | 分析大纲、提出原创化改造 | 用户确认方向 |
| 文献检索 | 生成候选清单与 BibTeX | **联网逐条访问官方页核验（发现 4 处错误）** |
| 论证 | 起草观点与结构 | 数字全部溯源原文、不可比性显式声明 |
| 写作 | 初稿 + 自我修正 3 轮 | 事实性声明逐条回查 |
| 排版 | 生成 TikZ 图、处理 microtype 缺失 | **真机编译验证（四步链，exit 0）** |
| 复盘 | 起草 AAR 骨架 | 失败案例均来自本会话真实事件 |

## 附 2：本挑战自带的"元证据"

论文的核心论点是"AI 生成的中间结论不可信，必须引入核验层"。本项目在**自身的
文献准备环节**上独立验证了这一点：AI 生成的 18 条引用里，**4 条是错的（22%）**，
且错误全部以**高置信、无犹豫**的语气给出。一个简单的核验协议（访问官方页）
即拦截了全部 4 处错误——**这就是论文论点在真实工作流中的一次对照实验**。

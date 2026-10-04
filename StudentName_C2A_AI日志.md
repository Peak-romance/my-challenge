# AI 生成日志 / AI Generation Log

**作者 / Author:** StudentName  
**挑战 / Challenge:** C2A — Track 2 Metacognition（ΔE-Bench）  
**日期 / Date:** 2026-10-04

---

## 一、使用的工具 / Tools Used

- **WorkBuddy AI 智能体**（agent loop 工作模式）：论文资料解析、文献检索核实、提案撰写与迭代、benchmark 原型代码生成与调试
- **Web 检索**（由 AI 智能体调用）：文献编号与结论核实
- **Python 3.13**：原型代码离线验证

## 二、论文精读 / Paper Analysis

- **方法**：将资料包中的 DeepMind 框架摘要 PDF（4 页）与 CHALLENGE.md 全文喂给 AI，要求提取：
  1. 十大认知能力的定义与八基础+两复合结构；
  2. 五个评估缺口赛道及各自的核心问题；
  3. 三阶段评估协议（认知评估 → 人类基线 → 认知画像）；
  4. 元认知与幻觉的关系表述。
- **关键提取**：论文将元认知定义为"对自身认知过程的监控与理解"，并明确其为幻觉的关键根源——这成为提案动机的第一句话；三阶段协议中"人类基线"部分被改造成提案第 3 节。
- **KSTAR 对齐**：由 AI 将挑战文档中的 KSTAR 表格（ΔE + 置信度校准）与 Nelson & Narens 的监控时间点理论做映射，发现"作答前预测"（R̂\_E）在现有 LLM 评测中缺位——这是选题的直接来源。

## 三、文献调研与核实 / Research & Verification

**检索策略（AI 执行，共 5 轮）：**

1. `Kadavath "Language Models (Mostly) Know What They Know" arXiv 2207.05221` → 确认编号、作者、P(True)/P(IK) 双概念，并捕获关键坦白："struggle with calibration of P(IK) on new tasks"（成为 v2 的核心论据）；
2. `Yin 2023 "Do Large Language Models Know What They Don't Know" SelfAware` → 确认 ACL 2023 Findings、arXiv:2305.18153、1032 道不可答 + 2337 道可答题的构成；
3. `Tian "Just Ask for Calibration" EMNLP 2023` → **发现并纠正了一个凭记忆产生的错误**：AI 初稿把编号记成 arXiv:2205.14334，检索确认为 **arXiv:2305.14975**——该错误未进入任何提交文件；
4. `Kuhn Farquhar "Semantic Uncertainty" + SimpleQA` → 确认 ICLR 2023 Spotlight、arXiv:2302.09664；SimpleQA 确认为 OpenAI、4326 题、三态判分、模型普遍过度自信；
5. 经典心理学文献（Flavell 1979、Nelson & Narens 1990、Kruger & Dunning 1999、Moore & Healy 2008、Erev et al. 1994）按作者+年份+期刊引用，不标注未核实的编号。

**结果**：最终参考文献 13 条，全部真实可查；引用处均写明"论文说了什么"，未发现转述失真。

## 四、方案构思与提案撰写 / Ideation & Writing

**迭代 1（v1，CalibQA 初稿）**：

- Prompt 要旨："Track 2 元认知，设计一个测校准与知识边界的 benchmark，四部分结构，800–1500 字"；
- AI 产出 v1：置信度输出 + ECE + 不可答题拒答率 + 人类过度自信基线。

**迭代 2（结构化自评 → v2）**：

- 用 rubric 五维度对 v1 做体检，发现四个实质弱点（详见 v2 文末迭代说明表）：构念效度不足（语言化置信度≈风格）、静态数据污染、ECE 单指标混淆校准与判别、拒答率可被恒拒答刷分；
- 每个弱点对应一个设计动作：D2 新颖域（内容控制）、D3 程序化伪事实、ECE+AUC+d′+MG 组合、d′ 防 Goodhart。

**迭代 3（可行性闭环）**：

- 要求 AI "证明它一周内能做出来"→ AI 直接产出可运行原型并用两个不同人格的模拟模型离线跑通，验证了"指标组合能区分过度自信模型与校准良好模型"的最小闭环。

**人工参与（预填写，提交者确认后生效）：**

- 赛道选择（Track 2）与差异化决策（避开官方示例 Track 1）由提交者确认；
- 人类基线的预期数字（如"过度自信 +10~15pp"）来自文献，需提交者按预测试数据修订；
- 提交前需重命名文件（StudentName → 姓名拼音）并通读全文。

## 五、Benchmark 原型中的 AI 使用 / Prototype Development

- **AI 生成**：`deltae_bench/` 全部四个模块（generator / protocol / models / scoring）、CLI、README；
- **AI 验证**：离线自检（`--selftest`：完美校准 ECE≈0、完美排序 AUC=1、d′ 合理性断言）+ 双模拟模型对比运行，全部通过后写入 results/；
- **设计约束**：零第三方依赖（纯标准库），保证评分环境可复现。

## 六、手动步骤说明 / Manual Steps Justification（反向举证）

| 手动步骤          | 为什么没用（不该用）AI                      |
| ------------- | --------------------------------- |
| 确认赛道与放弃官方示例方向 | 涉及与同侪撞题的博弈判断，属于提交者策略，AI 只能提示风险    |
| 人类基线数字的最终确定   | 文献数字只是预期，必须由真实预测试数据替换——AI 无法替人填问卷 |
| 提交署名与文件重命名    | 身份信息属于提交者本人                       |
| 对引用文献的最终通读    | AI 已做检索核实，但按学术规范，署名者对每条引用负最终责任    |

## 七、AI 段位自评 / AI Usage Level

**🟣 驾驭**——本次工作流不是"一句话生成"，而是设计了一条带验证环节的流水线：资料解析 → 检索核实（含错误纠正回路）→ v1 → rubric 体检 → v2 → 原型离线验证。AI 负责执行与生成，人负责方向、取舍与署名责任。弱点：人类基线环节还是纸面计划，尚未跑真实预测试（这正是 C9 阶段的第一项任务）。

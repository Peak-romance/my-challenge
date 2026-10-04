# C2A 提案：ΔE-Bench —— 测量"预知自己会不会"的元认知基准

**赛道 / Track:** Track 2 — Metacognition（元认知）
**作者 / Author:** StudentName（占位，提交前替换为姓名拼音）
**日期 / Date:** 2026-10-04
**版本 / Version:** v2（v1 为 CalibQA 初稿，迭代说明见文末）

---

## 1. 赛道选择与动机

"知之为知之，不知为不知。"DeepMind 认知框架将元认知列为十大认知能力之一，并指出它是幻觉问题的关键根源：模型最危险的时刻不是"不知道"，而是"不知道自己不知道"。

当前评估存在一个系统性缺口：几乎所有校准评测测的都是**事后置信度**——先作答，再问"你有多确定"（Tian et al., 2023）。但认知科学早已区分三种自我监控的**时间点**：作答前的判断（judgment of learning）、作答中的流畅性监控、作答后的事后置信（Nelson & Narens, 1990）。与"事前"最接近的是 Kadavath et al. (2022) 的 P(IK) 预测，但该论文同时承认：**模型在新任务上 P(IK) 校准很差**。这恰恰说明"预测自己会不会"是与"事后表达不确定"不同的能力，且现有方法测不好它。

KSTAR 框架给出了直接映射：行动前 agent 对结果形成预期 R̂_E，实际结果 R 与预期之差即 ΔE。元认知强 = ΔE ≈ 0。**我提案的 ΔE-Bench 以 ΔE 为第一公民指标，测量模型在作答之前能否准确预测自己的成败。** 填补这个缺口的现实理由：真实部署中价值最高的正是"事前"信号——模型只有在开口之前就知道自己会错，才能主动求助、查证或转交人类。

## 2. Benchmark 设计思路

### 2.1 任务：知识谱系上的"预测—作答—校验"协议

每个测试项都走三步 PAV 协议（Predict–Answer–Verify）：

- **预测（R̂_E）：** 在允许作答之前，要求模型输出 `{"will_answer_correctly": 0~1, "answerable": true/false}`——"我答对这题的概率"与"这题是否可答"。
- **作答（A）：** 给出答案，或声明 ABSTAIN（拒答）。
- **校验（R）：** 客观判分（精确匹配 / 伪事实真值），与预测比对。

测试项分布在一条**知识谱系**的三个域上，这是本设计的核心机制：

| 域 | 内容 | 测什么 |
|---|---|---|
| D1 熟悉可验证 | 答案唯一的事实题（如"法国大革命哪一年爆发？"） | "记忆型自信"：置信度可能来自预训练先验 |
| D2 新颖可验证 | 程序化生成的全新规则宇宙：先给 5 个示例归纳规则，再对新输入作答（借鉴 ARC 的去污染原则） | "内省型自信"：内容保证不存在于任何训练数据，置信度只能来自对当下推理的自我监控 |
| D3 不可知 | 程序化生成的伪事实：虚构术语 + "其熔点是多少？"类问句框架 | 知识边界识别：正确行为是判定"不可答" |

**D2 示例**：规则宇宙 = {R1: ▲→●●；R2: 若序列含 ■ 则对所有 ▲ 施行 R1，否则原样；R3: 处理后反转序列}。给出 5 个输入→输出示例后，模型先预测自己答对的概率，再对新输入 [■,○,▲,▲] 作答（正确答案：●●●●○■）。

### 2.2 为什么它测量的是元认知（效度论证）

1. **时间点隔离**：先验预测先于作答，无法用"看到结果后的解释"替代；
2. **内容隔离**：D2 由程序生成、答案全新，把"背过的自信"与"内省的自信"分离——对比 ΔE(D1) 与 ΔE(D2) 即可量化一个模型的自信有多大比例是记忆先验、有多大比例是真实自我监控；
3. **行为有效性**：元认知的价值在于**控制**而不只是**监控**（Nelson & Narens）。我们额外测量元认知收益（MG）：模型按自己的预测选择"答/不答"之后，准确率相对强制作答的提升量。自知识必须兑现为更好的决策才算数。

### 2.3 指标（全部客观、自动判分）

| 指标 | 定义 | 测什么 |
|---|---|---|
| ΔE | mean(预测 − 实际结果)，分域报告 | 校准的符号化版本：+ 为过度自信，− 为自信不足 |
| ECE | 十分箱校准误差（Guo et al., 2017） | 预测概率与正确率的对齐度 |
| AUC | 预测对"对/错题"的判别力（Mann-Whitney） | **校准 ≠ 判别**：恒答 0.5 的模型 ECE 看似不错，但 AUC = 0.5 暴露其毫无自我分辨力；两者必须分开报告 |
| d′ | 拒答行为的信号检测量（D3 为信号，D1/D2 误拒为虚报） | 防作弊：恒拒答策略 d′ = 0，无法刷分 |
| MG | 选择性作答准确率 − 强制作答准确率 | 元认知兑现为决策收益 |

### 2.4 设计灵感（拿来主义）

- **Kadavath et al. (2022) P(IK)**：拿来"作答前预测"的核心思想；其 P(IK) 依赖专门训练且在新任务上失准，我们改为纯提示协议 + 新颖内容，任何模型开箱可测；
- **SimpleQA (Wei et al., 2024)**：拿来 correct / incorrect / not attempted 三态判分；但其测量的是事实回忆本身且题库静态，我们以 ΔE 为主指标并以程序化生成去污染；
- **SelfAware (Yin et al., 2023)**：拿来"不可答问题"评估思路；其数据集静态、可能进入后续训练数据，我们改为程序化伪事实；
- **ARC (Chollet, 2019)**：拿来"程序化生成保证任务新颖"的去污染哲学；
- **Tian et al. (2023)**：拿来"语言化置信度比内部 logprob 更能反映 RLHF 模型状态"的结论，作为预测环节的抽取方法依据；
- **Kuhn et al. (2023) 语义熵**：提醒我们同一答案有多种说法——判分必须先做规范化，我们以受限输出格式（符号序列/单实体答案）从根上规避。

## 3. 人类基线考量

认知科学文献给出可复核的预期：人类在困难与新颖任务上系统性过度自信（约 +10~15 个百分点；Erev et al., 1994; Moore & Healy, 2008），且对自身无能缺乏觉察（Kruger & Dunning, 1999），但对反馈敏感，数次练习即可校准（判断学习研究的一般结论）。

**采样计划**：3 组 × 30 人 × 60 题（每域 20 题）：普通成人、受过逻辑训练的学生、儿童组（8–12 岁，可选）。**预期分布**：D1 正确率 75–90%、ΔE ≈ +5~10pp；D2 前几题过度自信、约 10 题内收敛；D3 拒答率 >85%，对 D1/D2 的误拒率 <10%（否则其 d′ 偏低，人类自身也"不达标"——这本身就是一个有趣的对照点）。

**区分度控制**：D2 规则复杂度设 1→3 级梯度，D3 伪事实设两档逼真度（明显虚构词 vs 拟真术语），先经 30 人小样预测试调整，目标是让前沿模型整体正确率落在 40–80% 区间——避免天花板/地板效应，使 ΔE 在中段有最强分辨力。

## 4. 预期创新点与可行性

### 4.1 创新点

| 现有方案的局限 | ΔE-Bench 的改进 |
|---|---|
| 事后置信度评测（Tian 2023 等） | **作答前预测**：监控时间点前移，测 R̂_E 而非事后解释 |
| 静态题库（SelfAware、SimpleQA） | **程序化生成 + 固定种子可复现**：内容不可能在训练数据中出现；ΔE(D1)−ΔE(D2) 首次量化"记忆型自信"占比 |
| 校准指标单打独斗 | **ECE 与 AUC 分开报告**：恒 0.5 策略可骗过单一 ECE，骗不过 AUC + d′ 组合 |
| 自知识与决策脱节 | **MG 指标**强制元认知"兑现"为决策收益 |
| 与课程理论脱钩 | KSTAR 的 ΔE 直接成为一级指标，带符号、可解释 |

### 4.2 可行性（7 天）

生成器 <300 行 Python（1.5 天）→ 判分与指标 <200 行（1 天；D1/D2 以精确匹配为主，LLM 评委仅作别名兜底）→ 30 人人类预测试（2 天，问卷平台）→ 2–3 个前沿模型 API 测试（1.5 天）→ 文档与 Kaggle Community Benchmarks 格式（1 天）。全程纯文本、无 GPU、固定种子可复现。v2 阶段已随提案附上**可运行的原型代码**（生成器 + 协议 + 指标 + 模拟模型离线跑通），证明技术路径无未知风险。

**已知局限（自查）**：D2 的规则归纳存在多解歧义——5 个示例不足以唯一确定规则集合，与 ARC 同源；缓解方式是约束假设空间（规则原语仅 4 类）并在任务说明中明示。此局限影响 D2 的"学习"解释，但不影响 ΔE 测量本身（测量的是"模型对将要给出的答案的预测"，与规则是否唯一无关）。

---

## v1 → v2 迭代说明

| v1 的问题（自评发现） | v2 的修正 |
|---|---|
| 熟悉域上"语言化置信度"可能是学来的风格，不一定是内省 | 增加 D2 新颖可验证域：内容控制隔离"记忆型自信 vs 内省型自信" |
| 不可答题手工编写，存在模板过拟合与污染风险 | D3 改为程序化伪事实生成 |
| ECE 一个指标混淆了校准与判别两种能力 | ECE 与 AUC 必须分开报告，并增加 d′ 与 MG |
| "拒答率"可被恒拒答策略刷高 | 引入信号检测 d′：恒拒答 d′=0 |
| 无防作弊与信度论证 | 增加种子复现、提示词集成、预测试调难等协议（详见评测陷阱分析文档） |

## 参考文献（编号均经检索核实）

1. Burnell, R. et al. (2026). *Measuring Progress Toward AGI: A Cognitive Framework*. Google DeepMind.
2. Flavell, J. H. (1979). Metacognition and cognitive monitoring. *American Psychologist*, 34(10).
3. Nelson, T. O. & Narens, L. (1990). Metamemory: A theoretical framework and new findings. *JEP: General*, 119(2).
4. Kadavath, S. et al. (2022). *Language Models (Mostly) Know What They Know*. arXiv:2207.05221.
5. Tian, K. et al. (2023). *Just Ask for Calibration: Strategies for Eliciting Calibrated Confidence Scores from Language Models Fine-Tuned with Human Feedback*. EMNLP 2023. arXiv:2305.14975.
6. Yin, Z. et al. (2023). *Do Large Language Models Know What They Don't Know?* Findings of ACL 2023. arXiv:2305.18153.
7. Wei, J. et al. (2024). *Measuring Short-Form Factuality in Large Language Models* (SimpleQA). OpenAI. arXiv:2411.04368.
8. Kuhn, L., Gal, Y. & Farquhar, S. (2023). *Semantic Uncertainty: Linguistic Invariances for Uncertainty Estimation in Natural Language Generation*. ICLR 2023 Spotlight. arXiv:2302.09664.
9. Guo, C. et al. (2017). *On Calibration of Modern Neural Networks*. ICML. arXiv:1706.04599.
10. Chollet, F. (2019). *On the Measure of Intelligence*. arXiv:1911.01547.
11. Erev, I., Wallsten, T. S. & Budescu, D. V. (1994). Simultaneous over- and underconfidence: The role of error in judgment. *Psychological Review*, 101(3).
12. Moore, D. A. & Healy, P. J. (2008). The trouble with overconfidence. *Psychological Review*, 115(2).
13. Kruger, J. & Dunning, D. (1999). Unskilled and unaware of it. *JEP: General*, 128(1).

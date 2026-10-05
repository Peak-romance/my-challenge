# 作业解答 output 说明 — C4C 作业自动求解与排版

作者：谢嘉乐 (xujiale)　　日期：2026-10-05

> **成品只有一份：`all_homework.pdf`（35 页，7 组作业全在里面，带书签目录）。**
> 打开 PDF 阅读器的侧边书签栏即可在各作业间跳转。

## 命名规范

本目录所有产物统一为 **`<组>_homework.<扩展名>`**：

| 组标识 | 对应作业 |
|---|---|
| `la` | 线性代数 |
| `ode` | 常微分方程 |
| `sample` | 示例作业 |
| `ws3` | Berkeley 卷 3 · 切线与 ε-δ |
| `ws4` | Berkeley 卷 4 · 极限 |
| `ws4_mock` | 卷 4 重跑（LLM 兜底 mock） |
| `edge` | 边界用例 |
| `all` | 上述 7 组合并的合集 |

---

## 一、成品（本目录顶层）

| 文件 | 内容 |
|---|---|
| `all_homework.pdf` | **35 页 · 7 组作业合并一册 · 527 KB** |
| `all_homework说明.md` | 本文件 |

### 合集书签（页码）

| 书签 | 起始页 | 题数 | 解出 |
|---|---|---|---|
| 线性代数 | p.1 | 10 | **10** |
| 常微分方程 | p.7 | 6 | **6** |
| 示例作业 | p.10 | 10 | **10** |
| 微积分作业3 · 切线与 ε-δ | p.15 | 8 | **8** |
| 微积分作业4 · 极限 | p.21 | 10 | 9 |
| 微积分作业4 · 极限（LLM 兜底 mock） | p.27 | 10 | **10** |
| 边界用例 | p.33 | 7 | 5 |

**合计：60 题，解出 58，解出率 96.7%；有人工标准答案的 16 题 16/16 全对。**

> **关于 2 题未解**：不是能力不足跳过，是**诚实失败**——坏 LaTeX 输入报「无法提取方程」、
> 奇异矩阵报「det(A)=0，矩阵不可逆」。PDF 里都标注了原因，没有编造答案。

---

## 二、为什么有 7 组？（不是重复，是 6 种不同作业）

| 作业来源 | 内容 | 是否重复 |
|---|---|---|
| `la_homework.md`（自编） | 行列式 / 逆 / 特征值 / 秩 / 方程组 | 独立 |
| `ode_homework.md`（自编） | 一阶线性 / 二阶常系数 / 非齐次 ODE | 独立 |
| `sample_homework.md`（示例） | 导数 / 积分 / 化简 | 独立 |
| `baseline_worksheet3.md` | Berkeley Math 1A 卷 3：切线 & ε-δ | 独立 |
| `baseline_worksheet4.md` | Berkeley Math 1A 卷 4：极限 | 独立 |
| 边界用例集 `edge_cases.md` | DNE / 坏输入 / 奇异矩阵 | 独立 |
| **worksheet4 重跑（开 LLM mock）** | 同上卷 4，用于验证兜底链路 | **与卷 4 同源** |

也就是说：6 种不同内容 + 1 次重复运行（卷 4 跑了两遍，一次纯确定性 9/10、
一次开 LLM 兜底 10/10，用来证明兜底链路端到端可用）。

7 份独立分册仍保留在 `分册备份\`（`la_homework.pdf`、`ode_homework.pdf`、
`sample_homework.pdf`、`ws3_homework.pdf`、`ws4_homework.pdf`、
`ws4_mock_homework.pdf`、`edge_homework.pdf`），需要单独提交某一科时从那里取。

---

## 三、过程目录 `*_run\`（可追溯性证据，不用翻）

每组合并前的中间产物在同名目录：`1_ingested.json`（Stage1 摄入）、
`2_parsed.json`（Stage2 分类）、`3_solutions.json`（Stage3 解答与验证）、
`<组>_homework.tex`（LaTeX 源文件，如 `la_homework.tex`）、
`ai_usage_log.jsonl`（AI 事件日志）、`run_summary.json`（本次统计）。
`la_run\`、`ode_run\` 另含
`check_report.md`、`groundtruth_report.md`（人工标准答案对照）。

| 过程目录 | 对应合集中的段落 |
|---|---|
| `la_run\` | 线性代数 |
| `ode_run\` | 常微分方程 |
| `sample_run\` | 示例作业 |
| `ws3_run\` | 微积分作业3 |
| `ws4_run\` | 微积分作业4 |
| `ws4_mock_run\` | 微积分作业4（mock） |
| `edge_run\` | 边界用例 |

---

## 四、怎么重跑

```powershell
cd E:\C4C\homework-solver
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe `
    scripts\pipeline.py test_cases\la_homework.md ..\output\la_run --compile
```

换作业改 `test_cases\` 下的文件名，换输出目录改 `la_run` 即可。
参数与排错见 `homework-solver\USAGE.md`。

> 流水线默认产出的文件名固定为 `<输出目录>\homework.tex` / `homework.pdf`。
> 为了不让 7 个同名文件看起来像重复，本目录已按组统一重命名：
> `.tex` → `<组>_homework.tex`，分册 `.pdf` → `<组>_homework.pdf`，
> 7 份再合并为顶层的 `all_homework.pdf`。
> 重跑流水线时仍会生成默认的 `homework.tex` / `homework.pdf`，
> 这是程序行为，需要长期保留时请手动改名为 `<组>_homework.*`。

---

## 五、核验方式

- **自动验证**：`verify.py` 用残差法独立复核（方程代根、积分求导还原、定积分数值对比、
  极限两侧采样、det(A−λI)≈0、A·A⁻¹≈I、ODE 解代回），结果印成 PDF 每题末尾的 ✓/✗/− 徽标。
- **人工对照**：`la_run\check_report.md` 与 `ode_run\check_report.md` 是与
  **人工独立推导的标准答案**逐题比对的报告，结论 16/16 全对。
- **可复现**：所有数据与耗时写在各 `run_summary.json`，重跑结果一致。

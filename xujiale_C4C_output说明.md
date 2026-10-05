# output 交付说明 — C4C 作业自动求解与排版

作者：谢嘉乐 (xujiale)　　日期：2026-10-05

> **本目录顶层就是成品 PDF**，不需要往下翻任何文件夹。
> 下方的 `*_run/` 只是每份作业的过程留痕（中间 JSON、LaTeX 源文件、运行日志），
> 想看结果直接看本文件下面那张表里的 PDF 即可。

---

## 一、成品 PDF（7 份，全在本层）

| PDF 文件 | 作业内容 | 题数 | 解出 | 页数 | 大小 |
|---|---|---|---|---|---|
| `xujiale_C4C_output_线性代数作业解答.pdf` | 行列式 / 逆矩阵 / 特征值 / 秩 / 方程组 | 10 | **10** | 6 | 54 KB |
| `xujiale_C4C_output_常微分方程作业解答.pdf` | 一阶线性 / 二阶常系数 / 非齐次 ODE | 6 | **6** | 3 | 47 KB |
| `xujiale_C4C_output_示例作业解答.pdf` | 综合示例（导数 / 积分 / 化简） | 10 | **10** | 5 | 59 KB |
| `xujiale_C4C_output_微积分作业3_切线与εδ.pdf` | Berkeley Math 1A Worksheet 3（基线回归） | 8 | **8** | 6 | 63 KB |
| `xujiale_C4C_output_微积分作业4_极限.pdf` | Berkeley Math 1A Worksheet 4（基线回归） | 10 | 9 | 6 | 74 KB |
| `xujiale_C4C_output_微积分作业4_极限_LLM兜底mock.pdf` | 同上，但启用 LLM 兜底 mock 链路 | 10 | **10** | 6 | 78 KB |
| `xujiale_C4C_output_边界用例解答.pdf` | 边界：`|x|/x`→DNE、振荡→DNE、坏 LaTeX、奇异矩阵 | 7 | 5 | 3 | 59 KB |

**合计：60 题，解出 58，解出率 96.7%；有人工标准答案的 16 题 16/16 全对。**

PDF 里每份都包含：页眉（课程 / 姓名 / 日期）、逐题过程与加框答案、
文末汇总表（含 ✓/✗/− 独立验证徽标）、AI 使用声明。

> **关于 2 题未解**：不是能力不足而跳过，是**诚实失败**——
> 坏 LaTeX 输入报「无法提取方程」，奇异矩阵报「det(A)=0，矩阵不可逆」。
> 二者都在 PDF 里明确标注了原因，没有编造答案。

---

## 二、PDF 与过程目录的对应关系

每份 PDF 的过程产物在同名的 `*_run/` 目录里，文件名一一对应：

| PDF | 过程目录 | 该目录内容 |
|---|---|---|
| 线性代数作业解答 | `la_run/` | + `check_report.md`、`groundtruth_report.md`（标准答案对照） |
| 常微分方程作业解答 | `ode_run/` | + `check_report.md`、`groundtruth_report.md` |
| 示例作业解答 | `sample_run/` | 基础四件套 |
| 微积分作业3 | `ws3_run/` | 基础四件套 |
| 微积分作业4 | `ws4_run/` | 基础四件套 |
| 微积分作业4（mock） | `ws4_mock_run/` | 基础四件套（含 LLM mock 调用日志） |
| 边界用例 | `edge_run/` | 基础四件套 |

「基础四件套」= `1_ingested.json`（Stage1 摄入）+ `2_parsed.json`（Stage2 分类）
+ `3_solutions.json`（Stage3 解答与验证）+ `run_summary.json`（本次运行统计），
外加 `homework.tex`（LaTeX 源文件，可上传 Overleaf）与 `ai_usage_log.jsonl`（AI 事件日志）。

---

## 三、这些 PDF 是怎么重跑出来的

```powershell
cd E:\C4C\homework-solver
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe `
    scripts\pipeline.py test_cases\la_homework.md ..\output\la_run --compile
```

把 `la_homework.md` 换成 `test_cases/` 下任一作业，`la_run` 换成你喜欢的输出目录即可。
参数与排错见 `homework-solver\USAGE.md`。

> 流水线默认产出的是 `<输出目录>\homework.pdf`；
> 为了便于查阅，本目录已把 PDF 上提一层并按内容重命名，源文件仍留在各自的 run 目录。

---

## 四、核验方式

- **自动验证**：`verify.py` 用残差法独立复核（方程代根、积分求导还原、定积分数值对比、
  极限两侧采样、det(A−λI)≈0、A·A⁻¹≈I、ODE 解代回），结果直接印在 PDF 的徽标里。
- **人工对照**：`la_run/check_report.md` 与 `ode_run/check_report.md` 是与
  **人工独立推导的标准答案**逐题比对的报告，结论为 16/16 全对。
- **可复现**：所有数据与耗时都写在各目录的 `run_summary.json`，重跑结果一致。

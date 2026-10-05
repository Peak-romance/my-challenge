# XUJIALE_C4_demo —— challenge-auditor 真实运行记录（Live Demo）

> 本文件是 **live demo 记录**（挑战允许"视频、截图、或 live demo"三选一，此处选 live demo：全部输出为真实运行产物，命令与文件均可复现）。
> 运行环境：Windows + Python 3.13（audit.py 兼容 3.8+，纯标准库）
> 运行方式：从 `.skill` 包解压后直接运行包内脚本——与群友安装后的使用路径一致。

---

## 案例一：审计一个故意带缺陷的模拟 C2 提交

### 为什么这样设计

模拟文件夹 `demo/模拟_C2提交_测试用/` 里埋了 6 类缺陷，覆盖脚本全部检测路径：

| # | 预埋缺陷 | 应触发的检测 |
|---|---|---|
| 1 | demo 交付物完全没有 | missing_artifacts（critical） |
| 2 | `王五_C2_论文大纲.md` = 0 字节 | 空文件 → 交付物 weak（按缺失处理） |
| 3 | `王五_C2_AI日志.md` 仅 29 字符 | one_shot_ai（warning） |
| 4 | `李四_C2_随手笔记.md` 混入 | 姓名前缀一致性警告 |
| 5 | `王五_C2_总结.md` 全是"TODO 待补充" | 占位壳（placeholder_shell）检测 |
| 6 | `王五_C2_paper.md` + `_v1` 并存 | 多版本归组提醒 |

### 执行命令（原样可复现）

```bash
unzip -o XUJIALE_C4_challenge-auditor.skill -d skill-installed
python skill-installed/challenge-auditor/scripts/audit.py \
    --folder "E:/C4/demo/模拟_C2提交_测试用" \
    --author "王五" --out "E:/C4/demo/audit_result.json"
```

### 脚本实际输出（audit_result.json 摘录）

```
模式: elite20 ｜ 挑战: C2 AI for Math 论文（模拟测试用）
交付物: [('论文大纲','weak'), ('paper.md','ok'), ('references.bib','ok'),
         ('demo','missing'), ('AI日志','weak')]
红旗: [('missing_artifacts', True, critical),
       ('no_ai_log', False, clear),
       ('one_shot_ai',  True, warning)]
AI日志: 最长 29 字符 < 阈值 800 ｜ 迭代标记词: {}
警告: 姓名前缀不一致 ['李四_C2_随手笔记.md']；多版本 {'王五_C2_paper.md': ['无标记','v1']}
空文件: ['王五_C2_论文大纲.md']   占位壳: ['王五_C2_总结.md']
```

**6 类预埋缺陷全部命中，零误报。**

### LLM 层输出

按 SKILL.md 工作流，LLM 读取脚本 JSON + 抽查文件内容 + 对照 `references/rubric-guide.md` 锚点，产出完整 7 节报告：

📄 **`demo/审计报告_模拟C2提交.md`**

报告要点：预估总分 20–43/100；两条红旗触发；P0 行动清单三件事（补 demo、重写 AI 日志、填大纲）。每个结论都标注了证据来源（文件名 + JSON 字段）。

---

## 案例二：自审本 C4 提交（dogfooding，共 3 轮）

### 第 1 轮（提交尚不完整时）

```bash
python audit.py --folder "E:/C4" --author "XUJIALE" \
    --deliverables "skill说明,.skill,教学说明,demo,AI日志,README" \
    --out "E:/C4/demo/audit_result_自审.json"
```

```
交付物: skill说明->ok  .skill->ok  教学说明->ok
        demo->missing ❌   AI日志->ok   README->missing ❌
红旗: missing_artifacts=True  no_ai_log=False  one_shot_ai=False
AI日志: 4657 字符 ｜ 迭代标记 {'失败':11, '迭代':4, 'v1':4, '报错':3, 'prompt':3, 'v2':2}
```

**技能在提交未完成时准确抓到了 2 个缺口**（demo 记录和 README 当时还没写）——自检工具在自己的提交上抓到自己的缺失，这是比任何宣传都硬的正确性证据。同时量化确认了 AI 日志的迭代证据密度（失败×11），one_shot_ai 正确未触发。

### 第 2 轮（补齐两个文件后）——抓到了技能自己的 bug

补写 `XUJIALE_C4_demo.md` 和 `README.md` 后复审，demo 转绿，**但 README 仍报 missing**。排查：`README.md` 明明在文件夹里。根因是脚本自身缺陷——官方资料白名单误把 `readme.md` 当成官方文件排除了扫描，而 README 恰恰是 rubric 要求检查的提交物。

**修复（v1.2）**：将 `readme.md` 移出白名单，重新打包，并对模拟案例做回归（结果与 v1.1 完全一致，确认无副作用）。

> 这一步让整个 demo 闭环变得完整：**审计工具在自己的提交上先抓到环境缺陷（缺文件），又抓到自身缺陷（白名单误伤）**——自检的价值不只是查别人。

### 第 3 轮（v1.2 最终版）

```bash
python skill-installed/challenge-auditor/scripts/audit.py \
    --folder "E:/C4" --author "XUJIALE" \
    --deliverables "skill说明,.skill,教学说明,demo,AI日志,README" \
    --out "E:/C4/demo/audit_result_自审v2.json"
```

实际输出——**交付物 6/6 全 ok，三红旗全绿**：

```
交付物: [('skill说明','ok'), ('.skill','ok'), ('教学说明','ok'),
         ('demo','ok'), ('AI日志','ok'), ('README','ok')]
红旗: [('missing_artifacts', False), ('no_ai_log', False), ('one_shot_ai', False)]
README匹配: ['README.md']
```

两处说明（有意为之的决策）：
- `demo/` 下 3 个 `audit_result*.json` 未按 `姓名_C4_` 命名——它们是审计过程的机器输出（证据文件），按用途命名更利于复现，报告注明而非机械改名；
- `demo/` 里的模拟测试文件夹含"王五/李四"文件名——那是测试夹具，不是本提交的文件（在两层子目录内，默认扫描深度外，不影响自审结果）。

📄 对应 LLM 层报告：**`demo/审计报告_自审C4提交.md`**

---

## Demo 结论

| 验证点 | 证据 |
|---|---|
| 可安装 | .skill 为标准 ZIP 结构（顶层 challenge-auditor/SKILL.md），解压即用 |
| 可执行 | 脚本从包内路径直接运行成功，零依赖 |
| 可验证 | 6 类预埋缺陷全部命中、零误报；自审三轮状态机：2×❌ → 抓到自身白名单 bug（v1.2 修复） → 6×✅ 三红旗全绿 |
| IO 明确 | 输入一个文件夹路径，输出 JSON 事实 + 7 节 Markdown 报告 |

**复现指引**：所有命令原样保留在上文；模拟文件夹、两份 JSON、两份审计报告都在 `demo/` 目录内。

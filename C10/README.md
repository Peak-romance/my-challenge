# C10 · 第二大脑（Second Brain）

长期智能体：五层架构（接口 / 工具 / 循环 / 技能 / 记忆）+ KSTAR 四层记忆 + 技能演化机制。
零第三方依赖，Python 3.10+。

## 快速开始

```bash
cd D:\C10
python agent.py --demo              # 端到端演示（7 个任务）
python agent.py "生成今日简报"       # 单次任务
python agent.py                     # 交互模式
python tests/test_smoke.py          # 12 项契约测试
python agent.py --serve 8765        # HTTP 接口
```

Windows 用户可直接双击 `run_demo.bat`；类 Unix 环境用 `sh run_demo.sh`。

## 交付物导航

| 文件 | 内容 | 建议阅读顺序 |
| --- | --- | --- |
| `AGENT.md` | **主入口**：系统说明、五层架构、KSTAR 规范、命令、评分自检映射 | 1 |
| `architecture/ARCHITECTURE.md` | 分层契约、8 条 ADR、失败模式、不变量、扩展路径 | 2 |
| `architecture/architecture.html` | 一页可视化（双击打开，无外部依赖） | 3 |
| `architecture/layers/01..05.md` | 逐层深潜：职责 / 契约 / 失败模式 / 验收 | 4 |
| `architecture/schemas/*.json` | 三个数据契约：KSTAR 记忆、技能、轨迹 | 5 |
| `AAR/AAR.md` | 复盘：预期 vs 实际、12 个缺陷复盘、取舍、改进项 | 6 |
| `AI日志/AI日志.md` | AI 使用日志：阶段记录、提示词策略、12 处 AI 错误与纠正 | 7 |
| `logs/` | 运行证据：`demo-run.txt`、`test-report.txt`、`mining-report.md` | 8 |

## 目录速览

```
src/          内核 2,587 行（config / core / interfaces / tools / skills / memory）
skills/       6 个上线技能 + _proposed 草案（进化证据）
memory/       KSTAR 四层实际数据（k/s/t/a；t/ 为逐日轨迹）
tests/        12 项契约断言（临时目录隔离，不污染真实记忆）
logs/         运行与挖掘证据
workspace/    智能体工作区（inbox.md 等产物）
```

## 设计要点（三句话）

1. **分层**：每层都能在不改下层的前提下被替换（换接口只动 L1、换检索只动 L5、换规划器只动 L3）。
2. **记忆**：四层的区别不是格式，而是**回答的问题不同**——所以写入权限也必须不同（T 只追加、A 必带证据）。
3. **进化**：轨迹 → 挖掘重复序列 → 草案 → **人工闸门** → 上线为技能；下次同类指令直接走技能。

更完整的说明见 `AGENT.md`。

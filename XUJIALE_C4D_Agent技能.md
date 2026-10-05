# Agent 技能（交付物入口）

> **这是「Agent 技能」交付物的入口说明。**
> 技能本体是目录 **`XUJIALE_C4D_agent-skill/`** —— 「Agent 技能」是交付物名称，
> 不是文件名，所以在文件列表里找不到同名的文件。

## 技能本体在哪

```
XUJIALE_C4D_agent-skill/        ← 技能本体（约 2700 行，零第三方依赖）
├── agent/                      核心运行时
│   ├── llm_client.py           本地模型客户端（OpenAI 兼容，标准库实现）
│   ├── tools.py                工具注册表 + 工具工厂
│   ├── memory.py               三层记忆系统（事实 / 会话 / 工作）
│   └── core.py                 Agent 主循环（ReAct 式工具调用）
├── skills/
│   ├── sias_map.py             ★ 主程序：四阶段技能编排
│   ├── landmarks.json          本地离线地名词典（18 个规范地名）
│   └── offline_seed.json       演示种子数据
├── tools/
│   ├── map_render.py           Leaflet 地图渲染器 + 数据校验
│   └── chunked_downloader.py   分块并行下载器
├── tests/                      工程自检套件（4 套件 / 40+ 断言）
├── run.bat                     ★ Windows 一键运行（薄壳，5 行）
├── preflight.py                ★ 一键运行的 7 步编排逻辑（实际逻辑在此）
├── start_lowmem.bat            低内存模式启动 Ollama
├── verify_agent.py             Agent 能力验证套件（T1–T6）
├── bench_inference.py          推理性能基准
├── capture_evidence.py         证据采集
├── capture_env_limit.py        环境受限实测采集
├── report_builder.py           由真实产物渲染验证报告
├── package_submission.py       交付包打包
├── mem_check.py                加载模型前的内存预检
└── skill.json                  技能清单
```

## 怎么跑

```bash
cd XUJIALE_C4D_本地Agent技能/XUJIALE_C4D_agent-skill

# 生成交互式地图（需要本地模型）
python skills/sias_map.py --out output/sias_map.html

# 不用模型，验证「校验 → 定位 → 渲染」全链路
python skills/sias_map.py --offline-seed --out output/demo.html

# 工程自检（4 套件，秒级）
python -m tests.run_all
```

Windows 用户可直接双击 **`run.bat`**。

## 设计要点

- **零第三方依赖**：全程只用 Python 标准库，评审者不需要 `pip install`
- **按「创造性 / 确定性」切分职责**：模型产文案与分类，工具产坐标与距离 ——
  从架构上根除小模型最危险的幻觉类型（看似合理的错误坐标）
- **四阶段流水线**：记忆装载 → 模型生成（概率性）→ 事实校验（确定性）→
  地图渲染（确定性）

## 关联交付物

| 交付物 | 位置 |
|---|---|
| **demo** | `XUJIALE_C4D_demo/`（顶层，双击 `run_demo_offline.bat` 即可） |
| AI 日志 | `XUJIALE_C4D_AI日志.md` |
| AAR | `XUJIALE_C4D_AAR复盘.md` |
| 验证报告 | `XUJIALE_C4D_验证报告.md` |
| 环境受限分析 | `XUJIALE_C4D_环境受限分析.md` |

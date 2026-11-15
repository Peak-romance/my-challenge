# L4 · 技能层（Skills）

## 职责
把**重复任务**固化为声明式契约：可校验、可组合、可被挖掘、可被替换。
技能里没有代码——只有步骤编排，执行语义由工具定义。

## 双文件契约

```
skills/<name>/
├── skill.json   机器读：严格校验的步骤定义
└── SKILL.md     人读：解决什么问题、契约表、设计取舍、已知边界
```

```jsonc
{
  "name": "daily-brief",
  "version": "1.0.0",
  "status": "active",              // active | proposed | deprecated
  "description": "一句话说明解决什么问题",
  "triggers": ["简报", "日报"],     // 触发词，长度加权匹配
  "inputs": {                      // 输入契约
    "focus": {"type": "str", "required": false, "default": "", "desc": "..."}
  },
  "steps": [                       // 顺序执行
    {"id": "now", "tool": "time.now", "args": {"fmt": "%Y-%m-%d %A"}}
  ],
  "output": "模板，支持 {now} / {step.field} / {input.x} / {{字面量}}",
  "on_error": "abort"              // abort | continue
}
```

## 模板引擎（`skills/runtime.py::render`）

| 语法 | 含义 | 未命中时 |
| --- | --- | --- |
| `{step_id}` | 上一步的返回值（字符串原样 / 结构转 JSON） | 空串 |
| `{step_id.field}` | 结构返回值的字段（支持多级 `a.b.c`） | 空串 |
| `{input.name}` | 输入参数 | 空串 |
| `{{` `}}` | 字面量大括号（输出 JSON 时用） | — |

**为什么缺失变量渲染为空串而不是报错**：输出模板是"版式"，可选输入缺失不该让整条链路失败；
缺失会在 trace 里体现（该步输出为空），需要严格时应把输入标为 `required: true`。

## 装载与校验

```python
load_all()   # 逐目录装载，单个损坏不影响其他 → warnings
validate()   # 工具是否存在 / step id 是否重复 / output 是否为空 / on_error 合法性
```

装载器默认跳过 `_proposed/`（草案）与 `status=proposed`，因此"未确认的能力"不可能被误触发。

## 错误策略

| 值 | 语义 | 适用 |
| --- | --- | --- |
| `abort` | 任一步失败即整体失败（原子操作） | `capture-note`（双写要么都成，要么都不成） |
| `continue` | 失败步以 `[ERROR]` 占位，继续执行（聚合操作） | `daily-brief`、`repo-audit`、`self-check` |

选错策略的代价：
- 聚合任务用 `abort` → 一个信息源缺失导致整份简报失败（体验灾难）。
- 原子任务用 `continue` → 文件写了但记忆没写，用户以为记住了（信任灾难）。

## 组合与递归
`skill.run` 允许技能调用技能，`ctx.depth > 3` 中止。这是"原子技能 → 复合技能"的唯一通道，
避免把步骤复制粘贴到多个技能里（复制粘贴是技能库腐化的开始）。

## 挖掘 → 上线（能力闭环）

```
T 层轨迹（工具序列签名，忽略参数）
   → support ≥ min_support 的序列
   → skills/_proposed/<auto-name>/  （status=proposed，参数为占位符）
   → 人工：确认语义边界 / 补 triggers 与 inputs / 替换占位符
   → python agent.py --promote <name>  （status=active，version→1.0.0）
   → 此后同样的组合指令由规划器直接路由到该技能
```

**实测教训**：草案里的参数是 `<从轨迹补全: text>` 占位符，直接 promote 会让技能往 K 层写垃圾。
这就是人工闸门存在的实证理由（ADR-7），也是 `t_miner` 断言只验证"可上线"而非"可直接用"的原因。

## 技能设计五条准则

1. **一个技能只回答一个问题**。名字里出现"和/以及"就是拆分信号。
2. **输入不超过 3 个**。超过说明它其实是一类任务，应该拆开。
3. **输出模板可直接给人看**。技能产出的是成品，不是中间态。
4. **错误策略要显式选**。别用默认值蒙混——它是设计决策，不是配置项。
5. **SKILL.md 必须写边界与已知限制**。不写边界的技能，三个月后没人敢改。

## 验收
- `python agent.py --skills`：6 个技能，0 个契约问题
- `t_skill_load_validate` / `t_render` / `t_skill_budget_guard` 全绿
- `t_miner`：草案生成 → 上线 → 同样的指令改走技能（路由断言）

# L2 · 工具层（Tools）

## 职责
智能体唯一的"手"。**所有副作用必须经过这里**，这样"系统做了什么"永远可以被审计（trace 里记录 `tool/args/ms/ok`）。

## 契约

```python
@reg.register(name, description, params, danger=0, tags=())
def handler(ctx, **bound) -> Any: ...
```

| 规则 | 内容 |
| --- | --- |
| 参数声明 | `params` 必须声明类型/必填/默认值/说明；未知参数直接报错 |
| 显式失败 | 参数错误抛 `ToolError` 并给出可读原因（禁止静默返回空） |
| 危险分级 | `0` 只读 / `1` 写 / `2` 执行（`2` 需 `--danger` 显式授权） |
| 返回值 | 字符串或可 JSON 序列化的结构；结构化返回值供技能模板取字段 |
| 无状态 | 除记忆工具外，同样参数必须同样行为 |

## 工具清单（20 个）

| 类别 | 工具 | danger | 说明 |
| --- | --- | --- | --- |
| 时间 | `time.now` | 0 | strftime 时间锚点，用于简报与文件命名 |
| 文件 | `fs.list` / `fs.read` / `fs.grep` | 0 | 目录清单 / 读文本 / 正则搜索（返回 文件:行:内容） |
| 文件 | `fs.write` / `fs.append` | 1 | 写入 / 追加（自动建父目录） |
| 执行 | `shell.run` | 2 | 首命令白名单 + 超时 + 输出截断 |
| 网络 | `http.get` | 0 | GET + 去标签 + 截断（离线环境不可用时不阻塞其他能力） |
| 记忆 | `memory.search` / `memory.state` | 0 | 检索 K/A / 读 S |
| 记忆 | `memory.remember` / `memory.open_loop` / `memory.close_loop` | 1 | 写 K / 开待办 / 销待办 |
| 技能 | `skill.list` / `skill.run` / `skill.mine` | 0/1/1 | 列技能 / 组合调用（带递归保护）/ 挖掘草案 |
| 观测 | `trace.stats` / `system.info` | 0 | 轨迹统计 / 系统自检快照 |
| 格式 | `format.bullets` / `text.counter` | 0 | 列表→Markdown / 字数统计 |

## 安全边界（三层）

1. **路径沙箱**：相对路径一律相对项目根 `C10/` 解析；绝对路径越出项目根 → `ToolError("路径越界")`。
2. **命令白名单**：`shell.run` 的首命令必须在 `config.SHELL_ALLOWLIST` 内（python/git/ls/grep…），`rm -rf /` 直接拒绝。
3. **危险授权**：`danger≥2` 需 `ctx.allow_danger=True`（CLI 的 `--danger`），默认全部拒绝。

> 早期版本的设计是"写只允许 `workspace/`、读允许项目根"，实测立刻出现语义割裂：
> `巡检 src/tools` 会被解析成 `workspace/src/tools`（不存在）。改为同界后，边界从"目录隔离"
> 转为"根隔离 + 危险分级 + 轨迹留痕"，语义一致且仍可审计。详见 ADR-5。

## 失败模式

| 现象 | 机制 | 结果 |
| --- | --- | --- |
| 调用不存在的工具 | `Registry.get` 列出可用工具名 | `ok=False` + 建议清单 |
| 参数拼错 | `_bind` 检测未知参数 | `ok=False` + 允许的参数列表 |
| 工具内部异常 | `Registry.call` 兜底捕获 | 降级为步骤失败，不炸循环 |
| 输出过长 | `truncate()` | 截断 + 标注原长 |
| 命令超时 | `subprocess(timeout=)` | `ToolError("命令超时")` |

## 反模式（明确禁止）

- ❌ 工具内部 `except: return ""` —— 静默失败会让上层误判成功，是记忆污染的头号来源。
- ❌ 工具里 print —— 输出必须经 `ToolResult` 回到循环，否则无法进入 trace。
- ❌ 工具里直接 `open("memory/...")` —— 记忆必须经 `KStar`，否则四层策略形同虚设。

## 新增一个工具（3 步）

```python
@reg.register("demo.echo", "回显文本", {"text": {"type": "str"}}, danger=0, tags=("pure",))
def demo_echo(ctx, text: str):
    return text.upper()
```

随后 `python agent.py --tools` 即可见，技能也能直接引用（无需注册中心配置）。

## 验收
- `python agent.py --tools` 列出 20 个工具
- `python tests/test_smoke.py` 的 `t_tool_sandbox`：越界写被拒、`shell.run` 未授权被拒、未知参数被拒

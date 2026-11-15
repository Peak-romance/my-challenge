# L1 · 接口层（Interface）

## 职责
把任何外部输入规范化为一次 `Agent.run()` 调用，再把 `RunResult` 格式化回外部世界。
**不含任何规划、记忆、工具逻辑。** 判据很简单：把这一层整体删掉，内核仍然完好。

## 契约

```python
# 输入：任何形式的用户意图（文本 / JSON body / IM 消息）
# 输出：RunResult
RunResult(run_id, task, plan, steps, output, ok, quality, lesson, recall, ms, error)
```

| 接口 | 文件 | 输入 | 输出 | 适用 |
| --- | --- | --- | --- | --- |
| CLI 单次 | `cli.py` | `argv` 拼成的任务串 | 人类可读文本 | 脚本化 / 演示 |
| REPL | `cli.py` | 逐行 stdin | 逐轮输出 | 人工探索 |
| HTTP | `http_api.py` | `POST /run {"task": ...}` | JSON（`RunResult.to_dict()`） | 跨进程 / 前端 |
| （可扩展） | — | IM 消息 / 定时器 | 同上 | 长期运行 |

## 实现要点

1. **控制台编码兜底**：`_fix_console()` 把 stdout 重配为 UTF-8 + `errors="replace"`，
   避免 Windows 默认代码页在中文/符号上抛 `UnicodeEncodeError`。
2. **子命令与任务分离**：`--stats/--tools/--skills/--mine` 等直接操作内核对象，不进入循环；
   任务文本走 `Agent.run`。二者不混在一个分支里，避免"命令被当成任务执行"。
3. **退出码语义**：任务失败返回 `2`，参数/系统错误返回 `1`，成功 `0`——便于外部脚本判定。
4. **JSON 模式**：`--json` 输出完整 `RunResult`，包含 `run_id` 与召回分数，供审计与回归对比。

## 失败模式

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 中文输出乱码/报错 | 控制台代码页非 UTF-8 | `reconfigure(errors="replace")` |
| HTTP 端口占用 | 上一次 `--serve` 未退出 | 异常直出，提示换端口 |
| REPL 卡死 | `input()` 收到 EOF（管道输入） | 捕获 `EOFError` 并正常退出 |

## 扩展一个新接口（约 20 行）

```python
from src.core.loop import Agent
agent = Agent(verbose=False)
res = agent.run(text, source="feishu", session=chat_id)
reply(res.output)
```

**不需要改任何下层代码**——这就是分层的收益，也是本层唯一的验收标准：
新增接口不产生对 `src/core/`、`src/tools/`、`src/memory/` 的任何修改。

## 验收
- `python agent.py "自检"` 有输出且退出码 0
- `python agent.py --json "自检" | python -c "import json,sys;json.load(sys.stdin)"` 可解析
- `python agent.py --serve 8765` 后 `GET /health` 返回技能与工具数量

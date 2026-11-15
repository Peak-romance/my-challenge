"""内置工具集（L2 实现）。

工具是智能体唯一的"手"。所有副作用都必须经由这里，并留下 trace，
这样"系统做了什么"永远可以被审计。
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from pathlib import Path

from .. import config
from .base import Registry, ToolError, truncate

reg = Registry()


# ---------------------------------------------------------------- 路径安全
def _safe(path: str, *, write: bool) -> Path:
    p = Path(path)
    target = (p if p.is_absolute() else config.ROOT / p).resolve()
    root = (config.WRITE_SANDBOX if write else config.READ_SANDBOX).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        mode = "写" if write else "读"
        raise ToolError(f"路径越界：{target} 不在{mode}沙箱 {root} 内")
    return target


# ---------------------------------------------------------------- time
@reg.register(
    "time.now",
    "获取当前本地时间，用于日志、简报、文件命名",
    {"fmt": {"type": "str", "required": False, "default": "%Y-%m-%d %H:%M:%S", "desc": "strftime 格式"}},
    tags=("pure",),
)
def time_now(ctx, fmt: str):
    from datetime import datetime

    return datetime.now().strftime(fmt)


# ---------------------------------------------------------------- fs
@reg.register(
    "fs.list",
    "列出目录内容（文件名 + 大小）",
    {
        "path": {"type": "str", "required": False, "default": ".", "desc": "相对 workspace"},
        "limit": {"type": "int", "required": False, "default": 50},
    },
    tags=("read",),
)
def fs_list(ctx, path: str, limit: int):
    d = _safe(path, write=False)
    if not d.exists():
        raise ToolError(f"目录不存在: {d}")
    if d.is_file():
        return f"{d.name}\t{d.stat().st_size} bytes"
    items = sorted(d.iterdir(), key=lambda p: (p.is_file(), p.name))
    rows = [f"{'[D]' if p.is_dir() else '[F]'} {p.name}\t{0 if p.is_dir() else p.stat().st_size}" for p in items[: int(limit)]]
    return "\n".join(rows) or "（空目录）"


@reg.register(
    "fs.read",
    "读取文本文件内容（超长自动截断）",
    {
        "path": {"type": "str", "desc": "相对 workspace 的路径"},
        "max_chars": {"type": "int", "required": False, "default": 4000},
    },
    tags=("read",),
)
def fs_read(ctx, path: str, max_chars: int):
    f = _safe(path, write=False)  # 读允许覆盖整个项目根（C10/），写只允许 workspace/
    if not f.exists():
        raise ToolError(f"文件不存在: {f}")
    return truncate(f.read_text(encoding="utf-8", errors="replace"), int(max_chars))


@reg.register(
    "fs.write",
    "写入文本文件（覆盖），自动创建父目录",
    {
        "path": {"type": "str", "desc": "相对 workspace 的路径"},
        "content": {"type": "str"},
    },
    danger=1,
    tags=("write",),
)
def fs_write(ctx, path: str, content: str):
    f = _safe(path, write=True)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(content, encoding="utf-8")
    return f"已写入 {f.name}（{len(content)} 字符）"


@reg.register(
    "fs.append",
    "追加写入文本文件（用于日志）",
    {"path": {"type": "str"}, "content": {"type": "str"}},
    danger=1,
    tags=("write",),
)
def fs_append(ctx, path: str, content: str):
    f = _safe(path, write=True)
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a", encoding="utf-8") as fh:
        fh.write(content if content.endswith("\n") else content + "\n")
    return f"已追加 {f.name}"


@reg.register(
    "fs.grep",
    "在目录内按正则搜索文本，返回 文件:行号:内容",
    {
        "pattern": {"type": "str"},
        "path": {"type": "str", "required": False, "default": "."},
        "glob": {"type": "str", "required": False, "default": "*.md"},
        "limit": {"type": "int", "required": False, "default": 40},
    },
    tags=("read",),
)
def fs_grep(ctx, pattern: str, path: str, glob: str, limit: int):
    root = _safe(path, write=False)
    try:
        rx = re.compile(pattern)
    except re.error as e:
        raise ToolError(f"正则非法: {e}")
    hits: list[str] = []
    for f in root.rglob(glob):
        if not f.is_file() or f.stat().st_size > 2_000_000:
            continue
        try:
            for i, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if rx.search(line):
                    hits.append(f"{f.relative_to(root)}:{i}: {line.strip()[:160]}")
                    if len(hits) >= int(limit):
                        return "\n".join(hits) + "\n...[已达上限]"
        except OSError:
            continue
    return "\n".join(hits) or "（无匹配）"


# ---------------------------------------------------------------- shell
@reg.register(
    "shell.run",
    "执行 shell 命令（首命令白名单 + 超时 + 输出截断）",
    {
        "cmd": {"type": "str"},
        "cwd": {"type": "str", "required": False, "default": "."},
    },
    danger=2,
    tags=("exec",),
)
def shell_run(ctx, cmd: str, cwd: str):
    try:
        head = shlex.split(cmd, posix=False)[0].lower()
    except Exception:
        head = cmd.split()[0].lower() if cmd.split() else ""
    head = head.strip('"').removesuffix(".exe")
    if head not in config.SHELL_ALLOWLIST:
        raise ToolError(f"命令 `{head}` 不在白名单内，已拒绝执行")
    wd = _safe(cwd, write=True)
    try:
        p = subprocess.run(
            cmd,
            shell=True,
            cwd=str(wd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=config.DEFAULT_BUDGET.tool_timeout_s,
        )
    except subprocess.TimeoutExpired:
        raise ToolError(f"命令超时（>{config.DEFAULT_BUDGET.tool_timeout_s}s）")
    out = (p.stdout or "") + (("\n[stderr]\n" + p.stderr) if p.stderr else "")
    return truncate(f"exit={p.returncode}\n{out.strip()}")


# ---------------------------------------------------------------- http
@reg.register(
    "http.get",
    "HTTP GET 取回网页/接口文本（自动去标签、截断）",
    {
        "url": {"type": "str"},
        "max_chars": {"type": "int", "required": False, "default": 3000},
    },
    tags=("net",),
)
def http_get(ctx, url: str, max_chars: int):
    import urllib.request

    if not url.startswith(("http://", "https://")):
        raise ToolError("仅支持 http/https")
    req = urllib.request.Request(url, headers={"User-Agent": "C10-Agent/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=config.DEFAULT_BUDGET.tool_timeout_s) as resp:
            raw = resp.read(400_000).decode("utf-8", errors="replace")
    except Exception as e:
        raise ToolError(f"请求失败: {type(e).__name__}: {e}")
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return truncate(text.strip(), int(max_chars))


# ---------------------------------------------------------------- memory
@reg.register(
    "memory.search",
    "检索 K（知识）/A（复盘）记忆层，返回命中条目与得分",
    {
        "query": {"type": "str"},
        "layer": {"type": "str", "required": False, "default": "KA", "desc": "K/A/KA"},
        "k": {"type": "int", "required": False, "default": 5},
    },
    tags=("memory",),
)
def memory_search(ctx, query: str, layer: str, k: int):
    layers = tuple(x for x in layer.upper() if x in "KA") or ("K", "A")
    hits = ctx.memory.recall(query, k=int(k), layers=layers)
    return {
        "count": len(hits),
        "items": [
            {
                "id": h.get("id"),
                "layer": h.get("layer"),
                "text": h.get("text"),
                "score": h.get("_score"),
                "hit": h.get("_hit"),
            }
            for h in hits
        ],
    }


@reg.register(
    "memory.remember",
    "把一条稳定结论写入 K 层长期记忆（自动去重、可加标签与重要度）",
    {
        "text": {"type": "str"},
        "tags": {"type": "str", "required": False, "default": ""},
        "importance": {"type": "float", "required": False, "default": 0.7},
    },
    danger=1,
    tags=("memory", "write"),
)
def memory_remember(ctx, text: str, tags: str, importance: float):
    rec = ctx.memory.remember(text, tags=tags, importance=float(importance), source=f"run:{ctx.run_id}")
    return {"id": rec["id"], "dedup": bool(rec.get("_dedup")), "importance": rec["importance"]}


@reg.register(
    "memory.state",
    "读取 S 层工作状态（未闭环事项、焦点、最近任务）",
    {},
    tags=("memory", "read"),
)
def memory_state(ctx):
    st = ctx.memory.state()
    return {
        "turns": st.get("turns", 0),
        "focus": st.get("focus", ""),
        "last_task": st.get("last_task", ""),
        "open_loops": [l.get("text") for l in st.get("open_loops", [])],
        "recent": [r.get("task") for r in st.get("recent", [])][-5:],
    }


@reg.register(
    "memory.open_loop",
    "登记一个未闭环事项到 S 层（跨会话不丢）",
    {"text": {"type": "str"}},
    danger=1,
    tags=("memory", "write"),
)
def memory_open_loop(ctx, text: str):
    ctx.memory.add_open_loop(text)
    return f"已登记未闭环事项: {text}"


@reg.register(
    "memory.close_loop",
    "关闭包含指定关键词的未闭环事项（S 层闭环动作）",
    {"keyword": {"type": "str"}},
    danger=1,
    tags=("memory", "write"),
)
def memory_close_loop(ctx, keyword: str):
    n = ctx.memory.close_open_loop(keyword)
    return f"已关闭 {n} 条包含「{keyword}」的未闭环事项" if n else f"没有匹配「{keyword}」的未闭环事项"


# ---------------------------------------------------------------- skills
@reg.register("skill.list", "列出已装载技能", {}, tags=("skill",))
def skill_list(ctx):
    return [
        {"name": s.name, "version": s.version, "description": s.description, "triggers": s.triggers[:4]}
        for s in ctx.skills.all()
    ]


@reg.register(
    "skill.run",
    "调用另一个技能（技能可组合，含递归深度保护）",
    {"name": {"type": "str"}, "inputs": {"type": "dict", "required": False, "default": {}}},
    danger=1,
    tags=("skill",),
)
def skill_run(ctx, name: str, inputs: dict):
    if getattr(ctx, "depth", 0) >= 3:
        raise ToolError("技能递归深度超限（>3），已中止")
    return ctx.skills.run_nested(ctx, name, inputs or {})


# ---------------------------------------------------------------- trace / system
@reg.register(
    "trace.stats",
    "统计最近 N 天 T 层轨迹：运行数、成功率、平均质量、工具频次、教训分布",
    {"days": {"type": "int", "required": False, "default": 7}},
    tags=("memory", "read"),
)
def trace_stats(ctx, days: int):
    tr = ctx.memory.read_traces(int(days))
    if not tr:
        return {"runs": 0, "note": f"最近 {days} 天无轨迹"}
    tools: dict[str, int] = {}
    kinds: dict[str, int] = {}
    for r in tr:
        for s in r.get("steps", []):
            tools[s.get("tool", "?")] = tools.get(s.get("tool", "?"), 0) + 1
        lesson = r.get("lesson") or {}
        if lesson.get("kind"):
            kinds[lesson["kind"]] = kinds.get(lesson["kind"], 0) + 1
    ok_n = sum(1 for r in tr if r.get("ok"))
    return {
        "runs": len(tr),
        "ok_rate": round(ok_n / len(tr), 3),
        "avg_quality": round(sum(float(r.get("quality", 0)) for r in tr) / len(tr), 3),
        "avg_ms": int(sum(int(r.get("ms", 0)) for r in tr) / len(tr)),
        "top_tools": [f"{t} ×{c}" for t, c in sorted(tools.items(), key=lambda kv: -kv[1])[:6]],
        "lesson_kinds": kinds,
        "recent_tasks": [str(r.get("task", ""))[:50] for r in tr[-5:]],
    }


@reg.register(
    "system.info",
    "输出系统自检信息：工具数、技能清单与校验问题、记忆分层统计、预算",
    {},
    tags=("system", "read"),
)
def system_info(ctx):
    import sys
    from dataclasses import asdict

    return {
        "python": sys.version.split()[0],
        "root": str(config.ROOT),
        "tools": len(ctx.tools.names()),
        "skills": [s.name for s in ctx.skills.all()],
        "skill_problems": ctx.skills.problems,
        "skill_warnings": ctx.skills.warnings,
        "memory": ctx.memory.stats(),
        "budget": asdict(ctx.budget),
    }


@reg.register(
    "skill.mine",
    "从 T 层轨迹中挖掘可抽象为技能的工具序列（默认只出报告不落盘）",
    {
        "days": {"type": "int", "required": False, "default": 30},
        "min_support": {"type": "int", "required": False, "default": 2},
        "commit": {"type": "bool", "required": False, "default": False},
    },
    danger=1,
    tags=("skill",),
)
def skill_mine(ctx, days: int, min_support: int, commit: bool):
    from ..core import miner

    rep = miner.mine(ctx.memory, days=int(days), min_support=int(min_support), dry_run=not bool(commit))
    return {
        "traces_analyzed": rep["traces_analyzed"],
        "candidates": [
            {"name": c["name"], "support": c["support"], "tools": c["tools"]} for c in rep["candidates"]
        ],
        "written": rep["written"],
    }


# ---------------------------------------------------------------- format
@reg.register(
    "format.bullets",
    "把列表/JSON 字符串渲染为 Markdown 项目符号（可指定字段）",
    {
        "items": {"type": "str", "desc": "列表或 JSON 字符串，如 {st.open_loops}"},
        "prefix": {"type": "str", "required": False, "default": "- "},
        "field": {"type": "str", "required": False, "default": "", "desc": "元素为 dict 时取该字段"},
        "empty": {"type": "str", "required": False, "default": "（无）"},
    },
    tags=("pure",),
)
def format_bullets(ctx, items, prefix: str, field: str, empty: str):
    import json as _json

    data = items
    if isinstance(data, str):
        stripped = data.strip()
        if stripped[:1] in "[{":
            try:
                data = _json.loads(stripped)
            except Exception:
                data = [stripped]
        else:
            data = [stripped] if stripped else []
    if isinstance(data, dict):
        data = [f"**{k}**: {v}" for k, v in data.items()]
    if not isinstance(data, list):
        data = [str(data)]
    rows = []
    for it in data:
        if isinstance(it, dict):
            rows.append(str(it.get(field, it)) if field else _json.dumps(it, ensure_ascii=False))
        else:
            rows.append(str(it))
    return "\n".join(f"{prefix}{r}" for r in rows) if rows else empty


# ---------------------------------------------------------------- text
@reg.register(
    "text.counter",
    "统计文本的字符数/行数/词数，用于验收与自检",
    {"text": {"type": "str"}},
    tags=("pure",),
)
def text_counter(ctx, text: str):
    return {
        "chars": len(text),
        "lines": text.count("\n") + 1 if text else 0,
        "words": len(re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", text)),
    }


def build_registry() -> Registry:
    return reg

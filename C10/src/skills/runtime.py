"""技能运行时（L4 执行器）。

职责
----
1. 把声明式技能编译成顺序工具调用（参数模板 → 变量绑定 → 工具调用）。
2. 强制预算、错误策略（abort/continue）、递归深度保护。
3. 逐步产出 trace，使"技能内部发生了什么"同样可审计——
   这是技能能进入 AAR 的前提：没有轨迹的技能只是一个黑盒宏。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .. import config
from .loader import SkillSpec, load_all, validate

_TPL = re.compile(r"\{([A-Za-z0-9_.\-]+)\}")
_PH_OPEN, _PH_CLOSE = "\x00", "\x01"


def _stringify(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False, indent=2)
    return str(v)


def render(tpl: Any, vars: dict) -> str:
    """极简模板：支持 {step_id}、{step_id.field}、{input.name}；{{ }} 为字面量转义。

    未命中变量渲染为空串而非报错——技能输出模板是"版式"，
    不该因为可选输入缺失就整条链路失败；缺失会在 trace 里被记录。
    """
    if not isinstance(tpl, str):
        return _stringify(tpl)
    s = tpl.replace("{{", _PH_OPEN).replace("}}", _PH_CLOSE)

    def sub(m: re.Match) -> str:
        cur: Any = vars
        for part in m.group(1).split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return ""
        return _stringify(cur)

    return _TPL.sub(sub, s).replace(_PH_OPEN, "{").replace(_PH_CLOSE, "}")


def render_obj(obj: Any, vars: dict) -> Any:
    if isinstance(obj, str):
        return render(obj, vars)
    if isinstance(obj, dict):
        return {k: render_obj(v, vars) for k, v in obj.items()}
    if isinstance(obj, list):
        return [render_obj(v, vars) for v in obj]
    return obj


class SkillRuntime:
    def __init__(self, tools, root: Path | None = None):
        self.tools = tools
        self.root = Path(root or config.SKILLS_DIR)
        self.skills: dict[str, SkillSpec] = {}
        self.warnings: list[str] = []
        self.problems: dict[str, list[str]] = {}
        self.stats: dict[str, dict] = {}
        self.reload()

    # ------------------------------------------------------------ 装载
    def reload(self) -> None:
        self.skills, self.warnings = load_all(self.root)
        self.problems = {name: validate(s, self.tools.names()) for name, s in self.skills.items()}
        self.problems = {k: v for k, v in self.problems.items() if v}

    def all(self) -> list[SkillSpec]:
        return sorted(self.skills.values(), key=lambda s: s.name)

    def get(self, name: str) -> SkillSpec:
        if name not in self.skills:
            raise KeyError(f"未知技能 `{name}`；已装载: {sorted(self.skills)}")
        return self.skills[name]

    def match(self, task: str) -> tuple[SkillSpec | None, int]:
        """触发词匹配：命中长度加权，取最高分；并列时取名字更短者（更专指）。"""
        best: SkillSpec | None = None
        best_score = 0
        low = (task or "").lower()
        for spec in self.skills.values():
            score = 0
            for t in spec.triggers:
                tt = t.lower().strip()
                if tt and tt in low:
                    score += len(tt) + 1
            if score > best_score:
                best, best_score = spec, score
        return best, best_score

    # ------------------------------------------------------------ 执行
    def run(self, ctx, spec: SkillSpec, inputs: dict | None = None) -> dict:
        inputs = dict(inputs or {})
        # 输入契约校验：必填项缺失立即失败，不进入工具链
        for name, idef in spec.inputs.items():
            if name not in inputs or inputs[name] in (None, ""):
                if "default" in idef:
                    inputs[name] = idef["default"]
                elif idef.get("required", False):
                    return {
                        "ok": False,
                        "skill": spec.name,
                        "output": "",
                        "error": f"技能 `{spec.name}` 缺少必填输入 `{name}`",
                        "steps": [],
                    }

        vars: dict[str, Any] = {"input": inputs, "task": ctx.task, "run_id": ctx.run_id}
        vars.update(inputs)

        ctx.depth += 1
        steps_trace: list[dict] = []
        try:
            for i, step in enumerate(spec.steps, 1):
                if ctx.steps_used >= ctx.budget.max_steps:
                    return self._fail(spec, steps_trace, f"步数预算耗尽（max_steps={ctx.budget.max_steps}）")
                tool = step.get("tool", "")
                raw_args = step.get("args", {}) or {}
                args = render_obj(raw_args, vars)
                res = ctx.tools.call(tool, args, ctx)
                ctx.steps_used += 1
                sid = step.get("id") or f"s{i}"
                value = res.value if res.ok else f"[ERROR] {res.error}"
                vars[sid] = value
                rec = {
                    "i": i,
                    "id": sid,
                    "tool": tool,
                    "args": args,
                    "ok": res.ok,
                    "ms": res.ms,
                    "out": (res.as_text() if res.ok else "")[:400],
                    "err": res.error,
                }
                steps_trace.append(rec)
                ctx.emit_step(rec)
                if not res.ok and spec.on_error == "abort":
                    return self._fail(spec, steps_trace, f"步骤 {sid}/{tool} 失败：{res.error}")

            output = render(spec.output, vars)
            self._bump(spec.name, ok=True)
            return {"ok": True, "skill": spec.name, "output": output, "steps": steps_trace, "error": ""}
        finally:
            ctx.depth -= 1

    def run_nested(self, ctx, name: str, inputs: dict) -> dict:
        spec = self.get(name)
        return self.run(ctx, spec, inputs)

    @staticmethod
    def _fail(spec: SkillSpec, steps: list[dict], error: str) -> dict:
        partial = "\n".join(f"- {s['id']}: {'OK' if s['ok'] else 'FAIL'}" for s in steps)
        return {
            "ok": False,
            "skill": spec.name,
            "output": "",
            "error": error,
            "steps": steps,
            "partial": partial,
        }

    def _bump(self, name: str, *, ok: bool) -> None:
        st = self.stats.setdefault(name, {"runs": 0, "ok": 0, "fail": 0})
        st["runs"] += 1
        st["ok" if ok else "fail"] += 1

"""工具层契约（L2）。

三条硬规则
----------
1. **声明式**：每个工具必须声明参数表（类型/必填/默认值），供规划器与技能校验共用。
2. **显式失败**：参数错误必须抛 ToolError 并给出可读原因，禁止静默返回空值——
   静默失败会让上层误判"成功"，是长期智能体最常见的记忆污染源。
3. **危险分级**：danger 0=只读 / 1=写 / 2=执行。危险级别进入 trace，
   使复盘能回答"这次运行到底动了什么"。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .. import config


class ToolError(Exception):
    """工具层异常。上层据此判定步骤失败并进入重试/降级路径。"""


@dataclass
class ToolSpec:
    name: str
    description: str
    params: dict[str, dict]
    handler: Callable[..., Any]
    danger: int = 0
    tags: tuple[str, ...] = ()

    def schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "danger": self.danger,
            "tags": list(self.tags),
            "params": self.params,
        }


@dataclass
class ToolResult:
    ok: bool
    value: Any = None
    error: str = ""
    ms: int = 0

    def as_text(self, indent: int | None = 2) -> str:
        if not self.ok:
            return f"[ERROR] {self.error}"
        if isinstance(self.value, str):
            return self.value
        import json

        try:
            return json.dumps(self.value, ensure_ascii=False, indent=indent)
        except TypeError:
            return str(self.value)


class Registry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self.calls = 0

    def register(
        self,
        name: str,
        description: str,
        params: dict[str, dict] | None = None,
        *,
        danger: int = 0,
        tags: tuple[str, ...] = (),
    ) -> Callable:
        def deco(fn: Callable) -> Callable:
            if name in self._tools:
                raise ValueError(f"工具重复注册: {name}")
            self._tools[name] = ToolSpec(
                name=name,
                description=description,
                params=params or {},
                handler=fn,
                danger=danger,
                tags=tags,
            )
            return fn

        return deco

    def get(self, name: str) -> ToolSpec:
        if name not in self._tools:
            near = ", ".join(sorted(self._tools)[:12])
            raise ToolError(f"未知工具 `{name}`。可用示例: {near}")
        return self._tools[name]

    def names(self) -> list[str]:
        return sorted(self._tools)

    def specs(self) -> list[dict]:
        return [self._tools[n].schema() for n in self.names()]

    def _bind(self, spec: ToolSpec, args: dict) -> dict:
        unknown = set(args) - set(spec.params)
        if unknown:
            raise ToolError(
                f"工具 `{spec.name}` 不接受参数 {sorted(unknown)}；"
                f"允许参数: {sorted(spec.params) or '（无）'}"
            )
        bound: dict[str, Any] = {}
        missing: list[str] = []
        for pname, pdef in spec.params.items():
            if pname in args and args[pname] is not None:
                bound[pname] = args[pname]
            elif "default" in pdef:
                bound[pname] = pdef["default"]
            elif pdef.get("required", True):
                missing.append(pname)
        if missing:
            raise ToolError(f"工具 `{spec.name}` 缺少必填参数 {missing}")
        return bound

    def call(self, name: str, args: dict | None, ctx: Any) -> ToolResult:
        t0 = time.perf_counter()
        try:
            spec = self.get(name)
            bound = self._bind(spec, args or {})
            if spec.danger >= 2 and not getattr(ctx, "allow_danger", False):
                raise ToolError(f"工具 `{name}` 属于执行级危险操作，本次运行未授权（ctx.allow_danger=False）")
            self.calls += 1
            value = spec.handler(ctx, **bound)
            return ToolResult(True, value, ms=int((time.perf_counter() - t0) * 1000))
        except ToolError as e:
            return ToolResult(False, None, str(e), ms=int((time.perf_counter() - t0) * 1000))
        except Exception as e:  # 工具内部未捕获异常一律降级为步骤失败，不炸掉整个循环
            return ToolResult(False, None, f"{type(e).__name__}: {e}", ms=int((time.perf_counter() - t0) * 1000))


def truncate(text: str, limit: int | None = None) -> str:
    limit = limit or config.DEFAULT_BUDGET.max_output_chars
    text = text if isinstance(text, str) else str(text)
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n...[截断，原长 {len(text)} 字符]"

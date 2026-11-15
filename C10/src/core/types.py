"""运行时数据结构：一次运行的全部上下文都收敛在这里。

RunContext 是各层之间的唯一"总线"：L2 工具拿它取沙箱与预算，
L4 技能拿它取工具表与深度计数，L3 循环拿它累计步数。禁止用全局变量传递状态。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .. import config


@dataclass
class RunContext:
    run_id: str
    task: str
    memory: Any
    tools: Any
    skills: Any
    budget: config.Budget = config.DEFAULT_BUDGET
    source: str = "cli"
    session: str = "default"
    allow_danger: bool = False
    depth: int = 0
    steps_used: int = 0
    on_step: Callable[[dict], None] | None = None

    def emit_step(self, rec: dict) -> None:
        if self.on_step:
            self.on_step(rec)


@dataclass
class Plan:
    """规划结果。kind 决定 L3 的分发路径。"""

    kind: str                       # skill | tools | answer
    rationale: str = ""
    skill: str = ""
    inputs: dict = field(default_factory=dict)
    steps: list[dict] = field(default_factory=list)
    answer: str = ""

    def to_dict(self) -> dict:
        d = {"kind": self.kind, "rationale": self.rationale}
        if self.skill:
            d.update({"skill": self.skill, "inputs": self.inputs})
        if self.steps:
            d["steps"] = [{"tool": s.get("tool"), "args": s.get("args", {})} for s in self.steps]
        if self.answer:
            d["answer"] = self.answer[:300]
        return d


@dataclass
class RunResult:
    run_id: str
    task: str
    plan: Plan
    steps: list[dict]
    output: str
    ok: bool
    quality: float
    lesson: dict | None
    recall: list[dict]
    ms: int
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "task": self.task,
            "ok": self.ok,
            "quality": round(self.quality, 3),
            "ms": self.ms,
            "plan": self.plan.to_dict(),
            "steps": len(self.steps),
            "recall": [{"id": r.get("id"), "layer": r.get("layer"), "score": r.get("_score")} for r in self.recall],
            "lesson": self.lesson,
            "output": self.output[:800],
            "error": self.error,
        }

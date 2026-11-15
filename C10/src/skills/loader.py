"""技能装载器（L4）。

技能 = 声明式契约（skill.json）+ 人读文档（SKILL.md）。

为什么用 JSON 而不是 YAML frontmatter
------------------------------------
YAML 子集解析器是 bug 温床（缩进、块标量、引号转义）。技能契约是要被机器严格校验的，
因此选择零歧义的 JSON 作为可执行规格，同时保留 SKILL.md 作为人类与 LLM 的阅读入口。
两者共存：机器读 JSON，人和模型读 MD，各自发挥所长。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .. import config

REQUIRED_KEYS = ("name", "description", "steps")


@dataclass
class SkillSpec:
    name: str
    description: str
    steps: list[dict]
    version: str = "1.0.0"
    triggers: list[str] = field(default_factory=list)
    inputs: dict[str, dict] = field(default_factory=dict)
    output: str = ""
    on_error: str = "abort"          # abort | continue
    tags: list[str] = field(default_factory=list)
    status: str = "active"           # active | proposed | deprecated
    meta: dict[str, Any] = field(default_factory=dict)
    path: Path | None = None

    @property
    def slug(self) -> str:
        return self.path.parent.name if self.path else self.name

    def schema(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "triggers": self.triggers,
            "inputs": self.inputs,
            "steps": [{"id": s.get("id"), "tool": s.get("tool")} for s in self.steps],
            "on_error": self.on_error,
        }


def load_one(path: Path) -> SkillSpec:
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        raise ValueError(f"{path} 缺少必填字段 {missing}")
    return SkillSpec(
        name=data["name"],
        description=data.get("description", ""),
        steps=data.get("steps", []),
        version=str(data.get("version", "1.0.0")),
        triggers=list(data.get("triggers", [])),
        inputs=dict(data.get("inputs", {})),
        output=data.get("output", ""),
        on_error=data.get("on_error", "abort"),
        tags=list(data.get("tags", [])),
        status=data.get("status", "active"),
        meta={k: v for k, v in data.items() if k not in
              {"name", "description", "steps", "version", "triggers", "inputs", "output", "on_error", "tags", "status"}},
        path=path,
    )


def load_all(root: Path | None = None, *, include_proposed: bool = False) -> tuple[dict[str, SkillSpec], list[str]]:
    """返回 (技能表, 装载告警)。单个技能损坏不影响其余技能可用。"""
    root = Path(root or config.SKILLS_DIR)
    skills: dict[str, SkillSpec] = {}
    warnings: list[str] = []
    if not root.exists():
        return skills, [f"技能目录不存在: {root}"]

    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        if d.name.startswith("_") and not include_proposed:
            continue
        cfg = d / "skill.json"
        if not cfg.exists():
            continue
        try:
            spec = load_one(cfg)
        except Exception as e:
            warnings.append(f"{d.name}: 装载失败 {type(e).__name__}: {e}")
            continue
        if spec.name in skills:
            warnings.append(f"{d.name}: 技能名 `{spec.name}` 与已装载技能重复，已跳过")
            continue
        if spec.status == "proposed" and not include_proposed:
            continue
        skills[spec.name] = spec
    return skills, warnings


def validate(spec: SkillSpec, tool_names: list[str]) -> list[str]:
    """静态校验：工具是否存在、必填 id、输出模板是否为空。"""
    problems: list[str] = []
    known = set(tool_names)
    ids = set()
    for i, step in enumerate(spec.steps, 1):
        tool = step.get("tool")
        if not tool:
            problems.append(f"step#{i} 缺少 tool")
            continue
        if tool not in known:
            problems.append(f"step#{i} 引用了未知工具 `{tool}`")
        sid = step.get("id") or f"s{i}"
        if sid in ids:
            problems.append(f"step#{i} 的 id `{sid}` 重复")
        ids.add(sid)
    if not spec.output.strip():
        problems.append("output 模板为空，技能不会产出任何内容")
    if spec.on_error not in ("abort", "continue"):
        problems.append(f"on_error 只能是 abort/continue，实际为 {spec.on_error}")
    return problems

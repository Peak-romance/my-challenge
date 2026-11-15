"""技能挖掘器（L4 的"进化引擎"）。

机制
----
系统每次运行都会在 T 层留下工具调用序列。挖掘器定期做三件事：
1. 抽取序列签名（只保留工具名，忽略参数），统计重复度；
2. 对 support ≥ 阈值的序列生成技能草案（skills/_proposed/），**不自动上线**；
3. 人工审阅后 promote，技能进入正式装载路径。

为什么必须人工闸门
------------------
自动生成的技能只是"曾经这样干过"，不等于"应该这样干"。
把未经确认的行为序列直接提升为可复用能力，等于把偶然固化成制度——
这正是长期智能体最危险的退化模式。
"""

from __future__ import annotations

import json
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from .. import config
from ..skills.loader import load_all

_CJK_RUN = re.compile(r"[\u4e00-\u9fff]+")
_EN = re.compile(r"[A-Za-z]{3,}")
_STOP = {"今天", "一下", "帮我", "请帮", "一个", "这个", "那个", "然后", "就是", "可以", "需要"}


def _signature(trace: dict) -> tuple[str, ...]:
    plan = trace.get("plan") or {}
    if plan.get("kind") == "skill":
        return (f"skill:{plan.get('skill')}",)
    tools = [s.get("tool") for s in (trace.get("steps") or []) if s.get("tool")]
    return tuple(tools)


def _keywords(texts: list[str], top: int = 3) -> list[str]:
    cnt: Counter[str] = Counter()
    for t in texts:
        for run in _CJK_RUN.findall(t or ""):
            for i in range(len(run) - 1):
                bg = run[i:i + 2]
                if bg not in _STOP:
                    cnt[bg] += 1
        for w in _EN.findall(t or ""):
            cnt[w.lower()] += 1
    return [w for w, c in cnt.most_common(top) if c >= 2]


def _slug(sig: tuple[str, ...]) -> str:
    parts = [s.split(":")[-1].replace(".", "-").replace("_", "-") for s in sig]
    raw = "auto-" + "-".join(parts)
    return re.sub(r"[^a-zA-Z0-9\-]", "", raw)[:48].strip("-")


def _step_args(trace: dict) -> list[dict]:
    out = []
    for i, s in enumerate(trace.get("steps") or [], 1):
        args = {}
        for k, v in (s.get("args") or {}).items():
            if isinstance(v, str) and len(v) <= 16:
                args[k] = v
            else:
                args[k] = f"<从轨迹补全: {k}>"
        out.append({"id": s.get("id") or f"s{i}", "tool": s.get("tool"), "args": args})
    return out


def mine(
    memory,
    *,
    days: int = 30,
    min_support: int = 2,
    dry_run: bool = False,
    skills_root: Path | None = None,
) -> dict:
    skills_root = Path(skills_root or config.SKILLS_DIR)
    traces = memory.read_traces(days)
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for t in traces:
        sig = _signature(t)
        if len(sig) < 2:
            continue          # 单步调用不值得抽象为技能
        groups[sig].append(t)

    existing, _ = load_all(skills_root)
    existing_sigs = {
        tuple(s.get("tool") for s in spec.steps) for spec in existing.values()
    }

    candidates: list[dict] = []
    covered: list[dict] = []
    written: list[str] = []
    for sig, records in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        support = len(records)
        if support < min_support:
            continue
        if tuple(x.split(":")[-1] for x in sig) in existing_sigs:
            # 该序列已被技能覆盖：不是"没发现"，而是"已经学会"——两者必须区分，
            # 否则报告会让人误以为系统什么都没学到。
            covered.append({"tools": list(sig), "support": support,
                            "sample": records[-1].get("task", "")[:40]})
            continue
        if sig[0].startswith("skill:"):
            continue          # 已是技能驱动，不再重复抽象

        name = _slug(sig)
        latest = max(records, key=lambda r: r.get("ts", ""))
        tasks = [r.get("task", "") for r in records]
        cand = {
            "name": name,
            "support": support,
            "tools": list(sig),
            "sample_tasks": tasks[:3],
            "proposed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        candidates.append(cand)
        if dry_run:
            continue

        d = skills_root / "_proposed" / name
        d.mkdir(parents=True, exist_ok=True)
        spec = {
            "name": name,
            "version": "0.1.0",
            "status": "proposed",
            "description": f"由 {support} 次轨迹自动归纳的工具序列（待人工确认语义与触发词）",
            "triggers": _keywords(tasks),
            "inputs": {"focus": {"type": "str", "required": False, "default": "", "desc": "任务焦点"}},
            "steps": _step_args(latest),
            "output": "## 自动归纳技能输出\n\n"
                      + "\n".join(f"- {s['tool']}: {{{s['id']}}}" for s in _step_args(latest)),
            "on_error": "continue",
            "tags": ["auto-mined"],
        }
        (d / "skill.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
        (d / "SKILL.md").write_text(
            f"# {name}（自动草案，未上线）\n\n"
            f"- 支持度：{support} 次轨迹\n"
            f"- 工具序列：{' → '.join(sig)}\n"
            f"- 样例任务：\n" + "\n".join(f"  - {t}" for t in tasks[:3]) +
            "\n\n## 上线前必须人工完成\n"
            "1. 确认该序列的语义边界（它到底解决什么问题）；\n"
            "2. 补齐 triggers 与 inputs 契约；\n"
            "3. 把 `<从轨迹补全>` 占位替换为真实参数绑定；\n"
            "4. `python agent.py --promote " + name + "`\n",
            encoding="utf-8",
        )
        written.append(str(d / "skill.json"))

    report = {
        "mined_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "traces_analyzed": len(traces),
        "signatures": len(groups),
        "candidates": candidates,
        "covered": covered,
        "written": written,
        "dry_run": dry_run,
    }
    _write_report(report)
    return report


def promote(name: str, skills_root: Path | None = None) -> Path:
    """把草案从 _proposed 提升为正式技能（人工闸门后的动作）。"""
    skills_root = Path(skills_root or config.SKILLS_DIR)
    src = skills_root / "_proposed" / name
    if not src.exists():
        raise FileNotFoundError(f"草案不存在: {src}")
    dst = skills_root / name
    if dst.exists():
        raise FileExistsError(f"目标技能已存在: {dst}")
    shutil.copytree(src, dst)
    spec_file = dst / "skill.json"
    spec = json.loads(spec_file.read_text(encoding="utf-8"))
    spec["status"] = "active"
    spec["version"] = "1.0.0"
    spec.pop("tags", None)
    spec_file.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    return dst


def _write_report(report: dict) -> None:
    lines = [
        "# 技能挖掘报告",
        "",
        f"- 时间：{report['mined_at']}",
        f"- 分析轨迹：{report['traces_analyzed']} 条",
        f"- 不同工具序列：{report['signatures']} 种",
        f"- 生成草案：{len(report['written'])} 个（dry_run={report['dry_run']}）",
        f"- 已被技能覆盖的序列：{len(report.get('covered', []))} 个",
        "",
        "| 候选技能 | 支持度 | 工具序列 | 样例任务 |",
        "| --- | --- | --- | --- |",
    ]
    for c in report["candidates"]:
        lines.append(
            f"| `{c['name']}` | {c['support']} | {' → '.join(c['tools'])} | "
            f"{(c['sample_tasks'][0] if c['sample_tasks'] else '')[:40]} |"
        )
    if not report["candidates"]:
        lines.append("| （无） | - | - | 轨迹重复度尚未达到阈值，或已达阈值的序列均已被技能覆盖 |")
    covered = report.get("covered") or []
    if covered:
        lines += ["", "## 已被技能覆盖（不再重复提议）", "",
                  "| 工具序列 | 支持度 | 说明 |", "| --- | --- | --- |"]
        for c in covered:
            lines.append(f"| {' → '.join(c['tools'])} | {c['support']} | 已存在同步骤技能，视为已学会 |")
    config.LOGS.mkdir(parents=True, exist_ok=True)
    (config.LOGS / "mining-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

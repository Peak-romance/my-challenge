"""反思层（L3 的"回头看"）。

原则：反思必须**结构化成数据**，而不是一段散文。
每次运行产出 (quality, lesson)，lesson 带 kind/evidence/action 三要素：
- kind      ：success / failure / gap / recall_miss —— 决定它未来被怎样复用
- evidence  ：指回 T 层的 run_id，杜绝"无从查证的教训"
- action    ：可执行的下一步（不是"下次注意"，而是"补哪条路径"）

单次运行只沉淀**最多一条**最高价值教训，防止 A 层被噪声灌满。
"""

from __future__ import annotations

from .types import Plan


def evaluate(
    *,
    task: str,
    plan: Plan,
    steps: list[dict],
    output: str,
    recall: list[dict],
    error: str = "",
) -> dict:
    total = len(steps)
    ok_n = sum(1 for s in steps if s.get("ok"))
    success = (ok_n / total) if total else (1.0 if output.strip() else 0.6)

    quality = success
    if not output.strip():
        quality *= 0.4
    if error:
        quality *= 0.3
    quality = round(max(0.0, min(1.0, quality)), 3)

    short = task.replace("\n", " ")[:40]
    candidates: list[dict] = []

    if error or (total and ok_n < total):
        bad = next((s for s in steps if not s.get("ok")), {})
        reason = bad.get("err") or error or "未知原因"
        candidates.append({
            "kind": "failure",
            "importance": 0.85,
            "text": f"任务『{short}』在 `{bad.get('tool', plan.skill or '?')}` 处失败：{reason}",
            "action": "为该步骤补充前置校验或降级路径；同类失败出现两次即提升为 K 层约束",
        })

    if plan.kind == "answer":
        candidates.append({
            "kind": "gap" if not recall else "weak_skill",
            "importance": 0.7 if not recall else 0.55,
            "text": (
                f"任务『{short}』无技能覆盖且记忆层无命中（知识缺口）"
                if not recall else
                f"任务『{short}』无技能覆盖，仅靠记忆应答，未产生可复用产物"
            ),
            "action": "若同类任务第二次出现，抽为 skills/<name>/skill.json",
        })

    if plan.kind == "skill" and quality >= 0.99:
        candidates.append({
            "kind": "success",
            "importance": 0.4,
            "text": f"技能 `{plan.skill}` 一次通过『{short}』（{total} 步，quality=1.0）",
            "action": "维持；可作为该任务族的默认路径",
        })

    if not recall and plan.kind != "answer":
        candidates.append({
            "kind": "recall_miss",
            "importance": 0.5,
            "text": f"任务『{short}』的记忆召回为空：K 层缺少相关稳定事实",
            "action": "任务完成后用 memory.remember 回填背景知识",
        })

    lesson = max(candidates, key=lambda c: c["importance"]) if candidates else None
    return {"quality": quality, "lesson": lesson, "success_ratio": round(success, 3), "ok_steps": ok_n, "total_steps": total}

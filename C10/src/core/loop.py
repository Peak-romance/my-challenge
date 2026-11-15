"""循环层（L3）：把五层缝成一条可重复执行的路径。

一次运行的固定节拍
------------------
    perceive → recall → plan → act → observe → reflect → persist → respond

每一步都产出可记录的观测，因此一次运行 = 一条可回放的 T 层轨迹。
循环只做三件事：分发、守预算、记账。业务逻辑一律下沉到工具与技能，
否则循环会退化成"什么都干、什么都干不好"的上帝对象。
"""

from __future__ import annotations

import time

from .. import config
from ..memory.kstar import KStar, new_id, now_iso
from ..skills.runtime import SkillRuntime
from ..tools.builtin import build_registry
from . import reflect as reflect_mod
from .planner import build_planner
from .types import Plan, RunContext, RunResult


class Agent:
    def __init__(
        self,
        *,
        memory: KStar | None = None,
        tools=None,
        skills: SkillRuntime | None = None,
        planner=None,
        budget: config.Budget | None = None,
        verbose: bool = True,
    ):
        config.ensure_dirs()
        self.memory = memory or KStar()
        self.tools = tools or build_registry()
        self.skills = skills or SkillRuntime(self.tools)
        self.planner = planner or build_planner()
        self.budget = budget or config.DEFAULT_BUDGET
        self.verbose = verbose

    # ------------------------------------------------------------------ 主入口
    def run(
        self,
        task: str,
        *,
        source: str = "cli",
        session: str = "default",
        allow_danger: bool = False,
    ) -> RunResult:
        task = (task or "").strip()
        if not task:
            raise ValueError("任务不能为空")

        t0 = time.perf_counter()
        run_id = new_id("run")
        state = self.memory.touch_state(task=task, run_id=run_id, session=session)
        recall = self.memory.recall(task, k=self.budget.max_recall)

        ctx = RunContext(
            run_id=run_id,
            task=task,
            memory=self.memory,
            tools=self.tools,
            skills=self.skills,
            budget=self.budget,
            source=source,
            session=session,
            allow_danger=allow_danger,
            on_step=self._print_step if self.verbose else None,
        )

        if self.verbose:
            print(f"[run] {run_id} · source={source} · session={session}")
            print(f"[task] {task}")
            print(f"[recall] {len(recall)} 条 " + ("(" + ", ".join(
                f"{r.get('layer')}:{str(r.get('text',''))[:18]}" for r in recall[:3]) + ")" if recall else "（K/A 层无命中）"))
            print(f"[state] turns={state.get('turns')} open_loops={len(state.get('open_loops', []))}")

        plan = self.planner.plan(task, ctx, recall)
        if self.verbose:
            print(f"[plan] {plan.kind}" + (f" `{plan.skill}`" if plan.skill else "") + f" — {plan.rationale}")

        steps: list[dict] = []
        output = ""
        ok = True
        error = ""

        if plan.kind == "skill":
            try:
                spec = self.skills.get(plan.skill)
                res = self.skills.run(ctx, spec, plan.inputs)
                steps = res["steps"]
                output = res["output"]
                ok = res["ok"]
                error = res.get("error", "")
            except KeyError as e:
                ok, error = False, str(e)
        elif plan.kind == "tools":
            output, ok, error = self._run_tools(ctx, plan, steps)
        else:
            output = plan.answer

        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        review = reflect_mod.evaluate(
            task=task, plan=plan, steps=steps, output=output, recall=recall, error=error
        )

        self._persist(
            run_id=run_id, task=task, source=source, session=session,
            plan=plan, steps=steps, output=output, ok=ok, error=error,
            quality=review["quality"], lesson=review["lesson"],
            recall=recall, ms=elapsed_ms, ctx=ctx,
        )
        self.memory.reinforce([r.get("id") for r in recall if r.get("id")])

        if self.verbose:
            lesson = review["lesson"]
            print(f"[reflect] quality={review['quality']:.2f} "
                  f"steps={review['ok_steps']}/{review['total_steps']} "
                  f"lesson={lesson['kind'] if lesson else 'none'}")
            print("─" * 60)

        return RunResult(
            run_id=run_id, task=task, plan=plan, steps=steps, output=output,
            ok=ok, quality=review["quality"], lesson=review["lesson"],
            recall=recall, ms=elapsed_ms, error=error,
        )

    # ------------------------------------------------------------------ 分支执行
    def _run_tools(self, ctx: RunContext, plan: Plan, steps: list[dict]) -> tuple[str, bool, str]:
        outputs: list[str] = []
        t_start = time.perf_counter()
        for i, step in enumerate(plan.steps, 1):
            if ctx.steps_used >= self.budget.max_steps:
                return "\n".join(outputs), False, f"步数预算耗尽（max_steps={self.budget.max_steps}）"
            if time.perf_counter() - t_start > self.budget.run_timeout_s:
                return "\n".join(outputs), False, f"运行超时（>{self.budget.run_timeout_s}s）"
            tool = step.get("tool", "")
            res = self.tools.call(tool, step.get("args", {}) or {}, ctx)
            ctx.steps_used += 1
            rec = {
                "i": i, "id": step.get("id") or f"s{i}", "tool": tool,
                "args": step.get("args", {}) or {}, "ok": res.ok, "ms": res.ms,
                "out": (res.as_text() if res.ok else "")[:400], "err": res.error,
            }
            steps.append(rec)
            ctx.emit_step(rec)
            if not res.ok:
                return "\n".join(outputs), False, f"步骤 {i}/{tool} 失败: {res.error}"
            outputs.append(res.as_text(indent=None))
        return "\n\n".join(outputs), True, ""

    # ------------------------------------------------------------------ 记账
    def _persist(self, **kw) -> None:
        ctx: RunContext = kw["ctx"]
        plan: Plan = kw["plan"]
        trace = {
            "run_id": kw["run_id"],
            "ts": now_iso(),
            "source": kw["source"],
            "session": kw["session"],
            "task": kw["task"],
            "planner": getattr(self.planner, "name", "unknown"),
            "plan": plan.to_dict(),
            "recall": [
                {"id": r.get("id"), "layer": r.get("layer"), "score": r.get("_score"),
                 "text": str(r.get("text", ""))[:80]}
                for r in kw["recall"]
            ],
            "steps": kw["steps"],
            "steps_used": ctx.steps_used,
            "output": kw["output"][:1200],
            "ok": kw["ok"],
            "error": kw["error"],
            "quality": kw["quality"],
            "ms": kw["ms"],
            "lesson": kw["lesson"],
        }
        self.memory.append_trace(trace)

        lesson = kw["lesson"]
        if lesson:
            self.memory.write_lesson(
                kind=lesson["kind"],
                text=lesson["text"],
                evidence=kw["run_id"],
                action=lesson.get("action", ""),
                importance=lesson.get("importance", 0.6),
            )

        # S 层焦点跟随最近一次任务；显式待办交给 memory.open_loop 登记
        st = self.memory.state()
        st["focus"] = kw["task"][:120]
        self.memory.save_state(st)

    def _print_step(self, rec: dict) -> None:
        mark = "ok  " if rec["ok"] else "FAIL"
        line = f"  [{rec['i']}] {rec['tool']:<20} {mark} {rec['ms']:>5}ms"
        if rec["ok"]:
            digest = (rec.get("out") or "").replace("\n", " ")[:60]
            if digest:
                line += f"  {digest}"
        else:
            line += f"  {rec.get('err', '')[:80]}"
        print(line)

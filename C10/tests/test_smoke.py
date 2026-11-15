"""零依赖冒烟测试：python tests/test_smoke.py

覆盖五层的关键契约，而不是覆盖率数字：
- L5 记忆：去重、召回、教训沉淀、遗忘
- L2 工具：沙箱越界拒绝、危险级拦截
- L4 技能：装载校验、模板渲染、预算熔断
- L3 循环：端到端任务、异常降级、反思写入

测试在临时目录里跑（C10_ROOT 重定向），绝不污染真实记忆。
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
TMP = Path(tempfile.mkdtemp(prefix="c10-test-"))
os.environ["C10_ROOT"] = str(TMP)
sys.path.insert(0, str(PROJECT))

# 复制技能库到临时根，模拟真实装载路径。
# 同时移除"后来才进化出来的技能"，让测试从"尚未学会"的起点开始——
# 否则进化闭环的断言会因为现状已覆盖而永远通过（假阳性）。
shutil.copytree(PROJECT / "skills", TMP / "skills")
shutil.rmtree(TMP / "skills" / "memorize-loop", ignore_errors=True)
shutil.rmtree(TMP / "skills" / "_proposed", ignore_errors=True)

from src import config  # noqa: E402
from src.core import miner  # noqa: E402
from src.core.loop import Agent  # noqa: E402
from src.memory import retrieve  # noqa: E402
from src.memory.kstar import KStar  # noqa: E402
from src.skills.loader import load_all, validate  # noqa: E402
from src.skills.runtime import render, render_obj  # noqa: E402
from src.tools.builtin import build_registry  # noqa: E402

PASS, FAIL = [], []


def check(name: str, fn):
    try:
        fn()
        PASS.append(name)
        print(f"  PASS  {name}")
    except Exception as e:
        FAIL.append((name, f"{type(e).__name__}: {e}"))
        print(f"  FAIL  {name} -> {type(e).__name__}: {e}")


# ------------------------------------------------------------------ L5 检索
def t_tokenize():
    toks = retrieve.tokenize("长期智能体的记忆系统")
    assert "记忆" in toks and "智能" in toks, toks
    assert "一下" not in retrieve.tokenize("想一下"), "停用词未被过滤"
    assert retrieve.tokenize("") == []


def t_rank_relevance():
    docs = [
        {"text": "记忆系统需要分层：知识、状态、轨迹、归档", "importance": 0.8, "created": "2026-11-15T00:00:00"},
        {"text": "今天午餐吃了牛肉面", "importance": 0.9, "created": "2026-11-15T00:00:00"},
    ]
    hits = retrieve.rank("记忆系统怎么分层", docs, top_k=2)
    assert hits and "记忆" in hits[0]["text"], hits
    assert retrieve.rank("区块链共识算法", docs, top_k=2) == [], "无关查询必须返回空召回"


# ------------------------------------------------------------------ L5 KSTAR
def t_kstar_knowledge():
    ks = KStar(TMP / "memory")
    a = ks.remember("测试事实：写权限边界是项目根", tags="test")
    b = ks.remember("测试事实：写权限边界是项目根", tags="more")
    assert a["id"] == b["id"] and b.get("_dedup"), "同文应去重"
    assert int(b["use_count"]) == 2
    hits = ks.recall("写权限边界", k=3)
    assert hits and hits[0]["id"] == a["id"]


def t_kstar_lesson():
    ks = KStar(TMP / "memory")
    l1 = ks.write_lesson(kind="failure", text="巡检任务在 fs.list 失败", evidence="run-1")
    l2 = ks.write_lesson(kind="failure", text="巡检任务在 fs.list 失败", evidence="run-2")
    assert l1["id"] == l2["id"], "同类同文教训应合并"
    assert float(l2["importance"]) > float(l1["importance"])


def t_kstar_state_and_trace():
    ks = KStar(TMP / "memory")
    st = ks.touch_state(task="单元测试任务", run_id="run-x")
    assert st["turns"] >= 1
    ks.add_open_loop("验证 open_loop 落盘")
    assert any("open_loop" in l["text"] for l in ks.state()["open_loops"])
    closed = ks.close_open_loop("open_loop")
    assert closed == 1
    ks.append_trace({"run_id": "run-x", "ts": "2026-11-15T10:00:00+08:00",
                     "task": "单元测试任务", "plan": {"kind": "tools"},
                     "steps": [{"tool": "time.now", "ok": True}], "ok": True, "quality": 1.0})
    assert any(t["run_id"] == "run-x" for t in ks.read_traces())


def t_kstar_decay():
    ks = KStar(TMP / "memory")
    rec = ks.remember("一条很久以前、只被用过一次的旧事实", importance=0.16)
    path = ks.k_file
    recs = ks._read(path)
    for r in recs:
        if r["id"] == rec["id"]:
            r["last_used"] = "2020-01-01T00:00:00+00:00"
            r["importance"] = 0.16
    ks._rewrite(path, recs)
    ks.decay()
    after = [r for r in ks._read(path) if r["id"] == rec["id"]][0]
    assert after["status"] == "archived", after


# ------------------------------------------------------------------ L2 工具
def t_tool_sandbox():
    reg = build_registry()

    class Ctx:
        run_id, task, depth, steps_used, allow_danger = "t", "t", 0, 0, False
        memory, skills, tools = None, None, reg
        budget = config.DEFAULT_BUDGET
        def emit_step(self, rec): ...
        on_step = None

    out = reg.call("fs.write", {"path": str(TMP / "a.txt"), "content": "hi"}, Ctx())
    assert out.ok, out.error
    bad = reg.call("fs.write", {"path": "C:/Windows/System32/evil.txt", "content": "x"}, Ctx())
    assert not bad.ok and "越界" in bad.error, bad.error
    denied = reg.call("shell.run", {"cmd": "python -V"}, Ctx())
    assert not denied.ok and "危险" in denied.error, denied.error
    blocked = reg.call("shell.run", {"cmd": "rm -rf /"}, Ctx())
    assert not blocked.ok
    unknown = reg.call("fs.write", {"path": "x.txt", "content": "y", "oops": 1}, Ctx())
    assert not unknown.ok and "不接受参数" in unknown.error


# ------------------------------------------------------------------ L4 技能
def t_skill_load_validate():
    skills, warns = load_all(TMP / "skills")
    assert len(skills) >= 5, skills.keys()
    assert not warns, warns
    reg = build_registry()
    for name, spec in skills.items():
        problems = validate(spec, reg.names())
        assert not problems, f"{name}: {problems}"


def t_render():
    vars = {"input": {"path": "src/tools"}, "st": {"open_loops": ["a", "b"]}, "n": 3}
    assert render("路径={input.path}", vars) == "路径=src/tools"
    assert render("{n} 条", vars) == "3 条"
    assert render("{missing.deep} 结尾", vars) == " 结尾"
    assert render('{{"k": 1}}', vars) == '{"k": 1}', "字面量转义失效"
    assert render_obj({"a": "{n}", "b": ["{input.path}"]}, vars) == {"a": "3", "b": ["src/tools"]}


def t_skill_budget_guard():
    agent = Agent(memory=KStar(TMP / "memory"), verbose=False,
                  budget=config.Budget(max_steps=1))
    res = agent.run("生成今日简报")
    assert not res.ok and "预算" in res.error, (res.ok, res.error)


# ------------------------------------------------------------------ L3 循环
def t_end_to_end():
    agent = Agent(memory=KStar(TMP / "memory"), verbose=False)
    r1 = agent.run("记住：C10 的测试约定是零依赖")
    assert r1.ok and "id" in r1.output
    r2 = agent.run("生成今日简报")
    assert r2.ok and "今日简报" in r2.output, r2.output
    r3 = agent.run("这是一个没有任何技能覆盖的奇怪任务：量子纠缠调参")
    assert r3.plan.kind == "answer" and r3.lesson["kind"] in ("gap", "weak_skill"), r3.lesson
    traces = agent.memory.read_traces()
    assert len(traces) >= 3
    assert all("run_id" in t and "quality" in t for t in traces)


def t_miner():
    agent = Agent(memory=KStar(TMP / "memory"), verbose=False)
    for _ in range(3):
        agent.run("记住：挖掘器测试事实 A；记个待办：挖掘器测试待办 B")
    rep = miner.mine(agent.memory, min_support=2, skills_root=TMP / "skills")
    assert rep["candidates"], rep
    assert rep["written"], "草案应落盘"
    proposed = json.loads(Path(rep["written"][0]).read_text(encoding="utf-8"))
    assert proposed["status"] == "proposed"
    name = proposed["name"]
    dst = miner.promote(name, skills_root=TMP / "skills")
    assert (dst / "skill.json").exists()
    assert json.loads((dst / "skill.json").read_text(encoding="utf-8"))["status"] == "active"

    # 进化闭环：草案上线后，同样的组合指令应改走技能而不是重新拼装
    agent.skills.reload()
    r = agent.run("记住：进化闭环测试事实；记个待办：进化闭环测试待办")
    assert r.plan.kind == "skill" and r.plan.skill == name, (r.plan.kind, r.plan.skill)


def main() -> int:
    print(f"[env] C10_ROOT={TMP}")
    groups = [
        ("L5 检索", [t_tokenize, t_rank_relevance]),
        ("L5 记忆（KSTAR）", [t_kstar_knowledge, t_kstar_lesson, t_kstar_state_and_trace, t_kstar_decay]),
        ("L2 工具", [t_tool_sandbox]),
        ("L4 技能", [t_skill_load_validate, t_render, t_skill_budget_guard]),
        ("L3 循环", [t_end_to_end, t_miner]),
    ]
    for title, fns in groups:
        print(f"\n{title}")
        for fn in fns:
            check(fn.__name__, fn)

    print(f"\n结果：{len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        for name, err in FAIL:
            print(f"  - {name}: {err}")
        return 1
    return 0


if __name__ == "__main__":
    code = main()
    shutil.rmtree(TMP, ignore_errors=True)
    raise SystemExit(code)

"""规划层（L3 的"想"）。

两种规划器，同一接口
--------------------
- RulePlanner：离线、确定、零依赖。负责意图识别 + 技能触发词匹配 + 兜底应答。
- LLMPlanner ：可选的 LLM 规划（OpenAI 兼容接口），输出严格 JSON 计划；
               任何异常自动降级到 RulePlanner，保证"有网更好、没网也能跑"。

这是刻意的工程取舍：**可运行性优先于智能上限**。没有 API Key 的评审者
也必须能在 30 秒内跑通全链路，否则再漂亮的架构也是纸面的。
"""

from __future__ import annotations

import json
import re
import urllib.request

from .. import config
from .types import Plan

REMEMBER_RX = re.compile(r"(?:记住|记下|remember)\s*[:：,，]?\s*(.+)", re.I)
TODO_RX = re.compile(r"(?:待办|todo|未闭环|open\s*loop)\s*[:：,，]?\s*(.+)", re.I)
STATUS_WORDS = ("状态", "进度", "到哪了", "待办清单", "status", "进行到")
CLOSE_RX = re.compile(r"(?:完成|关闭|销掉|结了|done)\s*[:：,，]?\s*(.+)", re.I)


def extract_path(task: str) -> str:
    """从自然语言里抠出路径型实参（含 / 或 \\ 或带扩展名的 token）。"""
    for tok in re.split(r"[\s，,：:；;、]+", task):
        t = tok.strip("`'\"()（）[]【】").rstrip("。.")
        if not t:
            continue
        if "/" in t or "\\" in t or re.search(r"\.[A-Za-z0-9]{1,5}$", t):
            return t
    return ""


def derive_inputs(spec, task: str) -> dict:
    """把任务文本映射到技能声明的输入契约。

    只做**保守推断**：认不出就交给技能默认值。
    宁可让技能用默认值跑出可解释的结果，也不要塞进一个猜错的实参——
    错误实参会静默产出错误产物，比失败更难发现。
    """
    out: dict = {}
    for name, idef in (spec.inputs or {}).items():
        if name in ("focus", "task"):
            out[name] = task
        elif name == "path":
            p = extract_path(task)
            if p:
                out[name] = p
        elif name == "days":
            m = re.search(r"(\d+)\s*(天|日|days?)", task)
            if m:
                out[name] = int(m.group(1))
        elif name == "text":
            cleaned = re.sub(r"^.*?(?:记录一下|记录|捕获|记一笔|capture)\s*[:：]?\s*", "", task, flags=re.I)
            if cleaned.strip():
                out[name] = cleaned.strip()
        # 其它输入不猜，交给 default / required 校验
    return out



_PREFIX_RX = re.compile(
    r"^\s*(?:记住|记下|记个待办|待办|记录一下|记录|remember|todo)\s*[:：,，]?\s*", re.I
)


def clean_part(part: str) -> str:
    return _PREFIX_RX.sub("", part or "").strip()


class RulePlanner:
    name = "rule"

    # ---------------------------------------------------------------- 子意图
    def _single_intent(self, text: str, ctx) -> dict | None:
        """把一段短句解析成单步工具调用；解析不出返回 None。"""
        text = (text or "").strip()
        if not text:
            return None
        m = REMEMBER_RX.search(text)
        if m:
            return {"tool": "memory.remember", "args": {"text": m.group(1).strip(), "tags": "cli"}}
        m = TODO_RX.search(text)
        if m:
            return {"tool": "memory.open_loop", "args": {"text": m.group(1).strip()}}
        m = CLOSE_RX.search(text)
        if m:
            return {"tool": "memory.close_loop", "args": {"keyword": m.group(1).strip()}}
        if any(w in text.lower() for w in STATUS_WORDS):
            return {"tool": "memory.state", "args": {}}
        spec, score = ctx.skills.match(text)
        if spec and score > 0:
            return {"tool": "skill.run", "args": {"name": spec.name, "inputs": derive_inputs(spec, text)}}
        return None

    def _compose(self, task: str, ctx) -> Plan | None:
        """多意图分解：一句话里塞了多件事时，拆成顺序步骤而不是只执行第一件。

        这是"循环层"最容易被忽略的能力——真实指令几乎从不单步。

        进化闭环：若这组工具序列已经被某个技能覆盖（哪怕它是上次才被挖掘上线的），
        则**直接走技能**而不是重新拼装。这样"重复劳动被抽象掉"是可观测的行为变化，
        而不只是文档里的一句承诺。
        """
        parts = [p.strip() for p in re.split(r"[；;]|，?然后|，?接着|，?之后|\.\s+", task) if p.strip()]
        if len(parts) < 2:
            return None
        steps = []
        for p in parts:
            st = self._single_intent(p, ctx)
            if st is None:
                return None          # 有一段解析不了就整体放弃，交回常规路径
            steps.append(st)

        sig = tuple(s["tool"] for s in steps)
        for spec in ctx.skills.all():
            if len(spec.steps) == len(steps) and tuple(s.get("tool") for s in spec.steps) == sig:
                inputs = derive_inputs(spec, task)
                for (iname, _idef), part in zip(spec.inputs.items(), parts):
                    inputs.setdefault(iname, clean_part(part))
                return Plan(
                    kind="skill", skill=spec.name, inputs=inputs,
                    rationale=f"该组合已被技能 `{spec.name}` 覆盖 → 走技能（进化闭环）",
                )

        return Plan(kind="tools", steps=steps,
                    rationale=f"多意图分解：识别到 {len(steps)} 个可执行子任务")

    def plan(self, task: str, ctx, recall: list[dict]) -> Plan:
        task = (task or "").strip()

        # 1) 显式指定技能：@skill-name 输入
        m = re.match(r"^@([A-Za-z0-9_\-]+)\s*(.*)$", task, re.S)
        if m and m.group(1) in ctx.skills.skills:
            return Plan(
                kind="skill",
                skill=m.group(1),
                inputs={"task": m.group(2).strip(), "focus": m.group(2).strip()},
                rationale=f"用户显式指定技能 @{m.group(1)}",
            )

        # 2) 多意图分解（必须先于单意图，否则"记住A；待办B"只会执行前半句）
        composed = self._compose(task, ctx)
        if composed:
            return composed

        # 3) 明确的记忆写/读意图（不依赖技能，即时生效）
        m = REMEMBER_RX.search(task)
        if m:
            return Plan(
                kind="tools",
                steps=[{"tool": "memory.remember", "args": {"text": m.group(1).strip(), "tags": "cli"}}],
                rationale="识别到『记住』意图 → 写入 K 层",
            )
        m = TODO_RX.search(task)
        if m:
            return Plan(
                kind="tools",
                steps=[{"tool": "memory.open_loop", "args": {"text": m.group(1).strip()}}],
                rationale="识别到『待办』意图 → 登记到 S 层未闭环事项",
            )
        m = CLOSE_RX.search(task)
        if m:
            return Plan(
                kind="tools",
                steps=[{"tool": "memory.close_loop", "args": {"keyword": m.group(1).strip()}}],
                rationale="识别到『闭环』意图 → 关闭 S 层对应未闭环事项",
            )
        # 4) 技能触发词匹配（比泛化关键词更具体，优先级高于状态查询）
        spec, score = ctx.skills.match(task)
        if spec and score > 0:
            inputs = {"focus": task, "task": task}
            inputs.update(derive_inputs(spec, task))
            return Plan(
                kind="skill",
                skill=spec.name,
                inputs=inputs,
                rationale=f"触发词命中技能 `{spec.name}`（score={score}）",
            )

        # 5) 状态查询（泛指，放在技能匹配之后，避免抢走 self-check 等专指技能）
        if any(w in task.lower() for w in STATUS_WORDS):
            return Plan(
                kind="tools",
                steps=[{"tool": "memory.state", "args": {}}],
                rationale="识别到『状态查询』意图 → 读取 S 层",
            )

        # 6) 兜底：基于 K/A 记忆组织应答（知识缺口会在反思阶段被登记）
        if recall:
            lines = [f"未匹配到可执行技能，已基于记忆层给出参考（召回 {len(recall)} 条）：", ""]
            for r in recall[:5]:
                tag = "知识" if r.get("layer") == "K" else "复盘"
                lines.append(f"- [{tag} · {r.get('id')}] {str(r.get('text', ''))[:160]}")
            answer = "\n".join(lines)
        else:
            answer = (
                "未匹配到可执行技能，且记忆层无相关条目。\n"
                "这是一个知识缺口：建议把该任务抽象为一个技能（skills/<name>/skill.json），"
                "或先用『记住：…』把背景写入 K 层。"
            )
        return Plan(kind="answer", answer=answer, rationale="无技能命中、无明确工具意图 → 记忆增强应答")


SYSTEM_PROMPT = """你是 C10 第二大脑的规划器。只能输出一个 JSON 对象，不要输出解释文字。
可选 kind:
- {"kind":"skill","skill":"<技能名>","inputs":{...},"rationale":"..."}
- {"kind":"tools","steps":[{"tool":"<工具名>","args":{...}}],"rationale":"..."}
- {"kind":"answer","answer":"<直接回答>","rationale":"..."}
优先复用已有技能；其次组合工具；最后才直接回答。
"""


class LLMPlanner:
    name = "llm"

    def __init__(self, fallback: RulePlanner | None = None):
        self.fallback = fallback or RulePlanner()
        self.last_error = ""

    @property
    def available(self) -> bool:
        return bool(config.LLM_BASE_URL and config.LLM_API_KEY)

    def _catalog(self, ctx) -> str:
        skills = [f"- {s.name} v{s.version}: {s.description} (触发词: {', '.join(s.triggers[:5])})"
                  for s in ctx.skills.all()]
        tools = [f"- {t['name']}({', '.join(t['params'])}) [{t['danger']}]: {t['description']}"
                 for t in ctx.tools.specs()]
        return "可用技能:\n" + "\n".join(skills) + "\n\n可用工具（[危险级]）:\n" + "\n".join(tools)

    def plan(self, task: str, ctx, recall: list[dict]) -> Plan:
        if not self.available:
            return self.fallback.plan(task, ctx, recall)
        mem = "\n".join(f"- [{r.get('layer')}] {r.get('text')}" for r in recall[:5]) or "（无）"
        payload = {
            "model": config.LLM_MODEL,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT + "\n" + self._catalog(ctx)},
                {"role": "user", "content": f"任务：{task}\n\n相关记忆：\n{mem}"},
            ],
        }
        try:
            req = urllib.request.Request(
                config.LLM_BASE_URL.rstrip("/") + "/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {config.LLM_API_KEY}"},
            )
            with urllib.request.urlopen(req, timeout=config.LLM_TIMEOUT_S) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            plan = self._parse(content)
            if plan:
                plan.rationale = f"[llm] {plan.rationale}"
                return plan
            self.last_error = "LLM 输出无法解析为计划"
        except Exception as e:
            self.last_error = f"{type(e).__name__}: {e}"
        return self.fallback.plan(task, ctx, recall)

    @staticmethod
    def _parse(content: str) -> Plan | None:
        m = re.search(r"\{.*\}", content, re.S)
        if not m:
            return None
        try:
            d = json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
        kind = d.get("kind")
        if kind == "skill" and d.get("skill"):
            return Plan(kind="skill", skill=d["skill"], inputs=d.get("inputs", {}),
                        rationale=d.get("rationale", ""))
        if kind == "tools" and d.get("steps"):
            return Plan(kind="tools", steps=d["steps"], rationale=d.get("rationale", ""))
        if kind == "answer" and d.get("answer"):
            return Plan(kind="answer", answer=d["answer"], rationale=d.get("rationale", ""))
        return None


def build_planner() -> RulePlanner | LLMPlanner:
    if config.LLM_BASE_URL and config.LLM_API_KEY:
        return LLMPlanner()
    return RulePlanner()

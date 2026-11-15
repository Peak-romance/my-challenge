"""KSTAR 四层记忆存储（L5 的落地实现）。

四层定义
--------
K · Knowledge   语义层：可长期复用的稳定事实、偏好、规则、领域结论。
S · State       情境层：本次会话的工作状态（目标、未闭环事项、焦点）。容量小、读写频繁。
T · Trajectory  轨迹层：每次任务的可回放执行记录（计划/步骤/结果/耗时）。
A · Archive     归档层：从轨迹中蒸馏的复盘与教训（R = Reflection 沉淀于此）。

写入策略（为什么这样分层）
-------------------------
- K 只接受**被试错/复核过**的结论：写入需显式调用，且同文去重，重要度随命中次数上浮。
- S 每轮自动更新，但有容量上限与淘汰规则，避免变成第二份垃圾堆。
- T 全量追加、只追加不改写，保证"可追溯"是不可协商的。
- A 只由反思模块写入，且必须带 evidence（指向 T 的 run_id），否则视为无根之谈。

读取策略
--------
K/A 走混合检索（BM25 + 时间衰减 + 重要度）；S 直读；T 只用于回放与挖掘，不进入上下文。
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .. import config
from . import retrieve

MAX_STATE_RECENT = 10
MAX_OPEN_LOOPS = 12


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", (text or "")).lower()


class KStar:
    """四层记忆的唯一入口。所有层都不允许被业务代码直接读写文件。"""

    def __init__(self, root: Path | None = None):
        base = Path(root) if root else config.MEM
        self.mem_dir = base
        self.k_file = base / "k" / "knowledge.jsonl"
        self.a_file = base / "a" / "lessons.jsonl"
        self.s_file = base / "s" / "state.json"
        self.t_dir = base / "t"
        for p in (self.k_file.parent, self.a_file.parent, self.s_file.parent, self.t_dir):
            p.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ 基础 IO
    @staticmethod
    def _read(path: Path) -> list[dict]:
        if not path.exists():
            return []
        out: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # 容错：跳过损坏行，绝不因一行脏数据丢掉整层记忆
        return out

    @staticmethod
    def _append(path: Path, rec: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    @staticmethod
    def _rewrite(path: Path, recs: Iterable[dict]) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        tmp.replace(path)  # 原子替换，避免半写损坏

    # ------------------------------------------------------------------ K 层
    def remember(
        self,
        text: str,
        *,
        tags: str | list[str] = "",
        source: str = "agent",
        importance: float = 0.6,
        confidence: float = 0.8,
        kind: str = "fact",
    ) -> dict:
        """写入 K 层；同文去重，重复写入只增强不重复膨胀。"""
        text = (text or "").strip()
        if not text:
            raise ValueError("remember: text 不能为空")
        tag_list = [t.strip() for t in (tags.split(",") if isinstance(tags, str) else tags) if t.strip()]
        key = _norm(text)

        recs = self._read(self.k_file)
        for r in recs:
            if _norm(r.get("text", "")) == key:
                r["use_count"] = int(r.get("use_count", 1)) + 1
                r["importance"] = round(min(1.0, float(r.get("importance", 0.6)) + 0.05), 3)
                r["last_used"] = now_iso()
                r["tags"] = sorted(set(r.get("tags", [])) | set(tag_list))
                self._rewrite(self.k_file, recs)
                r["_dedup"] = True
                return r

        rec = {
            "id": new_id("k"),
            "layer": "K",
            "kind": kind,
            "text": text,
            "tags": tag_list,
            "source": source,
            "importance": round(float(importance), 3),
            "confidence": round(float(confidence), 3),
            "created": now_iso(),
            "last_used": now_iso(),
            "use_count": 1,
            "status": "active",
        }
        self._append(self.k_file, rec)
        return rec

    def knowledge(self, include_archived: bool = False) -> list[dict]:
        recs = self._read(self.k_file)
        if include_archived:
            return recs
        return [r for r in recs if r.get("status", "active") == "active"]

    # ------------------------------------------------------------------ A 层
    def write_lesson(
        self,
        *,
        kind: str,
        text: str,
        evidence: str = "",
        action: str = "",
        importance: float = 0.6,
    ) -> dict:
        """写入 A 层。evidence 必须能指回 T 层的 run_id，否则复盘不可追溯。"""
        rec = {
            "id": new_id("a"),
            "layer": "A",
            "kind": kind,             # success | failure | gap | preference
            "text": (text or "").strip(),
            "evidence": evidence,
            "action": action,
            "importance": round(float(importance), 3),
            "created": now_iso(),
            "last_used": now_iso(),
            "use_count": 1,
            "status": "active",
        }
        if not rec["text"]:
            raise ValueError("write_lesson: text 不能为空")

        # 同类同文去重：重复发生的教训应当"变得更重"，而不是"变得更多"。
        # 否则 A 层会在几十次运行后被同一条教训淹没，复盘价值被稀释。
        recs = self._read(self.a_file)
        key = _norm(rec["text"])
        for r in recs:
            if _norm(r.get("text", "")) == key and r.get("kind") == rec["kind"]:
                r["use_count"] = int(r.get("use_count", 1)) + 1
                r["importance"] = round(min(1.0, float(r.get("importance", 0.6)) + 0.05), 3)
                r["last_used"] = now_iso()
                r["evidence"] = rec["evidence"] or r.get("evidence", "")
                self._rewrite(self.a_file, recs)
                r["_dedup"] = True
                return r

        self._append(self.a_file, rec)
        return rec

    def lessons(self) -> list[dict]:
        return [r for r in self._read(self.a_file) if r.get("status", "active") == "active"]

    # ------------------------------------------------------------------ S 层
    def state(self) -> dict:
        if not self.s_file.exists():
            st = {
                "session": "default",
                "turns": 0,
                "created": now_iso(),
                "updated": now_iso(),
                "focus": "",
                "last_task": "",
                "open_loops": [],
                "recent": [],
            }
            self.save_state(st)
            return st
        try:
            return json.loads(self.s_file.read_text(encoding="utf-8"))
        except Exception:
            # 状态层损坏不应导致任务失败：重建并以空状态继续
            st = {"session": "default", "turns": 0, "focus": "", "last_task": "",
                  "open_loops": [], "recent": [], "created": now_iso(),
                  "updated": now_iso(), "_recovered": True}
            self.save_state(st)
            return st

    def save_state(self, st: dict) -> None:
        st["updated"] = now_iso()
        st["open_loops"] = st.get("open_loops", [])[-MAX_OPEN_LOOPS:]
        st["recent"] = st.get("recent", [])[-MAX_STATE_RECENT:]
        tmp = self.s_file.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.s_file)

    def touch_state(self, *, task: str, run_id: str, session: str = "default") -> dict:
        st = self.state()
        st["session"] = session
        st["turns"] = int(st.get("turns", 0)) + 1
        st["last_task"] = task
        st["recent"] = st.get("recent", []) + [
            {"ts": now_iso(), "task": task[:120], "run_id": run_id}
        ]
        self.save_state(st)
        return st

    def add_open_loop(self, text: str) -> dict:
        st = self.state()
        loops = st.setdefault("open_loops", [])
        key = _norm(text)
        for l in loops:
            if _norm(l.get("text", "")) == key:   # 同一件事只登记一次，避免 S 层被重复项灌满
                return st
        loops.append({"id": new_id("loop"), "text": text, "created": now_iso()})
        self.save_state(st)
        return st

    def close_open_loop(self, keyword: str) -> int:
        st = self.state()
        loops = st.get("open_loops", [])
        keep = [l for l in loops if keyword and keyword not in l.get("text", "")]
        st["open_loops"] = keep
        self.save_state(st)
        return len(loops) - len(keep)

    # ------------------------------------------------------------------ T 层
    def append_trace(self, rec: dict) -> Path:
        day = (rec.get("ts") or now_iso())[:10]
        path = self.t_dir / f"{day}.jsonl"
        self._append(path, rec)
        return path

    def read_traces(self, days: int = 30) -> list[dict]:
        files = sorted(self.t_dir.glob("*.jsonl"))[-days:]
        out: list[dict] = []
        for f in files:
            out.extend(self._read(f))
        return out

    # ------------------------------------------------------------------ 检索
    def recall(self, query: str, *, k: int = 5, layers: tuple[str, ...] = ("K", "A")) -> list[dict]:
        docs: list[dict] = []
        if "K" in layers:
            docs += self.knowledge()
        if "A" in layers:
            docs += self.lessons()
        return retrieve.rank(query, docs, top_k=k)

    def reinforce(self, ids: Iterable[str]) -> int:
        """命中即强化：把"被用过"这件事写回记忆，让检索越用越准。"""
        ids = {i for i in ids if i}
        if not ids:
            return 0
        hit = 0
        for path, layer_key in ((self.k_file, "knowledge"), (self.a_file, "lessons")):
            recs = self._read(path)
            changed = False
            for r in recs:
                if r.get("id") in ids:
                    r["use_count"] = int(r.get("use_count", 1)) + 1
                    r["last_used"] = now_iso()
                    r["importance"] = round(min(1.0, float(r.get("importance", 0.6)) + 0.02), 3)
                    changed = True
                    hit += 1
            if changed:
                self._rewrite(path, recs)
        return hit

    # ------------------------------------------------------------------ 维护
    def decay(self, *, floor: float = 0.15, factor: float = 0.97) -> dict:
        """遗忘曲线：长期未被使用（且低重要度）的记忆降权，低于阈值转 archived。

        目的不是"删记忆"，而是让检索空间保持信噪比——归档保留，随时可捞回。
        """
        archived = decayed = 0
        recs = self._read(self.k_file)
        for r in recs:
            if r.get("status") != "active":
                continue
            age = retrieve.age_days(r.get("last_used") or r.get("created", ""))
            if age < 7:
                continue
            imp = float(r.get("importance", 0.6)) * (factor ** int(age // 7))
            r["importance"] = round(max(0.0, imp), 3)
            if r["importance"] < floor and int(r.get("use_count", 1)) <= 1:
                r["status"] = "archived"
                archived += 1
            else:
                decayed += 1
        self._rewrite(self.k_file, recs)
        return {"decayed": decayed, "archived": archived, "total": len(recs)}

    def stats(self) -> dict:
        traces = self.read_traces(days=365)
        st = self.state()
        return {
            "K_knowledge": len(self.knowledge()),
            "K_archived": len(self.knowledge(include_archived=True)) - len(self.knowledge()),
            "S_open_loops": len(st.get("open_loops", [])),
            "S_turns": st.get("turns", 0),
            "T_traces": len(traces),
            "A_lessons": len(self.lessons()),
        }

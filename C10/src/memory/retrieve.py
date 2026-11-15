"""检索层：中文友好的 BM25 变体 + 时间衰减 + 重要度加权。

为什么不用向量检索
------------------
本地无 GPU、无 embedding 服务时，引入向量库会让"可运行"变成"需先装模型"。
本实现对中文采用【字符 unigram + 相邻 bigram】切分，无需分词词典，
在几十到几千条记忆的量级上与向量检索的召回质量差距可忽略，
且零依赖、可解释（能打印命中词，便于复盘检索为何没命中）。
"""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone

_WORD = re.compile(r"[a-zA-Z0-9_]+")
_CJK_RUN = re.compile(r"[\u4e00-\u9fff]+")

BM25_K1 = 1.2
BM25_B = 0.6

# 停用词：中文虚词与高频套话。不过滤会让"一下 / 这个 / 需要"这类二元组
# 把无关记忆顶到召回前列——噪声召回比召回失败更危险，因为它看起来是"有依据的"。
_CJK_STOP = {
    "一下", "这个", "那个", "什么", "怎么", "可以", "需要", "我们", "你们", "他们",
    "一个", "这些", "那些", "就是", "然后", "还是", "已经", "如果", "因为", "所以",
    "但是", "而且", "以及", "没有", "不是", "是否", "可能", "应该", "必须", "目前",
    "现在", "进行", "对于", "关于", "通过", "根据", "由于", "并且", "或者", "不过",
    "时候", "东西", "问题", "这样", "那样", "一些", "有点", "比较", "非常",
}
_CJK_CHAR_STOP = set("的了吗呢吧啊是在和与及或把被给对为上下中个一不也就都还又很更最这那你我他它们着过")


def tokenize(text: str) -> list[str]:
    """英文按词；中文按相邻二元组为主（单字仅在整词仅一字时保留）。

    只用单字会引入大量虚词噪声，只用二元组又会漏掉"书"这类独字查询，
    因此采用"二元组 + 独字兜底 + 停用词过滤"的组合。
    """
    text = (text or "").lower()
    if not text:
        return []
    toks = _WORD.findall(text)
    for run in _CJK_RUN.findall(text):
        if len(run) == 1:
            if run not in _CJK_CHAR_STOP:
                toks.append(run)
            continue
        for i in range(len(run) - 1):
            bg = run[i:i + 2]
            if bg in _CJK_STOP:
                continue
            if bg[0] in _CJK_CHAR_STOP and bg[1] in _CJK_CHAR_STOP:
                continue
            toks.append(bg)
    return toks


def _now() -> datetime:
    return datetime.now(timezone.utc)


def age_days(ts: str) -> float:
    """输入 ISO 时间串，返回距今的天数；解析失败按 365 天计（即几乎不衰减）。"""
    try:
        t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return max(0.0, (_now() - t).total_seconds() / 86400.0)
    except Exception:
        return 365.0


def recency_factor(ts: str, half_life_days: float = 30.0) -> float:
    """半衰期衰减：30 天前的记忆权重 0.5。"""
    return 0.5 ** (age_days(ts) / half_life_days)


def bm25(query: str, docs: list[dict], text_key: str = "text") -> list[float]:
    """对 docs 逐条打分，返回与 docs 对齐的分数列表。"""
    q = set(tokenize(query))
    if not q or not docs:
        return [0.0] * len(docs)

    doc_tokens = [tokenize(d.get(text_key, "") + " " + " ".join(d.get("tags") or [])) for d in docs]
    n = len(docs)
    avgdl = (sum(len(t) for t in doc_tokens) / n) or 1.0

    df: dict[str, int] = {}
    for toks in doc_tokens:
        for term in set(toks) & q:
            df[term] = df.get(term, 0) + 1

    scores: list[float] = []
    for toks in doc_tokens:
        tf: dict[str, int] = {}
        for term in toks:
            if term in q:
                tf[term] = tf.get(term, 0) + 1
        s = 0.0
        for term, cnt in tf.items():
            idf = math.log(1.0 + (n - df.get(term, 0) + 0.5) / (df.get(term, 0) + 0.5))
            denom = cnt + BM25_K1 * (1 - BM25_B + BM25_B * len(toks) / avgdl)
            s += idf * (cnt * (BM25_K1 + 1)) / denom
        scores.append(s)
    return scores


def rank(
    query: str,
    docs: list[dict],
    *,
    top_k: int = 5,
    text_key: str = "text",
    importance_key: str = "importance",
    time_key: str = "created",
    half_life_days: float = 30.0,
) -> list[dict]:
    """混合排序：BM25 × 重要度权重 + 时间衰减加成。

    返回的每条结果附加 `_score` / `_hit`（命中的查询词），便于解释与复盘。
    """
    if not docs:
        return []
    base = bm25(query, docs, text_key=text_key)
    q_terms = set(tokenize(query))
    out: list[dict] = []
    for doc, s in zip(docs, base):
        # 无词面命中的条目一律不进召回集：宁可返回空（暴露知识缺口），
        # 也不要用"高重要度但不相关"的记忆污染上下文——这是记忆系统最常见的噪声源。
        if s <= 1e-9:
            continue
        importance = float(doc.get(importance_key, 0.5) or 0.5)
        decay = recency_factor(doc.get(time_key, ""), half_life_days)
        use_norm = min(1.0, float(doc.get("use_count", 0) or 0) / 10.0)
        final = s * (0.6 + 0.4 * importance) + 0.35 * decay + 0.15 * use_norm
        hit = sorted(term for term in (set(tokenize(doc.get(text_key, ""))) & q_terms) if len(term) > 1)
        rec = dict(doc)
        rec["_score"] = round(final, 4)
        rec["_hit"] = hit[:8]
        out.append(rec)
    out.sort(key=lambda r: r["_score"], reverse=True)
    return out[:top_k]

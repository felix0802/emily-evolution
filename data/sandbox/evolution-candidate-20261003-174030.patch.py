# Auto-generated code snippet by Emily Self-Modify
# Based on: SimpleTimeBench, 结果奖励强化学习用于预测中的证据搜索
# Generated: 2026-10-03T17:40:30.232363

def _evidence_search_rl(self, query: str, candidates: list, top_k: int = 3) -> list:
    import math, random
    from collections import defaultdict

    if not candidates:
        return []

    scores = defaultdict(float)
    counts = defaultdict(int)
    for cand in candidates:
        text = str(cand.get("title", "")) + " " + str(cand.get("summary", ""))
        q_tokens = set(query.lower().split())
        c_tokens = set(text.lower().split())
        overlap = len(q_tokens & c_tokens)
        base = overlap / (math.log(len(c_tokens) + 2) + 1.0)
        scores[id(cand)] = base
        counts[id(cand)] = 1

    for _ in range(5):
        ranked = sorted(candidates, key=lambda c: scores[id(c)], reverse=True)
        for i, cand in enumerate(ranked[:top_k]):
            reward = 1.0 / (i + 1)
            scores[id(cand)] = 0.7 * scores[id(cand)] + 0.3 * reward
        for cand in candidates:
            if random.random() < 0.2:
                scores[id(cand)] += random.gauss(0, 0.01)

    ranked = sorted(candidates, key=lambda c: scores[id(c)], reverse=True)
    return ranked[:top_k]


def _simple_time_bench(self, fn, *args, budget_ms: int = 500, **kwargs):
    import time
    start = time.perf_counter()
    result = None
    try:
        result = fn(*args, **kwargs)
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return {"ok": False, "error": str(e), "elapsed_ms": elapsed, "result": None}
    elapsed = (time.perf_counter() - start) * 1000
    return {
        "ok": elapsed <= budget_ms,
        "elapsed_ms": elapsed,
        "budget_ms": budget_ms,
        "result": result,
    }


def _enhance_with_evidence_rl(self, query: str, papers: list) -> list:
    top = self._evidence_search_rl(query, papers, top_k=3)
    verified = []
    for p in top:
        bench = self._simple_time_bench(lambda x=p: x.get("summary", ""), budget_ms=50)
        if bench["ok"]:
            p["_evidence_score"] = bench["elapsed_ms"]
            verified.append(p)
    return verified if verified else top
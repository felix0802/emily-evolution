# Auto-generated code snippet by Emily Self-Modify
# Based on: 条件计算/动态路由, 假设驱动架构发现
# Generated: 2026-11-27T23:47:57.010726

def _dynamic_route_and_discover(self, papers, context):
    import math
    from collections import defaultdict

    def _route_score(paper, ctx):
        text = (paper.get("title", "") + " " + paper.get("summary", "")).lower()
        novelty = sum(1 for w in ctx.get("novelty_terms", []) if w in text)
        relevance = sum(1 for w in ctx.get("focus_terms", []) if w in text)
        complexity = min(len(text.split()) / 200.0, 1.0)
        return 0.5 * novelty + 0.3 * relevance + 0.2 * complexity

    def _hypothesis_prior(paper):
        s = paper.get("summary", "")
        cues = ["we hypothesize", "we conjecture", "we propose", "we argue"]
        return 1.0 if any(c in s.lower() for c in cues) else 0.4

    routed = defaultdict(list)
    for p in papers:
        score = _route_score(p, context) * _hypothesis_prior(p)
        bucket = "high" if score >= 0.6 else ("mid" if score >= 0.3 else "low")
        routed[bucket].append((score, p))

    for b in routed:
        routed[b].sort(key=lambda x: -x[0])

    discoveries = []
    high = [p for _, p in routed.get("high", [])]
    mid = [p for _, p in routed.get("mid", [])]

    for i, p in enumerate(high[:5]):
        hyp = {
            "id": f"hyp_{i}",
            "claim": p.get("title", "")[:120],
            "support": p.get("summary", "")[:200],
            "confidence": round(0.7 + 0.05 * i, 2),
            "source": p.get("id", "unknown"),
        }
        discoveries.append(hyp)

    if high and mid:
        cross = {
            "id": "hyp_cross",
            "claim": f"Cross-link: {high[0].get('title','')[:60]} x {mid[0].get('title','')[:60]}",
            "support": "Synthesized from routed high/mid relevance clusters",
            "confidence": 0.55,
            "source": "dynamic_router",
        }
        discoveries.append(cross)

    self._routing_state = {
        "buckets": {k: len(v) for k, v in routed.items()},
        "discoveries": len(discoveries),
        "entropy": -sum((len(v)/max(len(papers),1)) * math.log(len(v)/max(len(papers),1) + 1e-9) for v in routed.values()),
    }
    return discoveries
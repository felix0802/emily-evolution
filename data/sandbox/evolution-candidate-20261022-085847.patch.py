# Auto-generated code snippet by Emily Self-Modify
# Based on: Petri网上的结构感知消息传递, 时间序列基础模型
# Generated: 2026-10-22T08:58:47.916144

def _structural_temporal_enhance(paper_meta: dict, history: list) -> dict:
    import math
    from collections import defaultdict

    # --- Petri-net style structural message passing over paper sections ---
    sections = paper_meta.get("sections", []) or [paper_meta.get("title", "")]
    n = max(len(sections), 1)
    adj = defaultdict(set)
    for i in range(n):
        for j in range(n):
            if i != j and abs(i - j) <= 2:
                adj[i].add(j)
    feats = [float(len(str(s))) for s in sections] or [1.0]
    max_f = max(feats) or 1.0
    feats = [f / max_f for f in feats]
    for _ in range(2):
        new_feats = []
        for i in range(n):
            agg = feats[i]
            if adj[i]:
                agg += sum(feats[j] for j in adj[i]) / len(adj[i])
            new_feats.append(agg / 2.0)
        feats = new_feats
    struct_score = sum(feats) / len(feats)

    # --- Time-series foundation model style temporal encoding ---
    series = [float(h.get("score", 0.0)) for h in history[-32:]]
    if len(series) >= 4:
        diffs = [series[i+1] - series[i] for i in range(len(series)-1)]
        trend = sum(diffs) / len(diffs)
        vol = math.sqrt(sum((d - trend) ** 2 for d in diffs) / len(diffs)) or 1e-6
        last = series[-1]
        z = (last - (sum(series) / len(series))) / vol
        temporal_score = 1.0 / (1.0 + math.exp(-z))
    else:
        temporal_score = 0.5

    combined = 0.6 * struct_score + 0.4 * temporal_score
    return {
        "struct_score": round(struct_score, 4),
        "temporal_score": round(temporal_score, 4),
        "combined_priority": round(combined, 4),
        "should_prioritize": combined > 0.55,
    }


def evolve():
    # ... existing evolution logic ...
    paper_meta = locals().get("paper_meta", {})
    history = locals().get("history", [])
    enhancement = _structural_temporal_enhance(paper_meta, history)
    if enhancement["should_prioritize"]:
        print(f"[enhance] prioritizing paper (score={enhancement['combined_priority']})")
    # ... continue with existing pipeline ...
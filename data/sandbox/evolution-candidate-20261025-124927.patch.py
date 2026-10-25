# Auto-generated code snippet by Emily Self-Modify
# Based on: Domain-Integrated Similarity Cost (DISC), Random Initialization Baseline for TSFMs
# Generated: 2026-10-25T12:49:27.843557

def _disc_tsfm_enhancement(papers, repo_state):
    import math
    import random
    from collections import defaultdict

    def _tokenize(text):
        return [t.lower() for t in text.replace("-", " ").split() if len(t) > 2]

    def _domain_similarity(a, b):
        ta, tb = set(_tokenize(a)), set(_tokenize(b))
        if not ta or not tb:
            return 0.0
        inter = len(ta & tb)
        union = len(ta | tb)
        jaccard = inter / union
        domain_bonus = 0.0
        for kw in ("time", "series", "forecast", "temporal", "tsfm", "foundation"):
            if kw in ta and kw in tb:
                domain_bonus += 0.05
        return min(1.0, jaccard + domain_bonus)

    def _disc_cost(candidate, anchors, weights=None):
        if not anchors:
            return 1.0
        weights = weights or [1.0 / len(anchors)] * len(anchors)
        sims = [_domain_similarity(candidate, a) for a in anchors]
        weighted_sim = sum(w * s for w, s in zip(weights, sims))
        return 1.0 - weighted_sim

    def _random_init_baseline(n, seed=42):
        rng = random.Random(seed)
        return [rng.uniform(0.0, 1.0) for _ in range(n)]

    anchors = [p.get("title", "") + " " + p.get("summary", "") for p in papers[:5]]
    scored = []
    for p in papers:
        text = p.get("title", "") + " " + p.get("summary", "")
        cost = _disc_cost(text, anchors)
        scored.append((cost, p))

    scored.sort(key=lambda x: x[0])
    selected = [p for _, p in scored[: max(3, len(scored) // 3)]]

    baseline = _random_init_baseline(len(selected))
    mean_baseline = sum(baseline) / len(baseline) if baseline else 0.0
    disc_mean = sum(c for c, _ in scored[: len(selected)]) / max(1, len(selected))
    improvement = mean_baseline - disc_mean

    repo_state.setdefault("disc_metrics", []).append({
        "disc_mean_cost": round(disc_mean, 4),
        "random_baseline_mean": round(mean_baseline, 4),
        "improvement": round(improvement, 4),
        "selected_count": len(selected),
    })
    repo_state["disc_selected_papers"] = [
        {"title": p.get("title", ""), "id": p.get("id", "")} for p in selected
    ]
    return selected, repo_state
# Auto-generated code snippet by Emily Self-Modify
# Based on: 领域集成相似性成本 (DISC), 不确定性感知的搜索复用 (QuaNAS)
# Generated: 2026-10-24T02:13:25.712402

def _disc_quanas_evolve_hook(self, candidates, history, budget=8):
    import math, random
    from collections import defaultdict

    def _disc_cost(a, b):
        sa, sb = set(a.get("tags", [])), set(b.get("tags", []))
        if not sa and not sb:
            return 1.0
        inter = len(sa & sb)
        union = len(sa | sb) or 1
        jacc = inter / union
        va = a.get("score", 0.0)
        vb = b.get("score", 0.0)
        return (1.0 - jacc) * (1.0 + abs(va - vb))

    def _uncertainty(c):
        n = c.get("trials", 1)
        s = c.get("score", 0.0)
        return math.sqrt(max(s * (1.0 - s), 1e-6) / max(n, 1))

    if not candidates:
        return []

    pool = list(candidates)
    random.shuffle(pool)
    selected = []
    remaining = list(pool)

    while remaining and len(selected) < budget:
        best, best_val = None, -1e9
        for c in remaining:
            u = _uncertainty(c)
            if selected:
                d = min(_disc_cost(c, s) for s in selected)
            else:
                d = 1.0
            reuse = 0.0
            for h in history[-20:]:
                if h.get("signature") == c.get("signature"):
                    reuse += h.get("gain", 0.0)
            val = 0.6 * u + 0.3 * d + 0.1 * reuse
            if val > best_val:
                best_val, best = val, c
        if best is None:
            break
        selected.append(best)
        remaining.remove(best)

    for c in selected:
        c["disc_quanas_weight"] = round(_uncertainty(c), 4)
    return selected

# 在 evolve() 内部调用：
# candidates = _disc_quanas_evolve_hook(self, candidates, history, budget=8)
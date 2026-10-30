# Auto-generated code snippet by Emily Self-Modify
# Based on: 基于锚点的比较框架, 重整化群（RG）理论
# Generated: 2026-10-30T07:49:58.784265

def _rg_anchor_compare(candidates, anchor_pool, scale_levels=3):
    import math
    def _dist(a, b):
        keys = set(a) | set(b)
        s = 0.0
        for k in keys:
            va, vb = a.get(k, 0.0), b.get(k, 0.0)
            try:
                s += (float(va) - float(vb)) ** 2
            except (TypeError, ValueError):
                s += 0.0 if va == vb else 1.0
        return math.sqrt(s)

    def _coarse(feats, level):
        if level <= 0:
            return dict(feats)
        out = {}
        for k, v in feats.items():
            try:
                out[k] = round(float(v), max(0, level))
            except (TypeError, ValueError):
                out[k] = v
        return out

    scored = []
    for cand in candidates:
        feats = cand.get("features", {}) if isinstance(cand, dict) else {}
        total = 0.0
        weight = 1.0
        for lvl in range(scale_levels):
            cf = _coarse(feats, lvl)
            best = min((_dist(cf, _coarse(a.get("features", {}), lvl)) for a in anchor_pool), default=1.0)
            total += weight * best
            weight *= 0.5
        scored.append((total, cand))

    scored.sort(key=lambda x: x[0])
    if not scored:
        return []
    best_score = scored[0][0]
    tol = best_score * 0.05 + 1e-9
    return [c for s, c in scored if s <= best_score + tol]
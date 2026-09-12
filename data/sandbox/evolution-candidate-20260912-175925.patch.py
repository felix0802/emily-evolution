# Auto-generated code snippet by Emily Self-Modify
# Based on: 无编码器/无VAE架构, Mixture Of Experts, Mixture Of
# Generated: 2026-09-12T17:59:25.660874

def _moe_route_and_merge(experts, inputs, top_k=2):
    import numpy as np
    scores = np.array([e.get("score", 0.0) for e in experts], dtype=float)
    if scores.size == 0:
        return inputs
    if scores.sum() <= 0:
        scores = np.ones_like(scores)
    probs = scores / scores.sum()
    k = min(top_k, len(experts))
    top_idx = np.argsort(probs)[-k:]
    gate = np.zeros_like(probs)
    gate[top_idx] = probs[top_idx] / probs[top_idx].sum()
    merged = []
    for i, e in enumerate(experts):
        if gate[i] <= 0:
            continue
        try:
            out = e["fn"](inputs)
        except Exception:
            continue
        merged.append((gate[i], out))
    if not merged:
        return inputs
    if isinstance(merged[0][1], str):
        return "".join(w * o for w, o in merged)
    try:
        arr = np.zeros_like(np.asarray(merged[0][1], dtype=float))
        for w, o in merged:
            arr = arr + w * np.asarray(o, dtype=float)
        return arr
    except Exception:
        return merged[0][1]


def _evolve_with_moe(self, papers, experts=None):
    experts = experts or getattr(self, "experts", [])
    routed = _moe_route_and_merge(experts, papers, top_k=2)
    return self.evolve(routed)
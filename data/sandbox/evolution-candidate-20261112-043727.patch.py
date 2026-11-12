# Auto-generated code snippet by Emily Self-Modify
# Based on: 隐私感知深度学习, 锚点比较基准框架
# Generated: 2026-11-12T04:37:27.949180

def _privacy_aware_anchor_compare(candidates, anchors, epsilon=1.0, min_anchor_gain=0.02):
    import numpy as np
    from sklearn.metrics import pairwise_distances

    def _laplace_noise(shape, scale):
        return np.random.laplace(0.0, scale, size=shape)

    def _clip_and_noise(vec, clip_norm=1.0, scale=1.0):
        norm = np.linalg.norm(vec)
        if norm > clip_norm:
            vec = vec * (clip_norm / (norm + 1e-12))
        return vec + _laplace_noise(vec.shape, scale)

    if not candidates or not anchors:
        return []

    cand_vecs = np.array([c.get("embedding", np.zeros(8)) for c in candidates], dtype=float)
    anchor_vecs = np.array([a.get("embedding", np.zeros(8)) for a in anchors], dtype=float)

    if cand_vecs.ndim == 1:
        cand_vecs = cand_vecs.reshape(1, -1)
    if anchor_vecs.ndim == 1:
        anchor_vecs = anchor_vecs.reshape(1, -1)

    noise_scale = 1.0 / max(epsilon, 1e-6)
    cand_vecs = np.array([_clip_and_noise(v, 1.0, noise_scale) for v in cand_vecs])
    anchor_vecs = np.array([_clip_and_noise(v, 1.0, noise_scale) for v in anchor_vecs])

    dists = pairwise_distances(cand_vecs, anchor_vecs, metric="cosine")
    best_anchor_dist = dists.min(axis=1)
    baseline = float(np.median(best_anchor_dist)) if len(best_anchor_dist) else 0.0

    scored = []
    for cand, d in zip(candidates, best_anchor_dist):
        gain = baseline - float(d)
        if gain >= min_anchor_gain:
            cand = dict(cand)
            cand["anchor_gain"] = round(gain, 6)
            cand["privacy_epsilon"] = epsilon
            scored.append(cand)

    scored.sort(key=lambda x: x.get("anchor_gain", 0.0), reverse=True)
    return scored

# 在 evolve() 中插入调用：
# candidates = _privacy_aware_anchor_compare(candidates, anchors, epsilon=1.0)
# Auto-generated code snippet by Emily Self-Modify
# Based on: Geometric feature-based facial expression recognition, Anchor-based comparative benchmarking, Geometric
# Generated: 2026-11-14T16:12:09.279431

def geometric_expression_benchmark(perception_data, anchor_samples=None):
    import numpy as np
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics.pairwise import cosine_similarity

    def extract_geometric_features(landmarks):
        pts = np.asarray(landmarks, dtype=float)
        if pts.ndim != 2 or pts.shape[0] < 3:
            return np.zeros(8)
        centroid = pts.mean(axis=0)
        centered = pts - centroid
        dists = np.linalg.norm(centered, axis=1)
        angles = np.arctan2(centered[:, 1], centered[:, 0])
        cov = np.cov(centered.T) if pts.shape[0] > 1 else np.eye(2)
        eigvals = np.linalg.eigvalsh(cov)
        return np.array([
            dists.mean(), dists.std(),
            angles.mean(), angles.std(),
            eigvals[0], eigvals[1],
            float(eigvals[0] / (eigvals[1] + 1e-8)),
            float(np.sum(dists > dists.mean()))
        ])

    feats = []
    for item in perception_data:
        lm = item.get("landmarks") if isinstance(item, dict) else None
        feats.append(extract_geometric_features(lm if lm is not None else []))
    feats = np.vstack(feats) if feats else np.zeros((1, 8))

    scaler = StandardScaler()
    feats_n = scaler.fit_transform(feats)

    if anchor_samples is None or len(anchor_samples) == 0:
        anchor_samples = feats_n
    anchors = np.asarray(anchor_samples, dtype=float)
    if anchors.shape[1] != feats_n.shape[1]:
        anchors = scaler.transform(anchors) if anchors.shape[1] == feats.shape[1] else feats_n

    sim = cosine_similarity(feats_n, anchors)
    best_anchor = np.argmax(sim, axis=1)
    confidence = np.max(sim, axis=1)

    return {
        "features": feats_n.tolist(),
        "anchor_assignment": best_anchor.tolist(),
        "confidence": confidence.tolist(),
        "mean_confidence": float(confidence.mean()),
        "geometric_variance": float(feats_n.var(axis=0).mean())
    }

# 插入到 evolve() 中：
# benchmark = geometric_expression_benchmark(perception_data, anchor_samples)
# if benchmark["mean_confidence"] < 0.6:
#     evolution_log.append({"stage": "geometric_benchmark", "result": benchmark})
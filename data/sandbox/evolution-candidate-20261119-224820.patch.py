# Auto-generated code snippet by Emily Self-Modify
# Based on: 混合图神经网络代理模型, 分布外泛化
# Generated: 2026-11-19T22:48:20.958239

def _enhance_with_gnn_ood(self, candidates, context):
    import numpy as np
    from sklearn.neighbors import LocalOutlierFactor
    from sklearn.preprocessing import StandardScaler

    if not candidates:
        return candidates

    feats = []
    for c in candidates:
        vec = c.get("embedding") or c.get("features") or []
        if not vec:
            vec = [len(str(c.get("code", ""))), len(c.get("deps", []) or []),
                   float(c.get("score", 0.0)), float(c.get("novelty", 0.0))]
        feats.append(vec)

    max_dim = max(len(v) for v in feats)
    feats = [v + [0.0] * (max_dim - len(v)) for v in feats]
    X = np.asarray(feats, dtype=float)

    if X.shape[0] < 3:
        return candidates

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    try:
        lof = LocalOutlierFactor(n_neighbors=min(5, X.shape[0] - 1), novelty=False)
        ood_scores = -lof.fit_predict(Xs)
        raw = -lof.negative_outlier_factor_
    except Exception:
        ood_scores = np.zeros(X.shape[0])
        raw = np.zeros(X.shape[0])

    adj = np.zeros((X.shape[0], X.shape[0]))
    for i in range(X.shape[0]):
        d = np.linalg.norm(Xs - Xs[i], axis=1)
        k = min(3, X.shape[0] - 1)
        idx = np.argsort(d)[1:k + 1]
        adj[i, idx] = 1.0 / (d[idx] + 1e-6)
    adj = adj / (adj.sum(axis=1, keepdims=True) + 1e-9)

    H = Xs.copy()
    for _ in range(2):
        H = 0.5 * H + 0.5 * (adj @ H)

    gnn_scores = H.mean(axis=1)
    gnn_scores = (gnn_scores - gnn_scores.min()) / (gnn_scores.ptp() + 1e-9)

    for i, c in enumerate(candidates):
        ood_penalty = float(raw[i]) if raw[i] > 0 else 0.0
        c["gnn_ood_score"] = float(gnn_scores[i])
        c["ood_penalty"] = ood_penalty
        base = float(c.get("score", 0.0))
        c["score"] = base * (0.7 + 0.3 * gnn_scores[i]) - 0.1 * ood_penalty

    candidates.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    self._last_gnn_ood = {"n": len(candidates), "mean_ood": float(np.mean(raw))}
    return candidates
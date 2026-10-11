# Auto-generated code snippet by Emily Self-Modify
# Based on: 样条与项目反应理论, 白色盒欺骗检测探针
# Generated: 2026-10-11T21:09:04.255597

def _apply_spline_irt_whiteprobe(self, papers, responses):
    import numpy as np
    from scipy.interpolate import UnivariateSpline
    from sklearn.decomposition import PCA

    if not papers or not responses:
        return {"spline_scores": [], "irt_abilities": [], "probe_flags": []}

    feats = []
    for p in papers:
        vec = p.get("embedding") or p.get("features") or [len(p.get("title", "")), len(p.get("abstract", ""))]
        feats.append(np.asarray(vec, dtype=float))
    X = np.vstack(feats)
    if X.shape[1] > 1:
        X = PCA(n_components=min(3, X.shape[1])).fit_transform(X)
    else:
        X = X.reshape(-1, 1)

    spline_scores = []
    for i in range(X.shape[1]):
        col = X[:, i]
        if len(col) >= 4:
            k = min(3, len(col) - 1)
            try:
                spl = UnivariateSpline(np.arange(len(col)), col, k=k, s=len(col) * 0.1)
                spline_scores.append(float(np.mean(np.abs(spl(np.arange(len(col))) - col))))
            except Exception:
                spline_scores.append(float(np.std(col)))
        else:
            spline_scores.append(float(np.std(col)))

    theta = np.zeros(len(responses))
    b = np.zeros(len(responses))
    for _ in range(20):
        p = 1.0 / (1.0 + np.exp(-(theta - b)))
        grad = responses - p
        theta += 0.1 * grad
        b -= 0.05 * grad
    irt_abilities = theta.tolist()

    probe_flags = []
    for r in responses:
        p = 1.0 / (1.0 + np.exp(-(np.mean(theta) - np.mean(b))))
        probe_flags.append(bool(abs(r - p) > 0.35))

    self._spline_irt_state = {
        "spline_scores": spline_scores,
        "irt_abilities": irt_abilities,
        "probe_flags": probe_flags,
    }
    return self._spline_irt_state
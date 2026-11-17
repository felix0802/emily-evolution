# Auto-generated code snippet by Emily Self-Modify
# Based on: 等变消息传递神经网络, 机器学习原子间势（MLIP）
# Generated: 2026-11-17T05:28:04.858464

def _enhance_with_equivariant_mlip(self, papers, repo_context):
    import numpy as np
    try:
        from sklearn.neural_network import MLPRegressor
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        return papers

    def _equivariant_features(coords, species, cutoff=5.0):
        coords = np.asarray(coords, dtype=float)
        species = np.asarray(species)
        n = len(coords)
        feats = []
        for i in range(n):
            d = coords - coords[i]
            r = np.linalg.norm(d, axis=1)
            mask = (r > 1e-8) & (r < cutoff)
            if not np.any(mask):
                feats.append(np.zeros(6))
                continue
            r_m = r[mask]
            d_m = d[mask] / r_m[:, None]
            radial = np.exp(-r_m) * (1.0 - r_m / cutoff)
            angular = np.einsum('ij,ij->i', d_m, d_m)
            feats.append(np.array([
                radial.sum(), (radial * r_m).sum(), radial.mean(),
                angular.mean(), np.cos(r_m).mean(), len(r_m) / n
            ]))
        return np.array(feats)

    def _mlip_score(feats):
        if feats.size == 0:
            return 0.0
        scaler = StandardScaler().fit(feats)
        X = scaler.transform(feats)
        model = MLPRegressor(hidden_layer_sizes=(32, 16), max_iter=200,
                             random_state=0)
        target = np.linalg.norm(X, axis=1)
        model.fit(X, target)
        return float(np.mean(np.abs(model.predict(X) - target)))

    enriched = []
    for p in papers:
        try:
            text = (p.get('title', '') + ' ' + p.get('summary', '')).lower()
            if any(k in text for k in ('equivariant', 'mlip', 'interatomic',
                                       'message passing', 'potential energy')):
                rng = np.random.default_rng(abs(hash(text)) % (2**32))
                coords = rng.normal(size=(6, 3)) * 2.0
                species = rng.integers(1, 8, size=6)
                feats = _equivariant_features(coords, species)
                score = _mlip_score(feats)
                p['mlip_relevance'] = round(score, 4)
                p['equivariant_flag'] = True
        except Exception:
            p['mlip_relevance'] = 0.0
        enriched.append(p)
    enriched.sort(key=lambda x: x.get('mlip_relevance', 0.0), reverse=True)
    return enriched

papers = _enhance_with_equivariant_mlip(self, papers, repo_context)
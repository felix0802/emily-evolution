# Auto-generated code snippet by Emily Self-Modify
# Based on: 分阶段蒸馏至双向循环扩散语言模型, 固定状态循环的匹配状态分解
# Generated: 2026-10-13T22:01:49.615394

def _distill_bidirectional_recurrent_diffusion(papers, state_dim=64, steps=8):
    import numpy as np
    from sklearn.decomposition import TruncatedSVD
    from sklearn.preprocessing import normalize

    if not papers:
        return {"distilled": [], "state": np.zeros(state_dim)}

    texts = []
    for p in papers:
        t = (p.get("title", "") + " " + p.get("summary", "")).strip()
        if t:
            texts.append(t)
    if not texts:
        return {"distilled": [], "state": np.zeros(state_dim)}

    vocab = {}
    for t in texts:
        for w in t.lower().split():
            vocab.setdefault(w, len(vocab))
    if not vocab:
        return {"distilled": [], "state": np.zeros(state_dim)}

    X = np.zeros((len(texts), len(vocab)), dtype=np.float32)
    for i, t in enumerate(texts):
        for w in t.lower().split():
            X[i, vocab[w]] += 1.0
    X = normalize(X)

    k = min(state_dim, max(2, min(X.shape) - 1))
    svd = TruncatedSVD(n_components=k, random_state=42)
    Z = svd.fit_transform(X)

    def _match_state_decomp(h, fixed_state):
        proj = h @ fixed_state.T
        recon = proj @ fixed_state
        residual = h - recon
        return recon, residual

    fixed_state = np.random.RandomState(0).randn(k, k).astype(np.float32)
    fixed_state, _ = np.linalg.qr(fixed_state)

    h = Z.mean(axis=0)
    for _ in range(steps):
        recon, residual = _match_state_decomp(h.reshape(1, -1), fixed_state)
        h = 0.5 * h + 0.5 * (recon.flatten() + 0.1 * residual.flatten())
        h = h / (np.linalg.norm(h) + 1e-8)

    scores = Z @ h
    order = np.argsort(-scores)
    distilled = [papers[i] for i in order[: max(1, len(papers) // 2)]]

    return {"distilled": distilled, "state": h, "svd": svd, "vocab": vocab}
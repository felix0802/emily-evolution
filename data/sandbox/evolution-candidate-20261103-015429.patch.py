# Auto-generated code snippet by Emily Self-Modify
# Based on: 连续空间潜在推理, 检索增强多智能体路由
# Generated: 2026-11-03T01:54:29.796053

def _latent_retrieval_router(query: str, candidates: list, top_k: int = 3) -> list:
    import numpy as np
    from sklearn.feature_extraction.text import HashingVectorizer
    from sklearn.preprocessing import normalize

    if not candidates:
        return []

    vec = HashingVectorizer(n_features=2 ** 12, alternate_sign=False, norm=None)
    try:
        X = vec.transform([query] + [str(c) for c in candidates])
    except Exception:
        return candidates[:top_k]

    X = normalize(X)
    q = X[0]
    docs = X[1:]
    sims = (docs @ q.T).toarray().ravel()

    # continuous latent reasoning: softmax-weighted centroid refinement
    sims = np.nan_to_num(sims, nan=0.0, posinf=0.0, neginf=0.0)
    if sims.size == 0:
        return candidates[:top_k]
    shifted = sims - sims.max()
    weights = np.exp(shifted)
    weights = weights / (weights.sum() + 1e-12)
    centroid = np.asarray(docs.T @ weights).ravel()
    refined = np.asarray(docs @ centroid).ravel()
    score = 0.6 * sims + 0.4 * refined

    order = np.argsort(-score)[:top_k]
    return [candidates[i] for i in order]


def _multi_agent_route(task: str, agents: list, retrieved: list) -> dict:
    import numpy as np
    from sklearn.feature_extraction.text import HashingVectorizer
    from sklearn.preprocessing import normalize

    if not agents:
        return {"agent": None, "context": retrieved, "confidence": 0.0}

    vec = HashingVectorizer(n_features=2 ** 10, alternate_sign=False, norm=None)
    corpus = [task] + [str(a.get("name", a)) + " " + str(a.get("skills", "")) for a in agents]
    try:
        X = normalize(vec.transform(corpus))
    except Exception:
        return {"agent": agents[0], "context": retrieved, "confidence": 0.0}

    q = X[0]
    sims = (X[1:] @ q.T).toarray().ravel()
    sims = np.nan_to_num(sims, nan=0.0)
    if sims.size == 0:
        return {"agent": agents[0], "context": retrieved, "confidence": 0.0}

    idx = int(np.argmax(sims))
    conf = float(sims[idx])
    return {"agent": agents[idx], "context": retrieved, "confidence": conf}


def _enhance_with_latent_retrieval_router(task: str, candidates: list, agents: list) -> dict:
    retrieved = _latent_retrieval_router(task, candidates, top_k=3)
    route = _multi_agent_route(task, agents, retrieved)
    return {"retrieved": retrieved, "route": route}
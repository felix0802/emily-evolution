# Auto-generated code snippet by Emily Self-Modify
# Based on: 条件流模型, 基于相似性搜索的模型选择
# Generated: 2026-10-15T08:39:01.152227

def _conditional_flow_select(candidates, context, temperature=0.7):
    import numpy as np
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics.pairwise import cosine_similarity

    if not candidates:
        return None

    def _embed(obj):
        if isinstance(obj, dict):
            vals = []
            for k in sorted(obj.keys()):
                v = obj[k]
                if isinstance(v, (int, float)):
                    vals.append(float(v))
                elif isinstance(v, str):
                    vals.append(float(len(v) % 97) / 97.0)
                elif isinstance(v, (list, tuple)):
                    vals.append(float(len(v)) / 100.0)
            return np.array(vals if vals else [0.0], dtype=float)
        if isinstance(obj, str):
            return np.array([float(len(obj) % 97) / 97.0, float(sum(map(ord, obj)) % 89) / 89.0])
        return np.array([0.0])

    ctx_vec = _embed(context).reshape(1, -1)
    cand_vecs = np.array([_embed(c) for c in candidates])

    if cand_vecs.ndim == 1:
        cand_vecs = cand_vecs.reshape(1, -1)

    dim = min(ctx_vec.shape[1], cand_vecs.shape[1])
    ctx_vec = ctx_vec[:, :dim]
    cand_vecs = cand_vecs[:, :dim]

    scaler = StandardScaler()
    try:
        combined = scaler.fit_transform(np.vstack([ctx_vec, cand_vecs]))
    except Exception:
        combined = np.vstack([ctx_vec, cand_vecs])

    ctx_s = combined[0:1]
    cand_s = combined[1:]

    sims = cosine_similarity(ctx_s, cand_s)[0]
    logits = sims / max(temperature, 1e-6)
    logits = logits - np.max(logits)
    probs = np.exp(logits)
    probs = probs / (np.sum(probs) + 1e-12)

    idx = int(np.argmax(probs))
    return candidates[idx], float(probs[idx])
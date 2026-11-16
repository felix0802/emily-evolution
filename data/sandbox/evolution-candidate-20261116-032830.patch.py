# Auto-generated code snippet by Emily Self-Modify
# Based on: JEPA (Joint Embedding Predictive Architecture), Ambiguity-aware VQA
# Generated: 2026-11-16T03:28:30.906101

def _jepa_ambiguity_enhance(perception, understanding, decision):
    import numpy as np
    from sklearn.decomposition import PCA

    def _jepa_embed(obs, ctx, dim=32):
        x = np.concatenate([np.asarray(obs, dtype=float).ravel(),
                            np.asarray(ctx, dtype=float).ravel()])
        if x.size == 0:
            return np.zeros(dim)
        if x.size < dim:
            x = np.pad(x, (0, dim - x.size))
        pca = PCA(n_components=min(dim, x.size), random_state=0)
        z = pca.fit_transform(x.reshape(1, -1))[0]
        if z.size < dim:
            z = np.pad(z, (0, dim - z.size))
        return z[:dim]

    def _predictive_score(z_obs, z_ctx):
        if np.linalg.norm(z_obs) == 0 or np.linalg.norm(z_ctx) == 0:
            return 0.0
        cos = float(np.dot(z_obs, z_ctx) /
                    (np.linalg.norm(z_obs) * np.linalg.norm(z_ctx) + 1e-8))
        return max(0.0, min(1.0, (cos + 1.0) / 2.0))

    def _ambiguity_vqa(question, candidates, scores):
        if not candidates:
            return None, 1.0
        s = np.asarray(scores, dtype=float)
        if s.size == 0 or s.sum() == 0:
            return candidates[0], 1.0
        p = s / s.sum()
        entropy = float(-np.sum(p * np.log(p + 1e-8)))
        max_ent = float(np.log(len(p))) if len(p) > 1 else 1.0
        ambiguity = entropy / (max_ent + 1e-8)
        best = candidates[int(np.argmax(p))]
        return best, ambiguity

    obs = perception.get("observation", [])
    ctx = perception.get("context", [])
    z_obs = _jepa_embed(obs, [])
    z_ctx = _jepa_embed([], ctx)
    pred_score = _predictive_score(z_obs, z_ctx)

    q = understanding.get("question", "")
    cands = understanding.get("candidates", [])
    scs = understanding.get("scores", [])
    best, amb = _ambiguity_vqa(q, cands, scs)

    if amb > 0.6:
        decision["action"] = "clarify"
        decision["reason"] = f"high_ambiguity={amb:.2f}"
    elif pred_score < 0.3:
        decision["action"] = "explore"
        decision["reason"] = f"low_jepa_pred={pred_score:.2f}"
    else:
        decision["action"] = decision.get("action", "proceed")
        decision["reason"] = f"jepa={pred_score:.2f},amb={amb:.2f}"

    decision["jepa_score"] = pred_score
    decision["ambiguity"] = amb
    decision["vqa_answer"] = best
    return decision

# 在 evolve() 中插入：
# decision = _jepa_ambiguity_enhance(perception, understanding, decision)
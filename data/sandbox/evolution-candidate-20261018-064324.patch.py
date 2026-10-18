# Auto-generated code snippet by Emily Self-Modify
# Based on: Kronecker 积注意力（结构化 KV 压缩）, 权重空间 KV cache 补偿（PatchKV）, Kv Cache
# Generated: 2026-10-18T06:43:24.712296

def _apply_kronecker_patchkv_attention(self, kv_cache, query, patch_budget=64):
    import numpy as np
    if kv_cache is None or len(kv_cache) == 0:
        return query, kv_cache
    try:
        keys = np.asarray([c.get("k") for c in kv_cache if c.get("k") is not None], dtype=np.float32)
        vals = np.asarray([c.get("v") for c in kv_cache if c.get("v") is not None], dtype=np.float32)
        if keys.size == 0 or vals.size == 0 or keys.shape[0] != vals.shape[0]:
            return query, kv_cache
        q = np.asarray(query, dtype=np.float32).reshape(-1)
        n, d = keys.shape
        if q.shape[0] != d:
            d = min(q.shape[0], d)
            q = q[:d]; keys = keys[:, :d]; vals = vals[:, :d]
        r = int(np.sqrt(max(1, min(patch_budget, n))))
        c = int(np.ceil(n / r))
        pad = r * c - n
        if pad > 0:
            keys = np.vstack([keys, np.zeros((pad, d), dtype=np.float32)])
            vals = np.vstack([vals, np.zeros((pad, vals.shape[1]), dtype=np.float32)])
        k_blocks = keys.reshape(r, c, d)
        v_blocks = vals.reshape(r, c, vals.shape[1])
        k_comp = k_blocks.mean(axis=1)
        v_comp = v_blocks.mean(axis=1)
        scores = (k_comp @ q) / (np.linalg.norm(k_comp, axis=1) * (np.linalg.norm(q) + 1e-8) + 1e-8)
        w = np.exp(scores - scores.max())
        w = w / (w.sum() + 1e-8)
        ctx = (w[:, None] * v_comp).sum(axis=0)
        residual = q[:ctx.shape[0]] if q.shape[0] >= ctx.shape[0] else np.pad(q, (0, ctx.shape[0] - q.shape[0]))
        fused = 0.7 * ctx + 0.3 * residual
        new_cache = [{"k": k_comp[i].tolist(), "v": v_comp[i].tolist(), "compressed": True} for i in range(k_comp.shape[0])]
        return fused.tolist(), new_cache
    except Exception:
        return query, kv_cache

self._apply_kronecker_patchkv_attention = _apply_kronecker_patchkv_attention.__get__(self)
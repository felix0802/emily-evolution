# Auto-generated code snippet by Emily Self-Modify
# Based on: 可学习门控 KV cache 淘汰, 前缀记忆先验用于设备端推测解码
# Generated: 2026-11-08T08:12:01.846288

def _apply_kv_eviction_and_prefix_prior(self, kv_cache, prefix_tokens, budget=0.5):
    import math
    if not kv_cache or not isinstance(kv_cache, list):
        return kv_cache
    n = len(kv_cache)
    if n == 0:
        return kv_cache
    keep = max(1, int(n * (1.0 - budget)))
    gate_scores = []
    for i, entry in enumerate(kv_cache):
        try:
            norm = float(entry.get("norm", 1.0)) if isinstance(entry, dict) else 1.0
            age = (n - i) / float(n)
            pos_bias = 1.0 + 0.5 * math.exp(-age)
            score = norm * pos_bias
        except Exception:
            score = 1.0
        gate_scores.append((score, i))
    gate_scores.sort(reverse=True)
    kept_idx = set(i for _, i in gate_scores[:keep])
    new_cache = [kv_cache[i] for i in sorted(kept_idx)]
    prior = []
    for tok in (prefix_tokens or [])[-64:]:
        prior.append({"token": tok, "weight": 1.0, "source": "prefix_prior"})
    self._prefix_memory_prior = prior
    self._kv_eviction_stats = {
        "original": n,
        "kept": len(new_cache),
        "budget": budget,
        "prior_len": len(prior),
    }
    return new_cache

self._kv_cache = _apply_kv_eviction_and_prefix_prior(
    self,
    getattr(self, "_kv_cache", []),
    getattr(self, "_prefix_tokens", []),
    budget=0.5,
)
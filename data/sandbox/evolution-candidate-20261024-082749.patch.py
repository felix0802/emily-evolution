# Auto-generated code snippet by Emily Self-Modify
# Based on: KV 缓存压缩, 推测解码
# Generated: 2026-10-24T08:27:49.779783

def compress_kv_cache(kv_cache, max_size=512, alpha=0.5):
    """KV cache compression via attention-score weighted token eviction + merging."""
    if not kv_cache or len(kv_cache) <= max_size:
        return kv_cache
    scored = []
    for i, entry in enumerate(kv_cache):
        keys = entry.get("keys", [])
        values = entry.get("values", [])
        attn = entry.get("attention", [1.0] * len(keys))
        if not keys:
            continue
        score = sum(attn) / max(len(attn), 1)
        scored.append((score, i, keys, values, attn))
    scored.sort(key=lambda x: x[0], reverse=True)
    keep_n = int(max_size * alpha)
    kept = scored[:keep_n]
    rest = scored[keep_n:]
    merged = []
    if rest:
        merged_keys = []
        merged_values = []
        for _, _, k, v, _ in rest:
            merged_keys.extend(k)
            merged_values.extend(v)
        merged.append({"keys": merged_keys[:max_size - keep_n],
                       "values": merged_values[:max_size - keep_n],
                       "attention": [0.5] * min(len(merged_keys), max_size - keep_n)})
    result = [{"keys": k, "values": v, "attention": a} for _, _, k, v, a in kept]
    result.extend(merged)
    return result


def speculative_decode(prompt, draft_model, target_model, max_tokens=64, k=4):
    """Speculative decoding: draft k tokens, verify with target model."""
    generated = []
    while len(generated) < max_tokens:
        draft_tokens = draft_model(prompt + generated, k=k)
        if not draft_tokens:
            break
        accepted = 0
        for tok in draft_tokens:
            target_prob = target_model.prob(prompt + generated + [tok])
            draft_prob = draft_model.prob(prompt + generated + [tok])
            if target_prob >= draft_prob * 0.9:
                generated.append(tok)
                accepted += 1
            else:
                break
        if accepted == 0:
            fallback = target_model.sample(prompt + generated, 1)
            generated.extend(fallback)
    return generated[:max_tokens]


def evolve_with_compression_and_speculation(self, prompt, draft_model=None, target_model=None):
    """Enhanced evolve() using KV cache compression and speculative decoding."""
    compressed_cache = compress_kv_cache(getattr(self, "kv_cache", []), max_size=512)
    self.kv_cache = compressed_cache
    if draft_model is not None and target_model is not None:
        tokens = speculative_decode(prompt, draft_model, target_model, max_tokens=64, k=4)
    else:
        tokens = self.llm_generate(prompt, kv_cache=compressed_cache)
    return self.verify_and_act(tokens)
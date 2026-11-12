# Auto-generated code snippet by Emily Self-Modify
# Based on: 多任务多领域预训练, 采样频率不变性量化
# Generated: 2026-11-12T21:57:16.509779

def _multi_task_domain_pretrain_and_quantize(
    papers,
    domains=("nlp", "cv", "rl", "graph", "multimodal"),
    target_hz=1.0,
    max_tasks=8,
):
    import numpy as np
    from collections import defaultdict

    if not papers:
        return {"tasks": [], "quantized": [], "domain_weights": {}}

    def _hash_vec(text, dim=64):
        h = np.zeros(dim, dtype=np.float32)
        for i, ch in enumerate(str(text)):
            h[(ord(ch) + i * 31) % dim] += 1.0
        n = np.linalg.norm(h)
        return h / n if n > 0 else h

    domain_buckets = defaultdict(list)
    for p in papers:
        text = (p.get("title", "") + " " + p.get("summary", "")).lower()
        best, best_score = domains[0], -1
        for d in domains:
            score = text.count(d) + text.count(d[:2])
            if score > best_score:
                best, best_score = d, score
        domain_buckets[best].append(p)

    tasks = []
    for d, items in domain_buckets.items():
        if not items:
            continue
        vecs = np.stack([_hash_vec(it.get("title", "") + it.get("summary", "")) for it in items])
        centroid = vecs.mean(axis=0)
        tasks.append({
            "domain": d,
            "size": len(items),
            "centroid": centroid.tolist(),
            "sample_ids": [it.get("id", "") for it in items[:max_tasks]],
        })
        if len(tasks) >= max_tasks:
            break

    def _sample_freq_invariant_quantize(vec, hz):
        if hz <= 0:
            return vec
        scale = 1.0 / max(hz, 1e-6)
        v = np.asarray(vec, dtype=np.float32) * scale
        step = max(np.abs(v).max() / 127.0, 1e-8)
        q = np.clip(np.round(v / step), -127, 127).astype(np.int8)
        return {"q": q.tolist(), "step": float(step), "hz": float(hz)}

    quantized = []
    for t in tasks:
        q = _sample_freq_invariant_quantize(t["centroid"], target_hz)
        quantized.append({"domain": t["domain"], "quant": q})

    total = sum(t["size"] for t in tasks) or 1
    domain_weights = {t["domain"]: t["size"] / total for t in tasks}

    return {
        "tasks": tasks,
        "quantized": quantized,
        "domain_weights": domain_weights,
        "num_domains": len(tasks),
    }
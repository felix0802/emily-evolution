# Auto-generated code snippet by Emily Self-Modify
# Based on: 接口漂移鲁棒函数调用, 查询条件化记忆编译
# Generated: 2026-10-19T02:07:33.306356

def _query_conditioned_memory_compile(memory_store, query, top_k=5, drift_tol=0.35):
    import math, hashlib

    def _embed(text):
        h = hashlib.sha256(text.encode("utf-8", "ignore")).digest()
        vec = [(b / 255.0) - 0.5 for b in h[:32]]
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def _cos(a, b):
        return sum(x * y for x, y in zip(a, b))

    q_vec = _embed(query)
    scored = []
    for item in memory_store:
        text = item.get("text", "") if isinstance(item, dict) else str(item)
        if not text:
            continue
        sim = _cos(q_vec, _embed(text))
        drift = abs(sim - item.get("last_sim", sim)) if isinstance(item, dict) else 0.0
        if drift > drift_tol:
            sim *= (1.0 - min(drift, 1.0) * 0.5)
        scored.append((sim, text, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    compiled = []
    seen = set()
    for sim, text, item in scored[: top_k * 2]:
        key = text[:64]
        if key in seen:
            continue
        seen.add(key)
        compiled.append({"text": text, "score": round(sim, 4), "source": item})
        if len(compiled) >= top_k:
            break
    if isinstance(memory_store, list):
        for c in compiled:
            if isinstance(c["source"], dict):
                c["source"]["last_sim"] = c["score"]
    return compiled

def _robust_tool_call(tool_fn, args, fallbacks=None, retries=2):
    import inspect
    fallbacks = fallbacks or []
    try:
        sig = inspect.signature(tool_fn)
        accepted = set(sig.parameters.keys())
        filtered = {k: v for k, v in args.items() if k in accepted}
        return tool_fn(**filtered)
    except (TypeError, ValueError):
        for fb in fallbacks:
            try:
                return fb(args)
            except Exception:
                continue
        for _ in range(retries):
            try:
                return tool_fn(**args)
            except Exception:
                continue
    return None

def evolve(memory_store, query, tool_fn=None, tool_args=None):
    compiled_memory = _query_conditioned_memory_compile(memory_store, query)
    result = {"compiled_memory": compiled_memory}
    if tool_fn is not None:
        result["tool_result"] = _robust_tool_call(tool_fn, tool_args or {})
    return result
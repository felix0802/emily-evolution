# Auto-generated code snippet by Emily Self-Modify
# Based on: 自精炼 KV 缓存 (KV²), 反应式可逆 KV 驻留 (WakeKV)
# Generated: 2026-10-05T16:31:01.573030

def _kv2_wakekv_evolve_hook(self, papers, context):
    import hashlib, time
    from collections import OrderedDict

    if not hasattr(self, "_kv2_cache"):
        self._kv2_cache = OrderedDict()
        self._kv2_budget = 64
        self._wakekv_pins = set()

    def _sig(p):
        raw = (p.get("id", "") + p.get("title", "") + p.get("summary", "")[:512]).encode("utf-8", "ignore")
        return hashlib.blake2b(raw, digest_size=16).hexdigest()

    def _refine(entry, paper):
        prev = entry.get("refined", "")
        new = paper.get("summary", "")[:1024]
        merged = (prev + " || " + new)[-2048:]
        entry["refined"] = merged
        entry["hits"] = entry.get("hits", 0) + 1
        entry["ts"] = time.time()
        return entry

    def _wake(sig):
        if sig in self._kv2_cache:
            self._wakekv_pins.add(sig)
            self._kv2_cache.move_to_end(sig)
            return self._kv2_cache[sig]
        return None

    def _evict():
        for k in list(self._kv2_cache.keys()):
            if k not in self._wakekv_pins:
                self._kv2_cache.pop(k, None)
                return
        if self._kv2_cache:
            self._kv2_cache.popitem(last=False)

    refined_batch = []
    for p in papers:
        sig = _sig(p)
        hit = _wake(sig)
        if hit is not None:
            entry = _refine(hit, p)
        else:
            entry = {"refined": p.get("summary", "")[:1024], "hits": 1, "ts": time.time()}
            self._kv2_cache[sig] = entry
            if len(self._kv2_cache) > self._kv2_budget:
                _evict()
        refined_batch.append({"id": p.get("id"), "sig": sig, "refined": entry["refined"], "hits": entry["hits"]})

    context["kv2_wakekv"] = {
        "batch": refined_batch,
        "cache_size": len(self._kv2_cache),
        "pinned": len(self._wakekv_pins),
        "budget": self._kv2_budget,
    }
    return refined_batch
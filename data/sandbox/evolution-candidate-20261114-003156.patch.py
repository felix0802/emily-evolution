# Auto-generated code snippet by Emily Self-Modify
# Based on: KV-cache, Prototypical Visual Imagination, Generative Keyframing
# Generated: 2026-11-14T00:31:56.722800

def _kv_cache_imagination_evolve(self, papers, max_new=3):
    import hashlib, json
    from collections import OrderedDict

    class KVCache:
        def __init__(self, cap=64):
            self.cap = cap
            self.store = OrderedDict()
        def key(self, text):
            return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        def get(self, text):
            k = self.key(text)
            if k in self.store:
                self.store.move_to_end(k)
                return self.store[k]
            return None
        def put(self, text, value):
            k = self.key(text)
            self.store[k] = value
            self.store.move_to_end(k)
            if len(self.store) > self.cap:
                self.store.popitem(last=False)

    if not hasattr(self, "_kv_cache"):
        self._kv_cache = KVCache()

    def _prototypical_imagine(paper):
        abstract = (paper.get("summary") or paper.get("abstract") or "")[:600]
        cached = self._kv_cache.get(abstract)
        if cached is not None:
            return cached
        tokens = [t for t in abstract.replace("\n", " ").split(" ") if t]
        proto = tokens[:12] if tokens else ["novel", "method"]
        keyframes = []
        for i in range(0, min(len(tokens), 60), 12):
            chunk = tokens[i:i + 12]
            if chunk:
                keyframes.append(" ".join(chunk))
        imagined = {
            "prototype": " ".join(proto),
            "keyframes": keyframes[:5],
            "hypothesis": f"Apply {proto[0] if proto else 'technique'} to evolution-station pipeline",
        }
        self._kv_cache.put(abstract, imagined)
        return imagined

    def _generative_keyframe_plan(imagined_list):
        plan = []
        for idx, im in enumerate(imagined_list[:max_new]):
            plan.append({
                "step": idx + 1,
                "prototype": im["prototype"],
                "keyframes": im["keyframes"],
                "action": im["hypothesis"],
            })
        return plan

    imagined = [_prototypical_imagine(p) for p in papers[:max_new]]
    plan = _generative_keyframe_plan(imagined)
    self._last_imagination_plan = plan
    return plan
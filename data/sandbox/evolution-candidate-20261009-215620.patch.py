# Auto-generated code snippet by Emily Self-Modify
# Based on: PatchKV, DreamingGoose
# Generated: 2026-10-09T21:56:20.837125

def _patchkv_dreaming_goose_enhance(paper_meta: dict, repo_state: dict) -> dict:
    import hashlib, json, time
    from collections import OrderedDict

    class PatchKV:
        def __init__(self, capacity=64):
            self.capacity = capacity
            self.store = OrderedDict()

        def _key(self, k):
            return hashlib.sha256(json.dumps(k, sort_keys=True, default=str).encode()).hexdigest()[:16]

        def put(self, k, v, ttl=3600):
            key = self._key(k)
            self.store[key] = {"v": v, "exp": time.time() + ttl}
            if len(self.store) > self.capacity:
                self.store.popitem(last=False)
            return key

        def get(self, k):
            key = self._key(k)
            item = self.store.get(key)
            if not item:
                return None
            if item["exp"] < time.time():
                self.store.pop(key, None)
                return None
            self.store.move_to_end(key)
            return item["v"]

    class DreamingGoose:
        def __init__(self, kv):
            self.kv = kv
            self.dreams = []

        def dream(self, seed, branches=3, depth=2):
            frontier = [(seed, 0)]
            seen = set()
            while frontier:
                node, d = frontier.pop(0)
                if d >= depth:
                    continue
                h = hashlib.md5(json.dumps(node, sort_keys=True, default=str).encode()).hexdigest()[:8]
                if h in seen:
                    continue
                seen.add(h)
                for i in range(branches):
                    child = {
                        "parent": h,
                        "branch": i,
                        "seed": seed,
                        "depth": d + 1,
                        "novelty": (hash(h + str(i)) % 1000) / 1000.0,
                    }
                    self.dreams.append(child)
                    frontier.append((child, d + 1))
            self.dreams.sort(key=lambda x: x["novelty"], reverse=True)
            return self.dreams[:branches]

    kv = PatchKV(capacity=128)
    goose = DreamingGoose(kv)

    cache_key = {"paper": paper_meta.get("id"), "repo": repo_state.get("head")}
    cached = kv.get(cache_key)
    if cached:
        return cached

    seed = {
        "title": paper_meta.get("title", ""),
        "abstract": paper_meta.get("summary", "")[:256],
        "repo_files": list(repo_state.get("files", {}).keys())[:16],
    }
    dreams = goose.dream(seed, branches=4, depth=2)

    result = {
        "patchkv_hit": False,
        "dream_candidates": dreams,
        "top_novelty": dreams[0]["novelty"] if dreams else 0.0,
        "suggested_patch_targets": [d["parent"] for d in dreams[:2]],
    }
    kv.put(cache_key, result, ttl=1800)
    return result
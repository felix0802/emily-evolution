# Auto-generated code snippet by Emily Self-Modify
# Based on: Attic-KV, ReadKV
# Generated: 2026-10-09T17:37:52.127059

def enhance_with_attic_readkv(station, papers, max_kv_bytes=65536):
    import hashlib, json, base64, zlib
    from collections import OrderedDict

    class AtticKV:
        def __init__(self, cap=max_kv_bytes):
            self.cap = cap
            self.store = OrderedDict()
            self.bytes = 0

        def _evict(self):
            while self.bytes > self.cap and self.store:
                _, (k, v) = self.store.popitem(last=False)
                self.bytes -= len(k) + len(v)

        def put(self, key, value):
            k = hashlib.sha256(key.encode()).hexdigest()[:16]
            v = base64.b64encode(zlib.compress(json.dumps(value).encode(), 6)).decode()
            if k in self.store:
                self.bytes -= len(k) + len(self.store[k][1])
                del self.store[k]
            self.store[k] = (key, v)
            self.bytes += len(k) + len(v)
            self._evict()
            return k

        def get(self, key):
            k = hashlib.sha256(key.encode()).hexdigest()[:16]
            if k not in self.store:
                return None
            self.store.move_to_end(k)
            _, v = self.store[k]
            return json.loads(zlib.decompress(base64.b64decode(v)).decode())

    class ReadKV:
        def __init__(self, attic):
            self.attic = attic
            self.hits = 0
            self.misses = 0

        def read(self, key, loader):
            val = self.attic.get(key)
            if val is not None:
                self.hits += 1
                return val
            self.misses += 1
            val = loader()
            self.attic.put(key, val)
            return val

    attic = AtticKV()
    rkv = ReadKV(attic)
    enriched = []
    for p in papers:
        pid = p.get("id") or p.get("arxiv_id") or hashlib.md5(json.dumps(p, sort_keys=True).encode()).hexdigest()
        cached = rkv.read(f"paper::{pid}", lambda: {
            "title": p.get("title", ""),
            "summary": p.get("summary", "")[:2000],
            "tags": p.get("categories", []),
        })
        enriched.append({**p, "_attic": cached})
    station["_attic_kv"] = attic
    station["_read_kv"] = rkv
    station["_attic_stats"] = {"hits": rkv.hits, "misses": rkv.misses, "bytes": attic.bytes}
    return enriched
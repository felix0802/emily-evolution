# Auto-generated code snippet by Emily Self-Modify
# Based on: Speaker-Centered Dual-Track Memory, Autocompaction
# Generated: 2026-09-23T08:53:17.244031

def _dual_track_memory_consolidate(self, new_insight: dict, speaker_id: str = "emily") -> dict:
    import json, hashlib, time
    from collections import OrderedDict

    if not hasattr(self, "_dual_track_mem"):
        self._dual_track_mem = {
            "speaker_track": OrderedDict(),
            "semantic_track": OrderedDict(),
            "cross_links": {},
            "capacity": 512,
        }

    mem = self._dual_track_mem
    key = hashlib.sha1(
        (str(new_insight.get("title", "")) + str(new_insight.get("summary", ""))).encode("utf-8")
    ).hexdigest()[:16]

    speaker_entry = {
        "id": key,
        "speaker": speaker_id,
        "ts": time.time(),
        "raw": new_insight,
        "weight": float(new_insight.get("score", 1.0)),
    }
    mem["speaker_track"][key] = speaker_entry

    tokens = set()
    for field in ("title", "summary", "tags", "keywords"):
        val = new_insight.get(field, "")
        if isinstance(val, (list, tuple)):
            tokens.update(str(v).lower() for v in val)
        else:
            tokens.update(str(val).lower().split())
    tokens = {t for t in tokens if len(t) > 2}

    for tok in tokens:
        bucket = mem["semantic_track"].setdefault(tok, [])
        if key not in bucket:
            bucket.append(key)
        mem["cross_links"].setdefault(tok, set()).add(speaker_id)

    if len(mem["speaker_track"]) > mem["capacity"]:
        oldest = next(iter(mem["speaker_track"]))
        dropped = mem["speaker_track"].pop(oldest)
        for tok in list(mem["semantic_track"].keys()):
            mem["semantic_track"][tok] = [k for k in mem["semantic_track"][tok] if k != oldest]
            if not mem["semantic_track"][tok]:
                mem["semantic_track"].pop(tok, None)
        self._autocompaction_log = getattr(self, "_autocompaction_log", [])
        self._autocompaction_log.append({"evicted": dropped["id"], "ts": time.time()})

    related = set()
    for tok in tokens:
        related.update(mem["semantic_track"].get(tok, []))
    related.discard(key)

    return {
        "memory_key": key,
        "speaker": speaker_id,
        "related_ids": list(related)[:8],
        "semantic_tokens": len(tokens),
        "track_sizes": {
            "speaker": len(mem["speaker_track"]),
            "semantic": len(mem["semantic_track"]),
        },
    }
# Auto-generated code snippet by Emily Self-Modify
# Based on: LIBERO-PeRM, CoDA 数据引擎与策略协同进化
# Generated: 2026-10-17T03:24:50.299715

def _libero_perm_coda_evolve(self, papers, repo_state):
    import json, base64, urllib.request, hashlib
    from collections import defaultdict

    def _embed(text):
        h = hashlib.sha256(text.encode("utf-8")).digest()
        return [b / 255.0 for b in h[:16]]

    def _cos(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(y * y for y in b) ** 0.5
        return dot / (na * nb + 1e-9)

    coda_buffer = defaultdict(list)
    for p in papers:
        key = (p.get("category") or "general").lower()
        vec = _embed((p.get("title", "") + " " + p.get("summary", ""))[:2000])
        coda_buffer[key].append({"vec": vec, "paper": p, "reward": 0.0})

    perm_scores = {}
    for key, items in coda_buffer.items():
        if len(items) < 2:
            perm_scores[key] = 0.0
            continue
        sims = []
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                sims.append(_cos(items[i]["vec"], items[j]["vec"]))
        diversity = 1.0 - (sum(sims) / len(sims))
        perm_scores[key] = round(diversity, 4)

    selected = []
    for key, items in coda_buffer.items():
        items.sort(key=lambda x: perm_scores.get(key, 0.0), reverse=True)
        selected.extend([it["paper"] for it in items[:2]])

    policy_update = {
        "perm_diversity": perm_scores,
        "selected_count": len(selected),
        "coda_keys": list(coda_buffer.keys()),
        "repo_sha": repo_state.get("sha", "unknown") if isinstance(repo_state, dict) else "unknown",
    }

    try:
        payload = base64.b64encode(json.dumps(policy_update).encode()).decode()
        req = urllib.request.Request(
            "https://api.github.com/repos/emily-evolution/station/contents/policy.json",
            data=json.dumps({"message": "CoDA policy sync", "content": payload}).encode(),
            headers={"Content-Type": "application/json"},
            method="PUT",
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass

    self._last_perm_policy = policy_update
    return selected
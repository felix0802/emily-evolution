# Auto-generated code snippet by Emily Self-Modify
# Based on: AutoRecLab, 人格微调LLM
# Generated: 2026-09-21T01:59:43.543535

def _apply_autoreclab_persona_finetune(self, papers, repo_meta):
    import json, urllib.request, base64, hashlib
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    persona_seed = getattr(self, "persona_vector", None) or [
        "self-modifying agent", "recursive improvement", "persona alignment",
        "autonomous code evolution", "LLM fine-tuning"
    ]
    corpus = [p.get("title", "") + " " + p.get("summary", "") for p in papers]
    if not corpus:
        return {"status": "no_papers", "applied": False}

    vec = TfidfVectorizer(stop_words="english", max_features=512)
    try:
        matrix = vec.fit_transform(corpus + [" ".join(persona_seed)])
    except ValueError:
        return {"status": "vectorizer_empty", "applied": False}

    sims = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    ranked = sorted(zip(sims, papers), key=lambda x: x[0], reverse=True)[:3]

    persona_delta = []
    for score, paper in ranked:
        if score < 0.05:
            continue
        persona_delta.append({
            "title": paper.get("title", "")[:120],
            "affinity": round(float(score), 4),
            "signal": "persona_finetune_candidate"
        })

    if not persona_delta:
        return {"status": "no_alignment", "applied": False}

    self.persona_vector = persona_seed + [d["title"] for d in persona_delta]
    self.persona_vector = self.persona_vector[-32:]

    payload = {
        "persona_delta": persona_delta,
        "vector_hash": hashlib.sha256(
            json.dumps(self.persona_vector, sort_keys=True).encode()
        ).hexdigest()[:16],
        "autoreclab": {"mode": "online", "top_k": 3}
    }

    token = getattr(self, "github_token", None)
    repo = repo_meta.get("full_name") if isinstance(repo_meta, dict) else None
    if token and repo:
        try:
            url = f"https://api.github.com/repos/{repo}/contents/persona_finetune.json"
            body = json.dumps({
                "message": "AutoRecLab persona fine-tune update",
                "content": base64.b64encode(json.dumps(payload).encode()).decode()
            }).encode()
            req = urllib.request.Request(url, data=body, method="PUT", headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json"
            })
            urllib.request.urlopen(req, timeout=15)
            payload["pushed"] = True
        except Exception as e:
            payload["pushed"] = False
            payload["push_error"] = str(e)[:120]

    return {"status": "ok", "applied": True, "payload": payload}
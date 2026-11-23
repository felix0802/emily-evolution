# Auto-generated code snippet by Emily Self-Modify
# Based on: 黑盒归约 (Black-box reduction), NoPeBench 基准
# Generated: 2026-11-23T16:40:42.590863

def apply_blackbox_reduction_and_nopebench(self, papers, repo_state):
    import json, urllib.request, base64, hashlib
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    def _nopebench_score(candidate, baseline):
        if not candidate or not baseline:
            return 0.0
        vec = TfidfVectorizer(stop_words="english").fit([candidate, baseline])
        sim = cosine_similarity(vec.transform([candidate]), vec.transform([baseline]))[0][0]
        novelty = 1.0 - float(sim)
        length_penalty = min(1.0, len(candidate) / max(1, len(baseline)))
        return round(0.7 * novelty + 0.3 * length_penalty, 4)

    def _blackbox_reduce(paper_text, max_tokens=180):
        sentences = [s.strip() for s in paper_text.replace("\n", " ").split(".") if s.strip()]
        if not sentences:
            return ""
        vec = TfidfVectorizer(stop_words="english")
        try:
            mat = vec.fit_transform(sentences)
        except ValueError:
            return " ".join(sentences[:3])
        scores = mat.sum(axis=1).A1
        ranked = [s for _, s in sorted(zip(scores, sentences), reverse=True)]
        reduced, total = [], 0
        for s in ranked:
            total += len(s.split())
            if total > max_tokens:
                break
            reduced.append(s)
        return ". ".join(reduced) + "."

    reduced_papers = []
    for p in papers:
        abstract = p.get("abstract", "") or p.get("summary", "")
        reduced = _blackbox_reduce(abstract)
        score = _nopebench_score(reduced, abstract)
        reduced_papers.append({
            "id": p.get("id", hashlib.md5(reduced.encode()).hexdigest()[:8]),
            "title": p.get("title", ""),
            "reduced": reduced,
            "nopebench": score,
        })

    reduced_papers.sort(key=lambda x: x["nopebench"], reverse=True)
    top = reduced_papers[:5]

    payload = {
        "message": "evolution-station: blackbox reduction + NoPeBench",
        "content": base64.b64encode(json.dumps(top, indent=2).encode()).decode(),
    }
    token = getattr(self, "github_token", None)
    repo = getattr(self, "github_repo", None)
    if token and repo:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/contents/nopebench_results.json",
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"token {token}", "Accept": "application/vnd.github+json"},
            method="PUT",
        )
        try:
            urllib.request.urlopen(req, timeout=15)
        except Exception:
            pass

    self.last_reduction = top
    return top
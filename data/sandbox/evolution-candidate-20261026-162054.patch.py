# Auto-generated code snippet by Emily Self-Modify
# Based on: 零成本代理, 跨任务迁移学习
# Generated: 2026-10-26T16:20:54.484420

def _zero_cost_transfer_boost(perception, understanding, decision, action, verify):
    import json, urllib.request, base64
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    def _fetch(url):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "evolution-station"})
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read().decode("utf-8", "ignore"))
        except Exception:
            return None

    def _proxy_llm(prompt, context):
        # zero-cost proxy: reuse local perception/understanding outputs instead of paid LLM calls
        try:
            return understanding(prompt, context=context)
        except TypeError:
            return understanding(prompt)

    def _transfer_knowledge(source_task, target_task):
        # cross-task transfer: align source/target representations via TF-IDF cosine
        try:
            vec = TfidfVectorizer(stop_words="english").fit_transform([source_task, target_task])
            sim = float(cosine_similarity(vec[0], vec[1])[0][0])
        except Exception:
            sim = 0.0
        return sim

    def _github_push(repo, path, content, token):
        try:
            api = f"https://api.github.com/repos/{repo}/contents/{path}"
            payload = json.dumps({
                "message": "evolution-station: zero-cost transfer update",
                "content": base64.b64encode(content.encode()).decode()
            }).encode()
            req = urllib.request.Request(api, data=payload, method="PUT",
                headers={"Authorization": f"token {token}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.status == 200
        except Exception:
            return False

    try:
        papers = _fetch("http://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=3")
        ctx = perception(papers) if papers else {}
        prompt = "Propose a zero-cost improvement using cross-task transfer."
        proposal = _proxy_llm(prompt, ctx)
        sim = _transfer_knowledge(str(ctx), str(proposal))
        if sim > 0.3:
            plan = decision(proposal, context=ctx)
            result = action(plan)
            ok = verify(result)
            if ok:
                _github_push("emily/evolution-station", "artifacts/transfer.json",
                             json.dumps({"sim": sim, "proposal": str(proposal)[:500]}),
                             "GITHUB_TOKEN")
            return {"sim": sim, "verified": ok}
        return {"sim": sim, "verified": False}
    except Exception as e:
        return {"error": str(e)}

# insert into evolve():
# _zero_cost_transfer_boost(perception, understanding, decision, action, verify)
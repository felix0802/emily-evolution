# Auto-generated code snippet by Emily Self-Modify
# Based on: LIBERO-PeRM 基准, T2-z 测试时环境潜变量优化, CoDA 数据引擎与策略协同演化
# Generated: 2026-10-16T17:46:39.198646

def _evolve_with_libero_perm_and_coda(self, papers, repo_state):
    import json, urllib.request, urllib.parse, base64, hashlib
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    # 1) LIBERO-PeRM 基准：从论文中抽取任务/指标，构造可复现评测清单
    perm_tasks = []
    for p in papers:
        text = (p.get("title", "") + " " + p.get("summary", "")).lower()
        if any(k in text for k in ("libero", "perm", "manipulation", "long-horizon")):
            perm_tasks.append({
                "task_id": hashlib.md5(p.get("id", p.get("title", "")).encode()).hexdigest()[:12],
                "source": p.get("id", ""),
                "metrics": [m for m in ("success_rate", "path_length", "energy", "robustness")
                            if m in text] or ["success_rate"],
                "horizon": "long" if "long-horizon" in text else "short",
            })

    # 2) T2-z 测试时环境潜变量优化：用 TF-IDF 在论文语料上估计环境潜变量 z
    corpus = [p.get("title", "") + " " + p.get("summary", "") for p in papers] or ["empty"]
    vec = TfidfVectorizer(max_features=256, stop_words="english")
    X = vec.fit_transform(corpus)
    z = X.mean(axis=0).A1 if X.shape[0] > 0 else [0.0]
    z_norm = (z / (sum(z) + 1e-9)).tolist()

    # 3) CoDA 数据引擎与策略协同演化：按 z 加权采样，生成协同演化批次
    sim = cosine_similarity(X, X) if X.shape[0] > 1 else [[1.0]]
    co_evolve_batch = []
    for i, p in enumerate(papers):
        weight = float(sum(sim[i])) / max(len(papers), 1)
        co_evolve_batch.append({
            "paper": p.get("id", p.get("title", "")),
            "co_evolve_weight": round(weight, 4),
            "z_alignment": round(float(z_norm[i % len(z_norm)]), 4),
        })
    co_evolve_batch.sort(key=lambda x: x["co_evolve_weight"], reverse=True)

    # 4) 将结果注入 evolution-station 的决策层与验证层
    self.state["libero_perm_tasks"] = perm_tasks
    self.state["t2z_latent"] = z_norm[:32]
    self.state["coda_batch"] = co_evolve_batch[:16]

    # 5) 通过 GitHub API 推送协同演化产物
    if getattr(self, "github_token", None) and getattr(self, "github_repo", None):
        payload = json.dumps({
            "libero_perm_tasks": perm_tasks,
            "t2z_latent": z_norm[:32],
            "coda_batch": co_evolve_batch[:16],
        }).encode()
        url = f"https://api.github.com/repos/{self.github_repo}/contents/evolution/libero_perm_coda.json"
        req = urllib.request.Request(url, data=json.dumps({
            "message": "evolve: LIBERO-PeRM + T2-z + CoDA artifacts",
            "content": base64.b64encode(payload).decode(),
        }).encode(), headers={
            "Authorization": f"token {self.github_token}",
            "Content-Type": "application/json",
        }, method="PUT")
        try:
            urllib.request.urlopen(req, timeout=15)
        except Exception:
            pass

    return {"perm_tasks": len(perm_tasks), "z_dim": len(z_norm), "coda": len(co_evolve_batch)}
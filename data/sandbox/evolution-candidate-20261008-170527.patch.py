# Auto-generated code snippet by Emily Self-Modify
# Based on: 3D物体记忆, RLVR中的探索与优化解耦
# Generated: 2026-10-08T17:05:27.590545

def _spatial_memory_guided_exploration(self, state, candidate_actions, memory_bank=None, rng=None):
    import numpy as np
    from collections import defaultdict

    if rng is None:
        rng = np.random.default_rng()
    if memory_bank is None:
        memory_bank = getattr(self, "spatial_memory", defaultdict(lambda: {"pos": None, "reward": 0.0, "visits": 0}))

    def _key(a):
        return json.dumps(a, sort_keys=True, default=str)

    # 1) 3D 物体记忆：把候选动作映射到空间嵌入，检索最近邻经验
    def _embed(action):
        vec = []
        for k in sorted(action.keys()) if isinstance(action, dict) else [str(action)]:
            v = action[k] if isinstance(action, dict) else action
            try:
                vec.append(float(v))
            except (TypeError, ValueError):
                vec.append(float(abs(hash(str(v))) % 1000) / 1000.0)
        while len(vec) < 3:
            vec.append(0.0)
        return np.asarray(vec[:3], dtype=float)

    scored = []
    for a in candidate_actions:
        k = _key(a)
        rec = memory_bank.get(k, {"pos": None, "reward": 0.0, "visits": 0})
        emb = _embed(a)
        novelty = 1.0
        if rec.get("pos") is not None:
            d = float(np.linalg.norm(emb - np.asarray(rec["pos"], dtype=float)))
            novelty = float(np.tanh(d))
        exploit = float(rec.get("reward", 0.0)) / (1.0 + float(rec.get("visits", 0)))
        # 2) RLVR 探索/优化解耦：探索项与利用项独立加权，互不干扰
        explore_term = self._explore_weight * novelty
        exploit_term = self._exploit_weight * exploit
        score = exploit_term + explore_term
        scored.append((score, a, k, emb))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_action, best_key, best_emb = scored[0]

    # 3) 更新 3D 物体记忆
    memory_bank[best_key]["pos"] = best_emb.tolist()
    memory_bank[best_key]["visits"] = memory_bank[best_key].get("visits", 0) + 1
    self.spatial_memory = memory_bank

    # 4) 解耦调度：按探索预算决定是否注入随机扰动
    if rng.random() < self._explore_ratio:
        jitter = rng.normal(0, self._explore_sigma, size=best_emb.shape)
        perturbed = best_emb + jitter
        memory_bank[best_key]["pos"] = perturbed.tolist()

    return best_action, {"score": best_score, "novelty": float(novelty), "exploit": float(exploit)}
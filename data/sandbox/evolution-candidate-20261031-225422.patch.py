# Auto-generated code snippet by Emily Self-Modify
# Based on: 统一 RL 目标（最大似然推导）, 保形预测（Conformal Prediction）
# Generated: 2026-10-31T22:54:22.432100

def _unified_rl_conformal_evolve(self, papers, state):
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.isotonic import IsotonicRegression

    # 1. 统一 RL 目标：最大似然推导的奖励加权
    def _mle_reward(paper):
        try:
            score = float(paper.get("relevance", 0.5))
            novelty = float(paper.get("novelty", 0.5))
            feasibility = float(paper.get("feasibility", 0.5))
            log_lik = np.log(max(score, 1e-6)) + np.log(max(novelty, 1e-6)) + np.log(max(feasibility, 1e-6))
            return float(np.exp(log_lik / 3.0))
        except Exception:
            return 0.5

    rewards = np.array([_mle_reward(p) for p in papers]) if papers else np.array([0.5])
    weights = rewards / (rewards.sum() + 1e-9)

    # 2. 保形预测：构建非一致性分数与校准阈值
    calib_scores = np.abs(rewards - rewards.mean())
    alpha = 0.1
    n = len(calib_scores)
    q_level = min(1.0, np.ceil((n + 1) * (1 - alpha)) / max(n, 1))
    try:
        iso = IsotonicRegression(out_of_bounds="clip")
        iso.fit(np.arange(n), np.sort(calib_scores))
        threshold = float(np.quantile(calib_scores, q_level))
    except Exception:
        threshold = float(np.quantile(calib_scores, q_level)) if n > 0 else 0.5

    # 3. 融合决策：加权选择 + 保形过滤
    selected = []
    for i, p in enumerate(papers):
        score = rewards[i]
        nonconformity = abs(score - rewards.mean())
        if nonconformity <= threshold:
            p["_rl_weight"] = float(weights[i])
            p["_conformal_ok"] = True
            p["_nonconformity"] = float(nonconformity)
            selected.append(p)
        else:
            p["_conformal_ok"] = False

    if not selected and papers:
        selected = [papers[int(np.argmax(rewards))]]

    state["rl_conformal"] = {
        "alpha": alpha,
        "threshold": threshold,
        "n_calib": n,
        "n_selected": len(selected),
        "mean_reward": float(rewards.mean()),
    }
    return selected

# 在 evolve() 中调用：
# papers = self._unified_rl_conformal_evolve(papers, self.state)
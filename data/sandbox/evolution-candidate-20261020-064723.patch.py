# Auto-generated code snippet by Emily Self-Modify
# Based on: 不确定性感知协同预测, 因果约束离线强化学习
# Generated: 2026-10-20T06:47:23.899342

def uncertainty_aware_causal_evolve(papers, state, n_samples=8, alpha=0.1):
    import numpy as np
    from sklearn.ensemble import RandomForestRegressor

    def _featurize(p):
        txt = (p.get("title", "") + " " + p.get("summary", "")).lower()
        keys = ["rl", "causal", "uncertainty", "bayes", "offline", "policy", "model"]
        return [txt.count(k) for k in keys] + [len(txt) / 1000.0]

    X = np.array([_featurize(p) for p in papers]) if papers else np.zeros((1, 8))
    y = np.array([p.get("score", 0.0) for p in papers]) if papers else np.zeros(1)

    if len(X) >= 3:
        rf = RandomForestRegressor(n_estimators=50, random_state=0)
        rf.fit(X, y)
        preds = np.array([t.predict(X) for t in rf.estimators_])
        mu = preds.mean(axis=0)
        sigma = preds.std(axis=0) + 1e-6
        ucb = mu + alpha * sigma
        order = np.argsort(-ucb)
    else:
        order = np.argsort(-y)

    selected = [papers[i] for i in order[: max(1, len(papers) // 3)]]

    causal_gain = 0.0
    for p in selected:
        txt = (p.get("title", "") + " " + p.get("summary", "")).lower()
        if "causal" in txt and ("policy" in txt or "offline" in txt):
            causal_gain += 1.0
    causal_gain /= max(1, len(selected))

    state["uncertainty_ucb"] = float(np.mean(ucb)) if len(ucb) else 0.0
    state["causal_alignment"] = causal_gain
    state["selected_papers"] = selected

    if causal_gain > 0.3:
        state["strategy"] = "causal_offline_rl"
    else:
        state["strategy"] = "uncertainty_explore"

    return state
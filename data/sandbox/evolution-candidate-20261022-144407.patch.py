# Auto-generated code snippet by Emily Self-Modify
# Based on: 元学习（Meta-Learning）, 时间序列基础模型（TSFM）
# Generated: 2026-10-22T14:44:07.462178

def meta_learn_evolution_params(history: list, window: int = 20) -> dict:
    import numpy as np
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler

    if len(history) < window + 2:
        return {"lr": 0.1, "explore": 0.3, "decay": 0.95, "tsfm_weight": 0.5}

    scores = np.array([h.get("score", 0.0) for h in history], dtype=float)
    feats = []
    targets = []
    for i in range(window, len(scores) - 1):
        seg = scores[i - window:i]
        trend = seg[-1] - seg[0]
        vol = float(np.std(seg))
        mom = float(np.mean(seg[-3:]) - np.mean(seg[:3]))
        feats.append([seg[-1], trend, vol, mom])
        targets.append(scores[i + 1] - scores[i])
    if len(feats) < 3:
        return {"lr": 0.1, "explore": 0.3, "decay": 0.95, "tsfm_weight": 0.5}

    X = np.array(feats, dtype=float)
    y = np.array(targets, dtype=float)
    scaler = StandardScaler().fit(X)
    model = Ridge(alpha=1.0).fit(scaler.transform(X), y)

    recent = scores[-window:]
    cur = np.array([[recent[-1],
                     recent[-1] - recent[0],
                     float(np.std(recent)),
                     float(np.mean(recent[-3:]) - np.mean(recent[:3]))]])
    pred_delta = float(model.predict(scaler.transform(cur))[0])

    lr = float(np.clip(0.05 + 0.2 * abs(pred_delta), 0.02, 0.5))
    explore = float(np.clip(0.5 - 0.4 * pred_delta, 0.05, 0.8))
    decay = float(np.clip(0.9 + 0.05 * np.sign(pred_delta), 0.85, 0.99))
    tsfm_weight = float(np.clip(0.5 + 0.5 * np.tanh(pred_delta), 0.1, 0.9))

    return {"lr": lr, "explore": explore, "decay": decay, "tsfm_weight": tsfm_weight}


def evolve():
    history = getattr(evolve, "_history", [])
    params = meta_learn_evolution_params(history)
    apply_evolution_params(params)
    result = run_evolution_step(params)
    history.append({"score": result.get("score", 0.0), "params": params})
    evolve._history = history[-200:]
    return result
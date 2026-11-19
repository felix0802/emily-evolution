# Auto-generated code snippet by Emily Self-Modify
# Based on: 闭式最小二乘元学习, 形式验证安全RL
# Generated: 2026-11-19T04:46:21.213219

def _meta_learn_closed_form(history, ridge=1e-3):
    import numpy as np
    if len(history) < 4:
        return None
    X, y = [], []
    for h in history:
        feats = h.get("features")
        score = h.get("score")
        if feats is None or score is None:
            continue
        X.append(np.asarray(feats, dtype=float).ravel())
        y.append(float(score))
    if len(X) < 4:
        return None
    X = np.asarray(X)
    y = np.asarray(y)
    d = X.shape[1]
    A = X.T @ X + ridge * np.eye(d)
    b = X.T @ y
    try:
        w = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        return None
    preds = X @ w
    resid = y - preds
    sigma2 = float(np.mean(resid ** 2)) + 1e-9
    return {"weights": w.tolist(), "sigma2": sigma2, "n": len(X)}


def _verify_safe_action(action, meta, bounds=(-1e3, 1e3), max_norm=1e3):
    import numpy as np
    if action is None:
        return False, "null_action"
    try:
        vec = np.asarray(action, dtype=float).ravel()
    except Exception:
        return False, "non_numeric"
    if not np.all(np.isfinite(vec)):
        return False, "non_finite"
    if np.any(vec < bounds[0]) or np.any(vec > bounds[1]):
        return False, "out_of_bounds"
    if float(np.linalg.norm(vec)) > max_norm:
        return False, "norm_exceeded"
    if meta is not None:
        w = np.asarray(meta["weights"], dtype=float)
        if w.shape[0] == vec.shape[0]:
            pred = float(vec @ w)
            if pred < -3.0 * (meta["sigma2"] ** 0.5):
                return False, "predicted_unsafe"
    return True, "ok"


def _evolve_with_meta_and_verify(history, candidate_actions, apply_fn):
    meta = _meta_learn_closed_form(history)
    accepted = []
    for act in candidate_actions:
        ok, reason = _verify_safe_action(act, meta)
        if ok:
            accepted.append(act)
    if not accepted:
        return {"meta": meta, "applied": 0, "rejected": len(candidate_actions)}
    for act in accepted:
        apply_fn(act)
    return {"meta": meta, "applied": len(accepted), "rejected": len(candidate_actions) - len(accepted)}
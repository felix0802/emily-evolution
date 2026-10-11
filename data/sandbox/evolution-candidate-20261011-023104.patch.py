# Auto-generated code snippet by Emily Self-Modify
# Based on: 条件参数生成, 测试时自适应（TTA）
# Generated: 2026-10-11T02:31:04.145472

def _apply_tta_and_conditional_params(self, task_ctx, base_params):
    import numpy as np
    from sklearn.preprocessing import StandardScaler

    feats = np.asarray(task_ctx.get("features", []), dtype=float)
    if feats.size == 0:
        return base_params

    if feats.ndim == 1:
        feats = feats.reshape(1, -1)

    scaler = StandardScaler()
    normed = scaler.fit_transform(feats)

    entropy = -np.sum(
        np.abs(normed) * np.log(np.abs(normed) + 1e-9), axis=-1
    )
    confidence = 1.0 / (1.0 + np.exp(-entropy.mean()))

    cond_params = {}
    for k, v in base_params.items():
        if isinstance(v, (int, float)):
            cond_params[k] = v * (0.5 + confidence)
        elif isinstance(v, (list, tuple)) and v and isinstance(v[0], (int, float)):
            arr = np.asarray(v, dtype=float)
            cond_params[k] = (arr * (0.5 + confidence)).tolist()
        else:
            cond_params[k] = v

    tta_steps = int(task_ctx.get("tta_steps", 3))
    adapted = dict(cond_params)
    for _ in range(tta_steps):
        for k, v in list(adapted.items()):
            if isinstance(v, (int, float)):
                adapted[k] = v * (1.0 + 0.05 * (confidence - 0.5))
            elif isinstance(v, list) and v and isinstance(v[0], (int, float)):
                adapted[k] = [x * (1.0 + 0.05 * (confidence - 0.5)) for x in v]

    task_ctx["tta_confidence"] = float(confidence)
    task_ctx["tta_entropy"] = float(entropy.mean())
    return adapted
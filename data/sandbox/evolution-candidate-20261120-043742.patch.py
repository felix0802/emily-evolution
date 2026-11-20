# Auto-generated code snippet by Emily Self-Modify
# Based on: Channel-Independent / Channel-Dependent 互补建模, 固定大小历史表示（Timestamped Recent Events + Statistical Summaries）
# Generated: 2026-11-20T04:37:42.506312

def _channel_complementary_model(series, channel_axis=-1, window=32):
    import numpy as np
    arr = np.asarray(series, dtype=float)
    if arr.ndim == 1:
        arr = arr[:, None]
    if arr.shape[0] < 2:
        return {"ci": arr.copy(), "cd": arr.copy(), "fused": arr.copy()}
    n, c = arr.shape
    w = max(2, min(window, n))
    ci = np.zeros_like(arr)
    for ch in range(c):
        x = arr[:, ch]
        for i in range(n):
            lo = max(0, i - w + 1)
            seg = x[lo:i + 1]
            ci[i, ch] = seg.mean()
    cd = np.zeros_like(arr)
    if c > 1:
        for i in range(n):
            lo = max(0, i - w + 1)
            seg = arr[lo:i + 1]
            mu = seg.mean(axis=0)
            cov = np.cov(seg.T) if seg.shape[0] > 1 else np.eye(c)
            cov = np.atleast_2d(cov) + 1e-6 * np.eye(c)
            inv = np.linalg.pinv(cov)
            resid = arr[i] - mu
            cd[i] = resid @ inv
    else:
        cd = arr - ci
    ci_n = (ci - ci.mean(axis=0)) / (ci.std(axis=0) + 1e-8)
    cd_n = (cd - cd.mean(axis=0)) / (cd.std(axis=0) + 1e-8)
    fused = 0.5 * ci_n + 0.5 * cd_n
    return {"ci": ci, "cd": cd, "fused": fused}


def _fixed_size_history(events, stats, max_events=64):
    import numpy as np
    ev = list(events)[-max_events:]
    padded = ev + [None] * (max_events - len(ev))
    stat_vec = []
    for k in sorted(stats.keys()):
        v = stats[k]
        if isinstance(v, (int, float)):
            stat_vec.append(float(v))
        elif isinstance(v, (list, tuple)) and v and all(isinstance(x, (int, float)) for x in v):
            stat_vec.extend(float(x) for x in v)
    return {"recent_events": padded, "stat_summary": np.asarray(stat_vec, dtype=float)}
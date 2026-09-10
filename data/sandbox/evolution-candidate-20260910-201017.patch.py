# Auto-generated code snippet by Emily Self-Modify
# Based on: 硬件感知深度学习, 无污染时间序列留出评估
# Generated: 2026-09-10T20:10:17.647626

def hardware_aware_holdout_eval(series, model_factory, n_splits=5, purge_gap=1, device_budget=None):
    import numpy as np
    from sklearn.metrics import mean_squared_error

    series = np.asarray(series, dtype=float)
    n = len(series)
    if n < n_splits * 2 + purge_gap:
        return {"error": "insufficient_data", "n": n}

    fold_size = n // (n_splits + 1)
    scores, latencies = [], []

    for i in range(n_splits):
        train_end = fold_size * (i + 1)
        test_start = train_end + purge_gap
        test_end = min(test_start + fold_size, n)
        if test_start >= test_end:
            continue

        train = series[:train_end]
        test = series[test_start:test_end]

        model = model_factory()
        import time
        t0 = time.perf_counter()
        model.fit(train[:-1].reshape(-1, 1), train[1:])
        pred = model.predict(test[:-1].reshape(-1, 1))
        latencies.append(time.perf_counter() - t0)

        if len(pred) and len(test[1:]) == len(pred):
            scores.append(float(np.sqrt(mean_squared_error(test[1:], pred))))

    if not scores:
        return {"error": "no_valid_folds"}

    result = {
        "rmse_mean": float(np.mean(scores)),
        "rmse_std": float(np.std(scores)),
        "n_folds": len(scores),
        "purge_gap": purge_gap,
        "latency_mean_s": float(np.mean(latencies)),
    }

    if device_budget is not None:
        result["within_budget"] = result["latency_mean_s"] <= device_budget
        result["budget_ratio"] = result["latency_mean_s"] / max(device_budget, 1e-9)

    return result
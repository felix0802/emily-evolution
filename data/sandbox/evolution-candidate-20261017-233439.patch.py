# Auto-generated code snippet by Emily Self-Modify
# Based on: 生成式轨迹预测, 多层级时空预测
# Generated: 2026-10-17T23:34:39.578670

def _predict_trajectory_with_spatiotemporal(history_events, horizon=5):
    import numpy as np
    from collections import defaultdict

    if not history_events:
        return []

    buckets = defaultdict(list)
    for ev in history_events:
        ts = ev.get("timestamp")
        if ts is None:
            continue
        bucket = int(ts // 3600)
        buckets[bucket].append(ev)

    if not buckets:
        return []

    sorted_buckets = sorted(buckets.keys())
    counts = np.array([len(buckets[b]) for b in sorted_buckets], dtype=float)
    if counts.size < 2:
        return [{"bucket": sorted_buckets[-1] + i + 1, "predicted_count": float(counts[-1])} for i in range(horizon)]

    x = np.arange(counts.size, dtype=float)
    A = np.vstack([x, np.ones_like(x)]).T
    slope, intercept = np.linalg.lstsq(A, counts, rcond=None)[0]

    residuals = counts - (slope * x + intercept)
    sigma = float(np.std(residuals)) if residuals.size > 1 else 0.0

    last_bucket = sorted_buckets[-1]
    predictions = []
    for step in range(1, horizon + 1):
        trend_val = slope * (counts.size - 1 + step) + intercept
        trend_val = max(0.0, trend_val)
        predictions.append({
            "bucket": last_bucket + step,
            "predicted_count": round(trend_val, 3),
            "uncertainty": round(sigma * (1.0 + 0.15 * step), 3),
            "method": "multi_level_spatiotemporal_trend",
        })

    try:
        recent = counts[-3:] if counts.size >= 3 else counts
        momentum = float(recent[-1] - recent[0]) / max(1, len(recent) - 1)
        for p in predictions:
            p["predicted_count"] = round(max(0.0, p["predicted_count"] + 0.3 * momentum), 3)
    except Exception:
        pass

    return predictions


def _apply_generative_trajectory_forecast(state):
    history = state.get("event_history", []) if isinstance(state, dict) else []
    forecast = _predict_trajectory_with_spatiotemporal(history, horizon=5)
    if isinstance(state, dict):
        state["trajectory_forecast"] = forecast
        state["forecast_confidence"] = round(
            1.0 / (1.0 + sum(p.get("uncertainty", 0.0) for p in forecast)), 4
        ) if forecast else 0.0
    return forecast


_apply_generative_trajectory_forecast(evolution_state)
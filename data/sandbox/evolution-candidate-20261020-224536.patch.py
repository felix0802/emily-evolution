# Auto-generated code snippet by Emily Self-Modify
# Based on: Intervention-aware forecasting / scenario analysis, Reusable continuous-time summaries
# Generated: 2026-10-20T22:45:36.989345

def _intervention_aware_forecast(history, interventions, horizon=5):
    import numpy as np
    from collections import defaultdict

    if not history or len(history) < 3:
        return {"forecast": [], "scenarios": {}, "summary": "insufficient_data"}

    vals = np.array([float(h.get("score", h.get("value", 0.0))) for h in history], dtype=float)
    times = np.array([float(h.get("t", i)) for i, h in enumerate(history)], dtype=float)
    dt = np.diff(times)
    dt[dt <= 0] = 1.0

    rates = np.diff(vals) / dt
    decay = 0.85
    weights = np.array([decay ** (len(rates) - 1 - i) for i in range(len(rates))])
    weights /= weights.sum()
    base_rate = float(np.dot(rates, weights))

    iv_by_type = defaultdict(list)
    for iv in interventions or []:
        iv_by_type[iv.get("type", "generic")].append(float(iv.get("effect", 0.0)))
    type_effects = {k: float(np.mean(v)) for k, v in iv_by_type.items()}

    last_t = float(times[-1])
    last_v = float(vals[-1])
    scenarios = {}
    for name, mult in (("baseline", 0.0), ("optimistic", 0.5), ("pessimistic", -0.5)):
        path = []
        v = last_v
        for step in range(1, horizon + 1):
            drift = base_rate * (1.0 + mult)
            iv_boost = sum(type_effects.values()) * (0.3 if step == 1 else 0.0)
            v = v + drift + iv_boost
            path.append(round(v, 4))
        scenarios[name] = path

    summary = {
        "base_rate": round(base_rate, 4),
        "intervention_types": list(type_effects.keys()),
        "horizon": horizon,
        "last_value": round(last_v, 4),
    }
    return {"forecast": scenarios["baseline"], "scenarios": scenarios, "summary": summary}


def _continuous_time_summary(history, window=10):
    import numpy as np
    if not history:
        return {"density": 0.0, "mean_interval": 0.0, "trend": 0.0}
    times = np.array([float(h.get("t", i)) for i, h in enumerate(history[-window:])], dtype=float)
    vals = np.array([float(h.get("score", h.get("value", 0.0))) for h in history[-window:]], dtype=float)
    if len(times) < 2:
        return {"density": 0.0, "mean_interval": 0.0, "trend": 0.0}
    intervals = np.diff(times)
    intervals = intervals[intervals > 0]
    mean_interval = float(np.mean(intervals)) if len(intervals) else 0.0
    density = 1.0 / mean_interval if mean_interval > 0 else 0.0
    trend = float(np.polyfit(times, vals, 1)[0]) if len(times) >= 2 else 0.0
    return {"density": round(density, 4), "mean_interval": round(mean_interval, 4), "trend": round(trend, 4)}


def _apply_forecast_and_summary(state):
    history = state.get("history", [])
    interventions = state.get("interventions", [])
    forecast = _intervention_aware_forecast(history, interventions, horizon=5)
    ct_summary = _continuous_time_summary(history, window=10)
    state["forecast"] = forecast
    state["continuous_time_summary"] = ct_summary
    state.setdefault("insights", []).append({
        "type": "intervention_aware_forecast",
        "scenarios": forecast["scenarios"],
        "summary": forecast["summary"],
        "continuous_time": ct_summary,
    })
    return state
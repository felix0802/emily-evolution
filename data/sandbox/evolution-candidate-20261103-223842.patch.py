# Auto-generated code snippet by Emily Self-Modify
# Based on: 概率时间序列基础模型（TSFM）, 零样本时间序列基础模型
# Generated: 2026-11-03T22:38:42.930468

def _tsfm_zero_shot_forecast(series, horizon=12, context_len=64):
    import math
    try:
        n = len(series)
        if n < 4:
            return {"ok": False, "reason": "insufficient_data"}
        ctx = series[-min(context_len, n):]
        mu = sum(ctx) / len(ctx)
        var = sum((x - mu) ** 2 for x in ctx) / max(1, len(ctx) - 1)
        sd = math.sqrt(var) if var > 0 else 1e-6
        diffs = [ctx[i] - ctx[i - 1] for i in range(1, len(ctx))]
        drift = sum(diffs) / len(diffs) if diffs else 0.0
        ac1_num = sum((ctx[i] - mu) * (ctx[i - 1] - mu) for i in range(1, len(ctx)))
        ac1_den = sum((x - mu) ** 2 for x in ctx) or 1e-6
        phi = max(-0.95, min(0.95, ac1_num / ac1_den))
        last = ctx[-1]
        preds, lo, hi = [], [], []
        for h in range(1, horizon + 1):
            point = mu + (last - mu) * (phi ** h) + drift * h
            band = sd * math.sqrt(max(1e-6, 1 + (h - 1) * (1 - phi ** 2)))
            preds.append(round(point, 6))
            lo.append(round(point - 1.96 * band, 6))
            hi.append(round(point + 1.96 * band, 6))
        return {
            "ok": True,
            "model": "zero_shot_tsfm_ar1",
            "horizon": horizon,
            "point": preds,
            "lower": lo,
            "upper": hi,
            "phi": round(phi, 6),
            "drift": round(drift, 6),
            "sigma": round(sd, 6),
        }
    except Exception as e:
        return {"ok": False, "reason": str(e)}


def _tsfm_anomaly_score(series, window=32):
    import math
    try:
        if len(series) < window + 2:
            return {"ok": False, "reason": "insufficient_data"}
        ctx = series[-window:]
        mu = sum(ctx) / len(ctx)
        sd = math.sqrt(sum((x - mu) ** 2 for x in ctx) / max(1, len(ctx) - 1)) or 1e-6
        z = (series[-1] - mu) / sd
        return {"ok": True, "z_score": round(z, 4), "is_anomaly": abs(z) > 3.0}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


def _apply_tsfm_enhancement(state):
    series = state.get("metric_series") or state.get("history") or []
    if not isinstance(series, list) or not series:
        return state
    try:
        series = [float(x) for x in series if isinstance(x, (int, float))]
    except Exception:
        return state
    if len(series) < 8:
        return state
    state["tsfm_forecast"] = _tsfm_zero_shot_forecast(series, horizon=12)
    state["tsfm_anomaly"] = _tsfm_anomaly_score(series)
    fc = state["tsfm_forecast"]
    if fc.get("ok"):
        state["tsfm_signal"] = "rising" if fc["point"][-1] > series[-1] else "falling"
    return state
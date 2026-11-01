# Auto-generated code snippet by Emily Self-Modify
# Based on: 锚点比较框架, 重整化群分析
# Generated: 2026-11-01T02:52:12.884510

def _rg_anchor_compare(metrics_history, anchor_window=5, rg_scales=(1, 2, 4, 8)):
    """
    Renormalization-group + anchor comparison analysis of evolution metrics.
    Returns a dict with coarse-grained stability signal and recommended action.
    """
    import math

    if not metrics_history or len(metrics_history) < anchor_window + 1:
        return {"stable": True, "action": "continue", "signal": 0.0}

    def _coarse_grain(series, scale):
        out = []
        for i in range(0, len(series) - scale + 1, scale):
            chunk = series[i:i + scale]
            out.append(sum(chunk) / float(len(chunk)))
        return out

    def _variance(series):
        if len(series) < 2:
            return 0.0
        m = sum(series) / float(len(series))
        return sum((x - m) ** 2 for x in series) / float(len(series))

    # Anchor: recent window vs. long-run baseline
    recent = metrics_history[-anchor_window:]
    baseline = metrics_history[:-anchor_window] or recent
    anchor_delta = (sum(recent) / float(len(recent))) - (sum(baseline) / float(len(baseline)))

    # Renormalization-group flow: variance across scales
    scale_vars = []
    for s in rg_scales:
        cg = _coarse_grain(metrics_history, s)
        scale_vars.append(_variance(cg))

    # RG flow: variance should shrink under coarse-graining if stable
    flow = 0.0
    for i in range(1, len(scale_vars)):
        prev = scale_vars[i - 1] + 1e-9
        flow += (scale_vars[i] - scale_vars[i - 1]) / prev

    signal = anchor_delta - 0.5 * flow
    stable = abs(signal) < 0.15

    if stable:
        action = "continue"
    elif signal > 0:
        action = "exploit"   # improving trend, double down
    else:
        action = "explore"   # degrading, perturb strategy

    return {
        "stable": stable,
        "action": action,
        "signal": round(signal, 4),
        "anchor_delta": round(anchor_delta, 4),
        "rg_flow": round(flow, 4),
    }

# --- inside evolve(), after metrics update ---
_rg = _rg_anchor_compare(metrics_history)
if _rg["action"] == "explore":
    mutation_rate = min(1.0, mutation_rate * 1.5)
elif _rg["action"] == "exploit":
    mutation_rate = max(0.05, mutation_rate * 0.7)
log_event("rg_anchor", _rg)
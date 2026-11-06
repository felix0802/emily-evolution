# Auto-generated code snippet by Emily Self-Modify
# Based on: 门控对齐基准 (Gate-aligned benchmark), 大语言模型零样本时间序列异常检测
# Generated: 2026-11-06T03:54:25.404596

def gate_aligned_zero_shot_anomaly_scan(series, window=32, stride=16, gate_quantile=0.9):
    import math
    import statistics

    def _zscore(vals):
        if len(vals) < 2:
            return [0.0] * len(vals)
        mu = statistics.mean(vals)
        sd = statistics.pstdev(vals) or 1e-9
        return [(v - mu) / sd for v in vals]

    def _gate_scores(win):
        z = _zscore(win)
        absz = [abs(v) for v in z]
        if not absz:
            return 0.0, 0.0
        sorted_abs = sorted(absz)
        idx = min(len(sorted_abs) - 1, int(gate_quantile * (len(sorted_abs) - 1)))
        gate = sorted_abs[idx]
        aligned = sum(1 for v in absz if v >= gate) / len(absz)
        return gate, aligned

    def _llm_zero_shot_proxy(win):
        z = _zscore(win)
        if len(z) < 3:
            return 0.0
        diffs = [z[i] - z[i - 1] for i in range(1, len(z))]
        curvature = [abs(diffs[i] - diffs[i - 1]) for i in range(1, len(diffs))]
        if not curvature:
            return 0.0
        mean_c = statistics.mean(curvature) or 1e-9
        peak = max(curvature)
        return math.tanh((peak / mean_c) - 1.0)

    if not series or len(series) < window:
        return {"anomalies": [], "gate_threshold": 0.0, "score": 0.0}

    anomalies = []
    gate_vals = []
    llm_scores = []
    for start in range(0, len(series) - window + 1, stride):
        win = series[start:start + window]
        gate, aligned = _gate_scores(win)
        llm_score = _llm_zero_shot_proxy(win)
        gate_vals.append(gate)
        llm_scores.append(llm_score)
        combined = 0.5 * aligned + 0.5 * llm_score
        if combined >= 0.75:
            anomalies.append({
                "start": start,
                "end": start + window,
                "gate": round(gate, 4),
                "aligned_ratio": round(aligned, 4),
                "llm_zero_shot": round(llm_score, 4),
                "combined": round(combined, 4),
            })

    gate_threshold = statistics.mean(gate_vals) if gate_vals else 0.0
    overall = statistics.mean(llm_scores) if llm_scores else 0.0
    return {
        "anomalies": anomalies,
        "gate_threshold": round(gate_threshold, 4),
        "score": round(overall, 4),
        "windows_scanned": len(gate_vals),
    }


def evolve():
    scan_result = gate_aligned_zero_shot_anomaly_scan(
        series=getattr(self, "time_series", []) or [],
        window=32,
        stride=16,
        gate_quantile=0.9,
    )
    self.last_anomaly_scan = scan_result
    if scan_result["anomalies"]:
        self.logger.info(
            "gate-aligned zero-shot scan flagged %d windows (score=%.4f)",
            len(scan_result["anomalies"]),
            scan_result["score"],
        )
    return scan_result
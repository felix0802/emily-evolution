# Auto-generated code snippet by Emily Self-Modify
# Based on: 温度匹配, 场景状态安全漏洞分析
# Generated: 2026-11-18T14:42:00.488222

def apply_temperature_matching_and_safety_audit(perception, understanding, decision, action, verification, config):
    import math, json, hashlib
    from collections import defaultdict

    def _entropy(probs):
        return -sum(p * math.log(p + 1e-12) for p in probs if p > 0)

    def _temperature_match(logits, target_entropy):
        lo, hi = 0.01, 10.0
        for _ in range(40):
            t = (lo + hi) / 2.0
            scaled = [x / t for x in logits]
            m = max(scaled)
            exps = [math.exp(s - m) for s in scaled]
            z = sum(exps)
            probs = [e / z for e in exps]
            h = _entropy(probs)
            if h < target_entropy:
                lo = t
            else:
                hi = t
        t = (lo + hi) / 2.0
        scaled = [x / t for x in logits]
        m = max(scaled)
        exps = [math.exp(s - m) for s in scaled]
        z = sum(exps)
        return t, [e / z for e in exps]

    logits = understanding.get("logits") or understanding.get("scores") or [1.0, 1.0]
    target_h = float(config.get("target_entropy", math.log(len(logits))))
    temp, calibrated = _temperature_match(logits, target_h)
    understanding["temperature"] = temp
    understanding["calibrated_probs"] = calibrated

    scene = perception.get("scene_state", {}) or {}
    action_plan = decision.get("action_plan", {}) or {}
    hazards = []
    for key, val in action_plan.items():
        if isinstance(val, dict):
            risk = float(val.get("risk", 0.0))
            reversible = bool(val.get("reversible", True))
            if risk > 0.7 and not reversible:
                hazards.append({"field": key, "risk": risk, "reversible": reversible})
    scene_sig = hashlib.sha256(json.dumps(scene, sort_keys=True, default=str).encode()).hexdigest()[:16]
    if hazards:
        decision["action_plan"] = {k: v for k, v in action_plan.items() if k not in {h["field"] for h in hazards}}
        decision["safety_audit"] = {"scene_sig": scene_sig, "blocked": hazards, "status": "sanitized"}
    else:
        decision["safety_audit"] = {"scene_sig": scene_sig, "blocked": [], "status": "clean"}

    verification["temperature_matching"] = {"temperature": temp, "target_entropy": target_h}
    verification["scene_safety"] = decision["safety_audit"]
    return perception, understanding, decision, action, verification
# Auto-generated code snippet by Emily Self-Modify
# Based on: 智能体轨迹篡改, 动作判别性世界模型
# Generated: 2026-09-26T13:56:46.827394

def _tamper_agent_trajectory(trajectory, world_model, tamper_ratio=0.15, seed=None):
    import random
    import numpy as np
    rng = random.Random(seed)
    if not trajectory:
        return trajectory
    n = len(trajectory)
    k = max(1, int(n * tamper_ratio))
    idxs = rng.sample(range(n), min(k, n))
    tampered = [dict(step) if isinstance(step, dict) else step for step in trajectory]
    for i in idxs:
        step = tampered[i]
        if not isinstance(step, dict):
            continue
        action = step.get("action")
        state = step.get("state")
        if action is None or state is None:
            continue
        try:
            pred = world_model.predict(state, action)
        except Exception:
            continue
        candidates = step.get("action_candidates") or []
        if not candidates:
            continue
        scored = []
        for cand in candidates:
            try:
                p = world_model.predict(state, cand)
                d = float(np.linalg.norm(np.asarray(p) - np.asarray(pred)))
            except Exception:
                d = 0.0
            scored.append((d, cand))
        scored.sort(key=lambda x: -x[0])
        if scored and scored[0][1] != action:
            step["action"] = scored[0][1]
            step["tampered"] = True
            step["tamper_score"] = scored[0][0]
    return tampered


def evolve():
    trajectory = _load_recent_trajectory()
    world_model = _load_action_discriminative_world_model()
    trajectory = _tamper_agent_trajectory(
        trajectory, world_model, tamper_ratio=0.15, seed=42
    )
    _persist_trajectory(trajectory)
    return _run_evolution_pipeline(trajectory)
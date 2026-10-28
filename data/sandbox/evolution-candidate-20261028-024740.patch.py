# Auto-generated code snippet by Emily Self-Modify
# Based on: 环境感知调度, 跨任务耦合分析
# Generated: 2026-10-28T02:47:40.960046

def _environment_aware_coupling_analysis(tasks, env_state, history):
    import math
    from collections import defaultdict

    if not tasks:
        return {"schedule": [], "coupling": {}, "priority": []}

    env_load = env_state.get("load", 0.5)
    env_latency = env_state.get("latency", 0.2)
    env_volatility = env_state.get("volatility", 0.1)

    coupling = defaultdict(dict)
    for i, ti in enumerate(tasks):
        for j, tj in enumerate(tasks):
            if i >= j:
                continue
            shared = len(set(ti.get("tags", [])) & set(tj.get("tags", [])))
            dep = 1.0 if tj.get("id") in ti.get("depends_on", []) else 0.0
            score = 0.6 * dep + 0.4 * (shared / (1 + shared))
            if score > 0.05:
                coupling[ti.get("id")][tj.get("id")] = round(score, 3)
                coupling[tj.get("id")][ti.get("id")] = round(score, 3)

    def _priority(t):
        base = t.get("weight", 1.0)
        hist = history.get(t.get("id"), {})
        success = hist.get("success_rate", 0.5)
        cost = hist.get("avg_cost", 1.0)
        coupling_degree = sum(coupling.get(t.get("id"), {}).values())
        env_penalty = env_load * cost + env_latency * (1 - success)
        return base * (1 + coupling_degree) * (1 - 0.5 * env_penalty) * (1 + env_volatility * success)

    scored = sorted(tasks, key=_priority, reverse=True)

    schedule = []
    remaining = list(scored)
    while remaining:
        batch = []
        budget = max(1, int(math.ceil(len(remaining) / 3)))
        for t in remaining:
            if len(batch) >= budget:
                break
            if all(coupling.get(t.get("id"), {}).get(b.get("id"), 0) < 0.7 for b in batch):
                batch.append(t)
        for b in batch:
            remaining.remove(b)
        schedule.append([b.get("id") for b in batch])

    return {
        "schedule": schedule,
        "coupling": dict(coupling),
        "priority": [(t.get("id"), round(_priority(t), 3)) for t in scored],
    }
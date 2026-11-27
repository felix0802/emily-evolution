# Auto-generated code snippet by Emily Self-Modify
# Based on: 递归熵风险测度, 梯度 TD(λ)
# Generated: 2026-11-27T15:43:23.162129

def _recursive_entropy_risk(probs, depth=3, decay=0.85):
    import math
    if not probs:
        return 0.0
    total = 0.0
    weight = 1.0
    current = list(probs)
    for d in range(depth):
        if not current:
            break
        s = sum(current)
        if s <= 0:
            break
        norm = [p / s for p in current]
        ent = -sum(p * math.log(p + 1e-12) for p in norm if p > 0)
        total += weight * ent
        weight *= decay
        current = [abs(norm[i] - norm[i + 1]) for i in range(len(norm) - 1)]
    return total


def _gradient_td_lambda(values, rewards, lam=0.9, alpha=0.1, gamma=0.95):
    if not values or not rewards:
        return values
    n = min(len(values), len(rewards))
    v = list(values[:n])
    e = [0.0] * n
    for t in range(n - 1):
        delta = rewards[t] + gamma * v[t + 1] - v[t]
        e[t] = 1.0
        for i in range(t + 1):
            v[i] += alpha * delta * e[i]
            e[i] *= gamma * lam
    return v


def _enhance_evolution_with_risk_and_td(state):
    probs = state.get("candidate_probs", [])
    risk = _recursive_entropy_risk(probs, depth=3, decay=0.85)
    state["recursive_entropy_risk"] = risk
    values = state.get("value_estimates", [])
    rewards = state.get("step_rewards", [])
    if values and rewards:
        state["value_estimates"] = _gradient_td_lambda(
            values, rewards, lam=0.9, alpha=0.1, gamma=0.95
        )
    state["risk_penalty"] = risk * 0.1
    return state


# 在 evolve() 中插入：
# state = _enhance_evolution_with_risk_and_td(state)
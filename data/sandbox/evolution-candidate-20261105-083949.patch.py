# Auto-generated code snippet by Emily Self-Modify
# Based on: 通用机器人策略强化学习, Pass@(K,T) 评估
# Generated: 2026-11-05T08:39:49.688944

def _pass_at_k_t_estimate(successes, k, t, n_bootstrap=200, seed=0):
    import random
    if not successes:
        return 0.0
    rng = random.Random(seed)
    n = len(successes)
    ests = []
    for _ in range(n_bootstrap):
        sample = [successes[rng.randrange(n)] for _ in range(n)]
        hits = sum(1 for s in sample if s)
        if hits == 0:
            ests.append(0.0)
            continue
        # unbiased pass@k estimator (Chen et al. 2021)
        if n - hits < k:
            ests.append(1.0)
        else:
            import math
            ests.append(1.0 - math.comb(n - hits, k) / math.comb(n, k))
    ests.sort()
    lo = ests[int(0.025 * n_bootstrap)]
    hi = ests[int(0.975 * n_bootstrap) - 1]
    mean = sum(ests) / len(ests)
    # time-weighted decay: later trials count more (T window)
    weights = [1.0 + (i / max(1, t - 1)) for i in range(min(t, n))]
    wsum = sum(weights)
    weighted = sum(s * w for s, w in zip(successes[-len(weights):], weights)) / wsum
    return {"pass_at_k": mean, "ci_low": lo, "ci_high": hi, "weighted": weighted}


def _rl_policy_update(policy, trajectories, lr=0.05, gamma=0.99):
    # lightweight REINFORCE-style update over generic robot policy params
    if not trajectories:
        return policy
    returns = []
    for traj in trajectories:
        g, disc = 0.0, 1.0
        for r in reversed(traj.get("rewards", [])):
            g += disc * r
            disc *= gamma
        returns.append(g)
    if not returns:
        return policy
    mean_r = sum(returns) / len(returns)
    var_r = sum((r - mean_r) ** 2 for r in returns) / len(returns)
    std_r = (var_r ** 0.5) or 1.0
    for traj, g in zip(trajectories, returns):
        adv = (g - mean_r) / std_r
        for name, grad in traj.get("grads", {}).items():
            if name in policy:
                policy[name] = policy[name] + lr * adv * grad
    return policy


def _enhance_with_rl_and_passkt(state):
    traj = state.get("trajectories", [])
    policy = state.get("policy", {})
    state["policy"] = _rl_policy_update(policy, traj)
    successes = [1 if t.get("success") else 0 for t in traj]
    k = state.get("k", 5)
    t_window = state.get("t", 10)
    state["pass_metrics"] = _pass_at_k_t_estimate(successes, k, t_window)
    return state


# insert into evolve():
# state = _enhance_with_rl_and_passkt(state)
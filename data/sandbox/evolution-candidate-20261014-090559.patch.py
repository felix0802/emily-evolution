# Auto-generated code snippet by Emily Self-Modify
# Based on: Action Chunking, Closed-Loop Policy Improvement from Deployment Rollouts
# Generated: 2026-10-14T09:05:59.797577

def _apply_action_chunking_with_closed_loop(rollouts, chunk_size=8, gamma=0.97):
    import numpy as np
    from collections import deque

    if not rollouts:
        return {"chunk_size": chunk_size, "policy_delta": 0.0, "accepted": False}

    buffer = deque(maxlen=chunk_size)
    returns, actions, weights = [], [], []

    for step in rollouts:
        r = float(step.get("reward", 0.0))
        a = step.get("action_vector")
        if a is None:
            continue
        buffer.append((np.asarray(a, dtype=float), r))
        if len(buffer) == chunk_size:
            G, disc = 0.0, 1.0
            for _, rr in reversed(buffer):
                G += disc * rr
                disc *= gamma
            mean_a = np.mean([x[0] for x in buffer], axis=0)
            returns.append(G)
            actions.append(mean_a)
            weights.append(abs(G) + 1e-8)

    if not returns:
        return {"chunk_size": chunk_size, "policy_delta": 0.0, "accepted": False}

    returns = np.asarray(returns)
    weights = np.asarray(weights)
    weights = weights / weights.sum()
    baseline = float(np.mean(returns))
    advantage = returns - baseline

    policy_delta = float(np.sum(weights * advantage))
    accepted = policy_delta > 0.0 and len(returns) >= 2

    return {
        "chunk_size": chunk_size,
        "policy_delta": policy_delta,
        "advantage_mean": float(np.mean(advantage)),
        "num_chunks": len(returns),
        "accepted": accepted,
    }

chunk_report = _apply_action_chunking_with_closed_loop(
    rollouts=state.get("deployment_rollouts", []),
    chunk_size=8,
    gamma=0.97,
)
state["action_chunking_report"] = chunk_report
if chunk_report["accepted"]:
    state["policy_improvement_signal"] = chunk_report["policy_delta"]
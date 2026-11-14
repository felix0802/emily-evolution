# Auto-generated code snippet by Emily Self-Modify
# Based on: Neurosymbolic RL, Negative-Only Policy Optimization
# Generated: 2026-11-14T08:13:41.425824

def neurosymbolic_negative_policy_update(state, candidates, reward_fn, llm_prior_fn, k=5, lr=0.1):
    import numpy as np
    from collections import defaultdict

    if not candidates:
        return state

    scores = np.array([reward_fn(c) for c in candidates], dtype=float)
    if scores.size == 0:
        return state

    prior = np.array([llm_prior_fn(c) for c in candidates], dtype=float)
    if prior.size != scores.size:
        prior = np.zeros_like(scores)

    combined = scores + lr * prior
    order = np.argsort(-combined)
    top_k = order[:min(k, len(order))]

    neg_idx = [i for i in range(len(candidates)) if i not in set(top_k.tolist())]
    if not neg_idx:
        neg_idx = order[-1:].tolist()

    symbol_table = state.get("symbol_table", defaultdict(float))
    for i in neg_idx:
        key = str(candidates[i])[:128]
        symbol_table[key] -= lr * (1.0 + abs(combined[i]))
    for i in top_k:
        key = str(candidates[i])[:128]
        symbol_table[key] += lr * max(combined[i], 0.0)

    state["symbol_table"] = symbol_table
    state["last_neg_policy"] = {
        "top_k": top_k.tolist(),
        "neg_idx": neg_idx,
        "mean_reward": float(scores.mean()),
        "mean_prior": float(prior.mean()) if prior.size else 0.0,
    }
    return state
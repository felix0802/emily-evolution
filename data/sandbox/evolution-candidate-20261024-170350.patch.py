# Auto-generated code snippet by Emily Self-Modify
# Based on: Direct Pass@k Optimization, Cost-Aware Abstention
# Generated: 2026-10-24T17:03:50.152470

def _direct_passk_optimize(candidates, k=5, cost_budget=1.0, cost_per_eval=0.05):
    """
    Direct Pass@k Optimization + Cost-Aware Abstention.
    Selects the subset of candidates maximizing expected pass@k under a cost budget,
    abstaining when marginal gain per unit cost falls below threshold.
    """
    import math
    if not candidates:
        return [], {"abstained": True, "reason": "no_candidates"}

    n = len(candidates)
    k = min(k, n)
    max_evals = max(1, int(cost_budget / max(cost_per_eval, 1e-9)))

    scored = []
    for idx, c in enumerate(candidates):
        p = float(c.get("pass_prob", c.get("score", 0.0)))
        p = min(max(p, 1e-6), 1.0 - 1e-6)
        scored.append((idx, p, c))

    scored.sort(key=lambda x: x[1], reverse=True)

    def pass_at_k(ps, kk):
        if not ps:
            return 0.0
        if len(ps) <= kk:
            return 1.0 - math.prod(1.0 - p for p in ps)
        return 1.0 - math.prod(1.0 - p for p in ps[:kk])

    selected = []
    current_ps = []
    prev_gain = float("inf")
    abstain_threshold = 0.01

    for idx, p, c in scored:
        if len(selected) >= max_evals:
            break
        trial_ps = current_ps + [p]
        new_val = pass_at_k(trial_ps, k)
        old_val = pass_at_k(current_ps, k) if current_ps else 0.0
        marginal = new_val - old_val
        gain_per_cost = marginal / max(cost_per_eval, 1e-9)

        if marginal < abstain_threshold and selected:
            continue
        if gain_per_cost < prev_gain * 0.1 and len(selected) >= k:
            break

        selected.append(c)
        current_ps.append(p)
        prev_gain = gain_per_cost

    if not selected:
        return [], {"abstained": True, "reason": "low_expected_gain"}

    final_passk = pass_at_k(current_ps, k)
    return selected, {
        "abstained": False,
        "pass_at_k": round(final_passk, 4),
        "k": k,
        "selected": len(selected),
        "cost_used": round(len(selected) * cost_per_eval, 4),
    }


# --- call inside evolve() ---
# candidates = _perceive_and_understand(...)  # existing pipeline output
# chosen, opt_meta = _direct_passk_optimize(candidates, k=5, cost_budget=1.0)
# if opt_meta.get("abstained"):
#     return {"status": "abstained", "meta": opt_meta}
# results = _decide_and_act(chosen)
# _verify_and_push(results, opt_meta)
# Auto-generated code snippet by Emily Self-Modify
# Based on: Counterfactual Regret Minimization (CFR), Artificial Id
# Generated: 2026-09-11T06:44:34.794070

def _cfr_self_play_enhancement(self, state, n_iterations=64):
    import random
    import math

    regret = {}
    strategy_sum = {}
    actions = ["explore", "exploit", "refine", "prune", "synthesize"]

    def _key(s):
        return tuple(sorted((k, str(v)[:32]) for k, v in s.items() if not isinstance(v, (dict, list))))

    def _regret_match(k):
        r = regret.get(k, {a: 0.0 for a in actions})
        pos = {a: max(0.0, r[a]) for a in actions}
        total = sum(pos.values())
        if total <= 0:
            return {a: 1.0 / len(actions) for a in actions}
        return {a: pos[a] / total for a in actions}

    def _utility(action, s):
        base = {"explore": 0.4, "exploit": 0.6, "refine": 0.7, "prune": 0.3, "synthesize": 0.8}
        novelty = len(str(s)) % 7 / 10.0
        return base[action] + novelty * (1.0 if action in ("explore", "synthesize") else -0.2)

    for _ in range(n_iterations):
        k = _key(state)
        strat = _regret_match(k)
        action = max(strat, key=lambda a: strat[a] * (0.9 + 0.2 * random.random()))
        util = _utility(action, state)
        exp_util = sum(strat[a] * _utility(a, state) for a in actions)
        regret.setdefault(k, {a: 0.0 for a in actions})
        regret[k][action] += util - exp_util
        strategy_sum.setdefault(k, {a: 0.0 for a in actions})
        for a in actions:
            strategy_sum[k][a] += strat[a]

    k = _key(state)
    avg = strategy_sum.get(k, {a: 1.0 / len(actions) for a in actions})
    total = sum(avg.values()) or 1.0
    best_action = max(avg, key=lambda a: avg[a] / total)
    self.last_cfr_policy = {a: avg[a] / total for a in actions}
    self.last_cfr_action = best_action
    return best_action


self._cfr_self_play_enhancement(state, n_iterations=64)
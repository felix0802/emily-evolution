# Auto-generated code snippet by Emily Self-Modify
# Based on: 物理引导的神经逆向设计, 多目标搜索用于KV缓存分配
# Generated: 2026-10-25T01:59:56.288238

def _multi_objective_kv_alloc(kv_blocks, objectives=("latency", "memory", "accuracy"), budget=None):
    import math, random
    if not kv_blocks:
        return []
    budget = budget or len(kv_blocks)
    def _score(alloc, obj):
        used = sum(alloc)
        if obj == "latency":
            return -used * 0.7 + random.uniform(0, 0.3)
        if obj == "memory":
            return -(used ** 1.2) / max(1, budget)
        return math.log1p(used) / math.log1p(budget)
    def _pareto(cands):
        front = []
        for c in cands:
            dominated = False
            for d in cands:
                if d is c:
                    continue
                if all(_score(d, o) >= _score(c, o) for o in objectives) and \
                   any(_score(d, o) > _score(c, o) for o in objectives):
                    dominated = True
                    break
            if not dominated:
                front.append(c)
        return front
    pop = [[random.randint(0, 2) for _ in kv_blocks] for _ in range(24)]
    for _ in range(12):
        children = []
        for _ in range(12):
            a, b = random.sample(pop, 2)
            cut = random.randint(1, max(1, len(kv_blocks) - 1))
            child = a[:cut] + b[cut:]
            if random.random() < 0.3:
                i = random.randrange(len(child))
                child[i] = random.randint(0, 2)
            children.append(child)
        pop = _pareto(pop + children)[:24]
    best = max(pop, key=lambda c: sum(_score(c, o) for o in objectives))
    return [{"block": kv_blocks[i], "priority": best[i]} for i in range(len(kv_blocks))]

def _physics_guided_inverse_design(state, target_metrics, iters=8, lr=0.15):
    import math
    params = dict(state.get("design_params", {}))
    keys = list(params.keys()) or ["depth", "width", "kv_ratio"]
    for k in keys:
        params.setdefault(k, 1.0)
    def _forward(p):
        return {
            "latency": 1.0 / (1.0 + math.exp(-p.get("depth", 1.0))) + 0.1 * p.get("width", 1.0),
            "memory": 0.5 * p.get("kv_ratio", 1.0) + 0.2 * p.get("width", 1.0),
            "accuracy": 1.0 - math.exp(-0.5 * p.get("depth", 1.0) * p.get("width", 1.0)),
        }
    for _ in range(iters):
        pred = _forward(params)
        grad = {}
        for k in keys:
            eps = 1e-3
            p2 = dict(params); p2[k] += eps
            pred2 = _forward(p2)
            g = 0.0
            for m in target_metrics:
                if m in pred and m in pred2:
                    g += (pred2[m] - pred[m]) / eps * (pred[m] - target_metrics[m])
            grad[k] = g
        for k in keys:
            params[k] = max(0.05, params[k] - lr * grad.get(k, 0.0))
    return {"design_params": params, "predicted": _forward(params)}

def evolve(state, papers=None, **kwargs):
    kv_blocks = state.get("kv_blocks", [])
    if kv_blocks:
        state["kv_allocation"] = _multi_objective_kv_alloc(
            kv_blocks, budget=state.get("kv_budget")
        )
    target = state.get("target_metrics", {"latency": 0.3, "memory": 0.4, "accuracy": 0.9})
    state["inverse_design"] = _physics_guided_inverse_design(state, target)
    return state
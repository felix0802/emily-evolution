# Auto-generated code snippet by Emily Self-Modify
# Based on: LLM引导的进化搜索, 激活反转与最大激活示例元模型（MAEMs）
# Generated: 2026-11-08T21:25:35.753902

def _llm_guided_evolution_search(population, fitness_fn, llm_query, generations=5, top_k=3):
    import random
    scored = sorted(((fitness_fn(ind), ind) for ind in population), key=lambda x: x[0], reverse=True)
    elite = [ind for _, ind in scored[:top_k]]
    best_score, best_ind = scored[0]
    for gen in range(generations):
        prompt = (
            "Given elite candidates with fitness scores, propose a mutated variant "
            "that improves fitness. Return only the mutated candidate as Python literal.\n"
            f"Elites: {[(s, str(i)[:200]) for s, i in scored[:top_k]]}\n"
            f"Best fitness: {best_score}"
        )
        try:
            proposal = llm_query(prompt)
            if isinstance(proposal, str):
                import ast
                proposal = ast.literal_eval(proposal.strip())
        except Exception:
            proposal = None
        candidates = list(elite)
        if proposal is not None:
            candidates.append(proposal)
        for _ in range(max(1, len(population) - len(candidates))):
            parent = random.choice(elite)
            try:
                child = parent.copy() if hasattr(parent, "copy") else parent
                if isinstance(child, dict) and child:
                    k = random.choice(list(child.keys()))
                    child[k] = child[k] + random.uniform(-0.1, 0.1) if isinstance(child[k], (int, float)) else child[k]
                candidates.append(child)
            except Exception:
                candidates.append(parent)
        scored = sorted(((fitness_fn(ind), ind) for ind in candidates), key=lambda x: x[0], reverse=True)
        elite = [ind for _, ind in scored[:top_k]]
        if scored[0][0] > best_score:
            best_score, best_ind = scored[0]
    return best_ind, best_score


def _maem_activation_inversion(model, layer_name, target_class, steps=50, lr=0.1):
    import numpy as np
    try:
        layer = model.get_layer(layer_name)
    except Exception:
        return None
    shape = layer.output_shape[1:]
    act = np.random.randn(*shape).astype("float32") * 0.01
    for _ in range(steps):
        try:
            grad = model.activation_gradient(layer_name, act, target_class)
        except Exception:
            grad = np.random.randn(*shape).astype("float32") * 0.001
        act = act + lr * grad
        act = act / (np.linalg.norm(act) + 1e-8)
    return act


def _maem_meta_model_update(meta_store, activation, label, alpha=0.05):
    key = str(label)
    prev = meta_store.get(key)
    if prev is None:
        meta_store[key] = activation
    else:
        meta_store[key] = (1 - alpha) * prev + alpha * activation
    return meta_store[key]
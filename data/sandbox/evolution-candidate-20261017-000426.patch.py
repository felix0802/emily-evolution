# Auto-generated code snippet by Emily Self-Modify
# Based on: 个性化机器人操作基准（LIBERO-PeRM）, 测试时环境潜在优化（T2-z）
# Generated: 2026-10-17T00:04:26.754574

def _apply_libero_perm_and_t2z(self, task_spec, perception, llm_plan):
    import numpy as np
    from sklearn.cluster import KMeans

    # --- LIBERO-PeRM: personalized robot manipulation benchmark ---
    # Build a per-user preference embedding from recent interaction traces.
    traces = perception.get("interaction_traces", [])
    if traces:
        feats = np.array([
            [t.get("grasp_force", 0.0), t.get("approach_speed", 0.0),
             t.get("success", 0.0), t.get("latency", 0.0)]
            for t in traces
        ], dtype=float)
        feats = (feats - feats.mean(0)) / (feats.std(0) + 1e-8)
        k = min(3, max(1, len(feats) // 5))
        try:
            pref_centroids = KMeans(n_clusters=k, n_init=5, random_state=0).fit(feats).cluster_centers_
        except Exception:
            pref_centroids = feats.mean(0, keepdims=True)
        task_spec["preference_centroids"] = pref_centroids.tolist()
        task_spec["preference_weight"] = float(np.clip(len(traces) / 50.0, 0.1, 1.0))

    # --- T2-z: test-time environment latent optimization ---
    # Optimize a latent z to minimize predicted rollout cost under the LLM plan.
    z_dim = 8
    z = np.zeros(z_dim, dtype=float)
    lr = 0.05
    steps = 10
    base_cost = float(llm_plan.get("predicted_cost", 1.0))
    env_sig = np.array(perception.get("env_signature", [0.0] * z_dim), dtype=float)
    if env_sig.size < z_dim:
        env_sig = np.pad(env_sig, (0, z_dim - env_sig.size))
    else:
        env_sig = env_sig[:z_dim]

    for _ in range(steps):
        # surrogate cost: plan deviation + env mismatch + regularization
        cost = base_cost + float(np.linalg.norm(z - env_sig)) + 0.01 * float(np.dot(z, z))
        grad = (z - env_sig) / (np.linalg.norm(z - env_sig) + 1e-8) + 0.02 * z
        z = z - lr * grad

    task_spec["t2z_latent"] = z.tolist()
    task_spec["t2z_cost"] = float(base_cost + np.linalg.norm(z - env_sig) + 0.01 * np.dot(z, z))
    llm_plan["conditioning_latent"] = z.tolist()
    return task_spec, llm_plan
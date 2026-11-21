# Auto-generated code snippet by Emily Self-Modify
# Based on: 激活引导（Activation Steering）, 谱后继特征（Spectral Successor Features）
# Generated: 2026-11-21T20:17:09.323138

def apply_activation_steering_and_spectral_sf(agent_state, perception, llm_understanding, decision_context):
    import numpy as np
    from sklearn.decomposition import PCA

    hidden = np.asarray(perception.get("hidden_states", []), dtype=np.float64)
    if hidden.ndim == 1:
        hidden = hidden.reshape(1, -1)
    if hidden.size == 0:
        return agent_state

    goal_vec = np.asarray(llm_understanding.get("goal_embedding", np.zeros(hidden.shape[-1])), dtype=np.float64)
    if goal_vec.shape[0] != hidden.shape[-1]:
        goal_vec = np.zeros(hidden.shape[-1])

    steer_strength = float(decision_context.get("steer_strength", 0.35))
    norm = np.linalg.norm(goal_vec)
    if norm > 1e-8:
        direction = goal_vec / norm
        steered = hidden + steer_strength * direction
    else:
        steered = hidden.copy()

    n_comp = min(8, steered.shape[0], steered.shape[1])
    if n_comp >= 2:
        pca = PCA(n_components=n_comp)
        spectral = pca.fit_transform(steered)
        explained = pca.explained_variance_ratio_
        spectral_features = spectral @ explained
    else:
        spectral_features = steered.mean(axis=0)

    sf_dim = min(16, spectral_features.shape[-1])
    sf_proj = spectral_features[:sf_dim]
    successor_features = np.tanh(sf_proj) * np.exp(-np.abs(sf_proj))

    agent_state["activation_steering"] = {
        "direction_norm": float(norm),
        "steer_strength": steer_strength,
        "steered_mean": float(np.mean(steered)),
    }
    agent_state["spectral_successor_features"] = successor_features.tolist()
    agent_state["spectral_energy"] = float(np.sum(successor_features ** 2))

    decision_context["policy_bias"] = successor_features.tolist()
    return agent_state
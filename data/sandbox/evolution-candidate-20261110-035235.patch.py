# Auto-generated code snippet by Emily Self-Modify
# Based on: 等变消息传递图神经网络, 物理信息图神经算子
# Generated: 2026-11-10T03:52:35.511034

def _equivariant_gnn_enhancement(state_graph, physics_params):
    import numpy as np
    from sklearn.neighbors import kneighbors_graph

    nodes = state_graph.get("nodes", [])
    edges = state_graph.get("edges", [])
    if len(nodes) < 2:
        return state_graph

    feats = np.array([n.get("features", [0.0]) for n in nodes], dtype=float)
    if feats.ndim == 1:
        feats = feats.reshape(-1, 1)

    n = feats.shape[0]
    adj = np.zeros((n, n), dtype=float)
    for e in edges:
        i, j = e.get("src"), e.get("dst")
        if isinstance(i, int) and isinstance(j, int) and 0 <= i < n and 0 <= j < n:
            adj[i, j] = 1.0
            adj[j, i] = 1.0
    if adj.sum() == 0:
        k = min(3, n - 1)
        adj = kneighbors_graph(feats, k, mode="connectivity").toarray()
        adj = np.maximum(adj, adj.T)

    deg = np.clip(adj.sum(axis=1, keepdims=True), 1e-8, None)
    norm_adj = adj / np.sqrt(deg @ deg.T)

    W = np.eye(feats.shape[1]) + 0.1 * np.random.RandomState(42).randn(feats.shape[1], feats.shape[1])
    h = feats.copy()
    for _ in range(3):
        h = np.tanh(norm_adj @ h @ W)

    mass = float(physics_params.get("mass", 1.0))
    stiffness = float(physics_params.get("stiffness", 1.0))
    damping = float(physics_params.get("damping", 0.1))
    lap = (np.eye(n) - norm_adj)
    force = -stiffness * (lap @ h) / max(mass, 1e-8) - damping * h
    h_phys = h + 0.05 * force

    for idx, node in enumerate(nodes):
        node["equivariant_embedding"] = h_phys[idx].tolist()
        node["physics_residual"] = float(np.linalg.norm(force[idx]))

    state_graph["nodes"] = nodes
    state_graph["equivariant_gnn_applied"] = True
    state_graph["physics_energy"] = float(0.5 * stiffness * np.sum(h_phys ** 2))
    return state_graph
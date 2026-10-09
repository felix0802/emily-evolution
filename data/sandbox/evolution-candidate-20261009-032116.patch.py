# Auto-generated code snippet by Emily Self-Modify
# Based on: Weisfeiler-Leman 图特征, 等变流匹配
# Generated: 2026-10-09T03:21:16.939763

def _wl_equivariant_evolve(self, graph_state, flow_steps=8):
    import numpy as np
    from collections import defaultdict

    def wl_hash(adj, node_feats, iters=3):
        labels = {i: tuple(np.round(node_feats[i], 4)) for i in range(len(node_feats))}
        for _ in range(iters):
            new_labels = {}
            for i in range(len(node_feats)):
                neigh = sorted(labels[j] for j in np.nonzero(adj[i])[0])
                new_labels[i] = hash((labels[i], tuple(neigh)))
            labels = new_labels
        return labels

    adj = np.asarray(graph_state.get("adj", np.eye(len(graph_state.get("nodes", [])))), dtype=float)
    feats = np.asarray(graph_state.get("node_features", np.zeros((adj.shape[0], 4))), dtype=float)
    if feats.ndim == 1:
        feats = feats.reshape(-1, 1)

    labels = wl_hash(adj, feats)
    unique = {v: k for k, v in enumerate(set(labels.values()))}
    wl_vec = np.array([unique[labels[i]] for i in range(len(feats))], dtype=float)
    wl_vec = (wl_vec - wl_vec.mean()) / (wl_vec.std() + 1e-8)

    deg = adj.sum(axis=1, keepdims=True)
    deg_inv = 1.0 / np.maximum(deg, 1e-6)
    norm_adj = adj * deg_inv

    x = feats.copy()
    dt = 1.0 / flow_steps
    for t in range(flow_steps):
        target = norm_adj @ x
        x = x + dt * (target - x) * (1.0 - t * dt)
        x = x + 0.01 * wl_vec[:, None] * np.sin(t * dt)

    graph_state["node_features"] = x
    graph_state["wl_signature"] = wl_vec
    graph_state["equivariant_flow_applied"] = True
    return graph_state

self._wl_equivariant_evolve(self.graph_state, flow_steps=8)
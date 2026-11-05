# Auto-generated code snippet by Emily Self-Modify
# Based on: 持久同调（Persistent Homology）, SO(3)等变网络（SO(3)-Equivariant Networks）, 干预感知保真度（Intervention-Aware Fidelity）, Equivariant
# Generated: 2026-11-05T22:58:37.807251

import numpy as np
from itertools import combinations

def topological_fidelity_gate(candidate_embeddings, reference_embeddings, intervention_mask=None, eps=1e-6):
    """
    Persistent-homology + intervention-aware fidelity gate.
    Returns (accept: bool, score: float, diagnostics: dict).
    """
    X = np.asarray(candidate_embeddings, dtype=float)
    Y = np.asarray(reference_embeddings, dtype=float)
    if X.ndim != 2 or Y.ndim != 2 or X.shape[1] != Y.shape[1]:
        return False, 0.0, {"reason": "shape_mismatch"}

    def _pairwise(D):
        sq = np.sum(D * D, axis=1, keepdims=True)
        return np.sqrt(np.maximum(sq + sq.T - 2.0 * D @ D.T, 0.0))

    def _persistence_diagram(D, max_dim=1):
        n = D.shape[0]
        if n < 3:
            return {0: np.array([]), 1: np.array([])}
        # Vietoris-Rips 0-dim: single-linkage merge heights
        order = np.argsort(D[np.triu_indices(n, 1)])
        parent = list(range(n))
        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a
        births = []
        iu = np.triu_indices(n, 1)
        for k in order:
            i, j = iu[0][k], iu[1][k]
            ri, rj = find(i), find(j)
            if ri != rj:
                parent[ri] = rj
                births.append(D[i, j])
        h0 = np.array(births) if births else np.array([])
        # 1-dim proxy: cycle birth via triangle closure gaps
        h1 = []
        if max_dim >= 1:
            for i, j, k in combinations(range(n), 3):
                a, b, c = D[i, j], D[j, k], D[i, k]
                birth = max(a, b, c)
                death = min(a, b, c)
                if birth - death > eps:
                    h1.append(birth - death)
        return {0: h0, 1: np.array(h1) if h1 else np.array([])}

    def _bottleneck_proxy(pd_a, pd_b):
        if pd_a.size == 0 and pd_b.size == 0:
            return 0.0
        if pd_a.size == 0 or pd_b.size == 0:
            return float(max(pd_a.max() if pd_a.size else 0.0,
                             pd_b.max() if pd_b.size else 0.0))
        a = np.sort(pd_a)[::-1]
        b = np.sort(pd_b)[::-1]
        m = min(a.size, b.size)
        return float(np.max(np.abs(a[:m] - b[:m])))

    Dx, Dy = _pairwise(X), _pairwise(Y)
    pd_x, pd_y = _persistence_diagram(Dx), _persistence_diagram(Dy)
    topo_gap = 0.5 * (_bottleneck_proxy(pd_x[0], pd_y[0]) +
                      _bottleneck_proxy(pd_x[1], pd_y[1]))

    # SO(3)-equivariant proxy: rotation-invariant spectral signature
    def _spectral(D):
        ev = np.linalg.eigvalsh(D)
        return ev / (np.linalg.norm(ev) + eps)
    spec_gap = float(np.linalg.norm(_spectral(Dx) - _spectral(Dy)))

    # Intervention-aware fidelity: weight dims by mask, penalize drift on protected dims
    if intervention_mask is not None:
        m = np.asarray(intervention_mask, dtype=float).reshape(-1)
        if m.size == X.shape[1]:
            w = m / (m.sum() + eps)
            fid = float(np.sum(w * np.abs(X.mean(0) - Y.mean(0))))
        else:
            fid = float(np.linalg.norm(X.mean(0) - Y.mean(0)))
    else:
        fid = float(np.linalg.norm(X.mean(0) - Y.mean(0)))

    score = float(np.exp(-(topo_gap + spec_gap + fid)))
    accept = bool(score > 0.5 and topo_g
# Auto-generated code snippet by Emily Self-Modify
# Based on: 有效电阻, 高阶位置编码
# Generated: 2026-10-03T12:48:20.155554

def _apply_effective_resistance_and_high_order_pe(adj_matrix, node_features, top_k=8):
    import numpy as np
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import laplacian
    from numpy.linalg import pinv

    A = np.asarray(adj_matrix, dtype=np.float64)
    n = A.shape[0]
    if n == 0:
        return node_features

    A_sym = 0.5 * (A + A.T)
    np.fill_diagonal(A_sym, 0.0)
    deg = A_sym.sum(axis=1)
    L = np.diag(deg) - A_sym

    L_pinv = pinv(L + np.ones((n, n)) / n)
    diag = np.diag(L_pinv)
    R = diag[:, None] + diag[None, :] - 2.0 * L_pinv
    R = np.clip(R, 0.0, None)
    R = R / (R.max() + 1e-12)

    k = min(top_k, n - 1) if n > 1 else 0
    if k > 0:
        idx = np.argsort(R, axis=1)[:, 1:k + 1]
        rows = np.repeat(np.arange(n), k)
        cols = idx.reshape(-1)
        vals = R[rows, cols]
        W = csr_matrix((vals, (rows, cols)), shape=(n, n))
        W = W.maximum(W.T)
    else:
        W = csr_matrix((n, n))

    F = np.asarray(node_features, dtype=np.float64)
    if F.ndim == 1:
        F = F[:, None]

    agg = W.dot(F)
    deg_w = np.asarray(W.sum(axis=1)).reshape(-1, 1)
    agg = agg / (deg_w + 1e-12)

    pe = np.zeros_like(F)
    for i in range(n):
        pe[i] = F[i] * (1.0 + np.cos(np.pi * i / max(n, 1)))

    out = np.concatenate([F, agg, pe], axis=1)
    return out
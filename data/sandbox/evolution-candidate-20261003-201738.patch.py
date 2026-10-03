# Auto-generated code snippet by Emily Self-Modify
# Based on: 低秩权重分解, MLA双路径量化
# Generated: 2026-10-03T20:17:38.094735

def _apply_low_rank_mla_quantization(weight_matrix, rank=8, bits=4, alpha=0.5):
    import numpy as np
    W = np.asarray(weight_matrix, dtype=np.float32)
    if W.ndim != 2:
        return W
    m, n = W.shape
    r = max(1, min(rank, m, n))
    U, S, Vt = np.linalg.svd(W, full_matrices=False)
    U_r = U[:, :r]
    S_r = S[:r]
    Vt_r = Vt[:r, :]
    W_low = (U_r * S_r) @ Vt_r
    residual = W - W_low
    qmax = (1 << (bits - 1)) - 1
    scale = np.max(np.abs(residual)) / qmax if np.max(np.abs(residual)) > 0 else 1.0
    q_res = np.round(residual / scale).astype(np.int8)
    q_res = np.clip(q_res, -qmax, qmax)
    deq_res = q_res.astype(np.float32) * scale
    path_a = W_low
    path_b = deq_res
    W_hat = alpha * path_a + (1.0 - alpha) * path_b
    return W_hat.astype(np.float32)


def _enhance_evolution_with_low_rank_mla(self, state_dict, rank=8, bits=4):
    if not isinstance(state_dict, dict):
        return state_dict
    enhanced = {}
    for key, value in state_dict.items():
        try:
            arr = value.detach().cpu().numpy() if hasattr(value, "detach") else value
        except Exception:
            enhanced[key] = value
            continue
        if hasattr(arr, "ndim") and arr.ndim == 2 and min(arr.shape) >= 2:
            try:
                compressed = _apply_low_rank_mla_quantization(arr, rank=rank, bits=bits)
                enhanced[key] = compressed
            except Exception:
                enhanced[key] = value
        else:
            enhanced[key] = value
    return enhanced
# Auto-generated code snippet by Emily Self-Modify
# Based on: RunningTensor, SubZero+
# Generated: 2026-09-14T22:56:21.977731

def _subzero_tensor_compress(self, payload: dict, rank: int = 8) -> dict:
    import numpy as np
    from sklearn.decomposition import TruncatedSVD

    def _flatten(obj):
        if isinstance(obj, dict):
            return {k: _flatten(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_flatten(v) for v in obj]
        if isinstance(obj, (int, float)) and not isinstance(obj, bool):
            return float(obj)
        return obj

    def _tensorize(obj, acc):
        if isinstance(obj, dict):
            for v in obj.values():
                _tensorize(v, acc)
        elif isinstance(obj, list):
            for v in obj:
                _tensorize(v, acc)
        elif isinstance(obj, float):
            acc.append(obj)

    flat = _flatten(payload)
    scalars = []
    _tensorize(flat, scalars)
    if len(scalars) < rank * 2:
        return {"compressed": False, "payload": flat, "reason": "insufficient_scalars"}

    mat = np.asarray(scalars, dtype=np.float64).reshape(-1, 1)
    svd = TruncatedSVD(n_components=min(rank, mat.shape[0] - 1), random_state=42)
    reduced = svd.fit_transform(mat)
    recon = svd.inverse_transform(reduced)
    residual = float(np.linalg.norm(mat - recon) / (np.linalg.norm(mat) + 1e-12))

    return {
        "compressed": True,
        "rank": int(reduced.shape[1]),
        "residual": residual,
        "energy": float(np.sum(svd.singular_values_ ** 2)),
        "payload": flat,
    }

self._subzero_cache = _subzero_tensor_compress(self, self._last_payload or {})
if self._subzero_cache.get("compressed") and self._subzero_cache["residual"] < 0.05:
    self._last_payload = self._subzero_cache["payload"]
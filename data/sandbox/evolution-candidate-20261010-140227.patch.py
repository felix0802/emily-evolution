# Auto-generated code snippet by Emily Self-Modify
# Based on: Sim-to-real 强化学习, 安全过滤器
# Generated: 2026-10-10T14:02:27.070787

def apply_sim_to_real_safety_filter(self, action, obs, sim_state=None):
    import numpy as np
    from sklearn.ensemble import IsolationForest

    if not hasattr(self, "_safety_filter"):
        self._safety_filter = IsolationForest(
            n_estimators=50, contamination=0.05, random_state=42
        )
        self._safety_buffer = []
        self._domain_shift_threshold = 0.35

    obs_vec = np.asarray(obs, dtype=float).flatten()
    if obs_vec.size == 0:
        return action, {"filtered": False, "reason": "empty_obs"}

    self._safety_buffer.append(obs_vec)
    if len(self._safety_buffer) > 200:
        self._safety_buffer.pop(0)

    if len(self._safety_buffer) >= 20:
        X = np.vstack(self._safety_buffer)
        if not hasattr(self, "_sf_fitted"):
            self._safety_filter.fit(X)
            self._sf_fitted = True

    domain_shift = 0.0
    if sim_state is not None and hasattr(self, "_sf_fitted"):
        sim_vec = np.asarray(sim_state, dtype=float).flatten()
        if sim_vec.size == obs_vec.size:
            denom = np.linalg.norm(sim_vec) + 1e-8
            domain_shift = float(np.linalg.norm(obs_vec - sim_vec) / denom)

    is_anomaly = False
    if hasattr(self, "_sf_fitted"):
        try:
            is_anomaly = self._safety_filter.predict(obs_vec.reshape(1, -1))[0] == -1
        except Exception:
            is_anomaly = False

    if domain_shift > self._domain_shift_threshold or is_anomaly:
        safe_action = np.zeros_like(np.asarray(action, dtype=float))
        return safe_action, {
            "filtered": True,
            "domain_shift": domain_shift,
            "anomaly": bool(is_anomaly),
        }

    return action, {"filtered": False, "domain_shift": domain_shift}
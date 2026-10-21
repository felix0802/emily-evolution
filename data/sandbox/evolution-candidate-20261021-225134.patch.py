# Auto-generated code snippet by Emily Self-Modify
# Based on: 混合灵巧模仿, 连续时间策略梯度
# Generated: 2026-10-21T22:51:34.880895

def _hybrid_dexterous_imitation_and_ctpg(self, perception_state, action_space):
    import numpy as np
    from collections import deque

    if not hasattr(self, "_ctpg_buffer"):
        self._ctpg_buffer = deque(maxlen=256)
        self._ctpg_theta = np.zeros(action_space.shape[0] if hasattr(action_space, "shape") else 1)
        self._ctpg_baseline = 0.0
        self._ctpg_lr = 1e-3
        self._ctpg_tau = 0.05
        self._imitation_weights = None

    demo_traj = perception_state.get("demonstration_trajectory") if isinstance(perception_state, dict) else None
    if demo_traj is not None and len(demo_traj) > 0:
        demo = np.asarray(demo_traj, dtype=float)
        if demo.ndim == 1:
            demo = demo.reshape(-1, 1)
        feat = demo.mean(axis=0)
        if self._imitation_weights is None or self._imitation_weights.shape != feat.shape:
            self._imitation_weights = np.zeros_like(feat)
        self._imitation_weights = 0.9 * self._imitation_weights + 0.1 * feat
        imitation_bias = self._imitation_weights
    else:
        imitation_bias = np.zeros_like(self._ctpg_theta)

    state_vec = perception_state.get("state_vector") if isinstance(perception_state, dict) else None
    if state_vec is None:
        state_vec = np.zeros_like(self._ctpg_theta)
    state_vec = np.asarray(state_vec, dtype=float).ravel()
    if state_vec.shape[0] != self._ctpg_theta.shape[0]:
        pad = self._ctpg_theta.shape[0] - state_vec.shape[0]
        state_vec = np.concatenate([state_vec, np.zeros(max(pad, 0))])[: self._ctpg_theta.shape[0]]

    mu = np.tanh(self._ctpg_theta * state_vec + imitation_bias)
    sigma = 0.1 + 0.05 * np.abs(mu)
    action = mu + sigma * np.random.randn(*mu.shape)

    reward = perception_state.get("reward", 0.0) if isinstance(perception_state, dict) else 0.0
    self._ctpg_buffer.append((state_vec.copy(), action.copy(), float(reward)))

    if len(self._ctpg_buffer) >= 8:
        states = np.stack([b[0] for b in self._ctpg_buffer])
        acts = np.stack([b[1] for b in self._ctpg_buffer])
        rews = np.array([b[2] for b in self._ctpg_buffer])
        self._ctpg_baseline = (1 - self._ctpg_tau) * self._ctpg_baseline + self._ctpg_tau * rews.mean()
        adv = rews - self._ctpg_baseline
        grad = np.zeros_like(self._ctpg_theta)
        for s, a, g in zip(states, acts, adv):
            grad += g * (a - np.tanh(self._ctpg_theta * s)) * s
        self._ctpg_theta += self._ctpg_lr * grad / len(self._ctpg_buffer)

    return {
        "action": action,
        "theta": self._ctpg_theta.copy(),
        "imitation_bias": imitation_bias,
        "baseline": self._ctpg_baseline,
    }
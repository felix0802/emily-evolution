# Auto-generated code snippet by Emily Self-Modify
# Based on: 视频扩散模型用于潜在动作学习, 直接纳什优化（DNO）
# Generated: 2026-11-04T18:57:42.401032

def _video_diffusion_latent_action(self, obs_sequence, horizon=8):
    import numpy as np
    from sklearn.decomposition import PCA
    frames = np.asarray(obs_sequence, dtype=np.float64)
    if frames.ndim == 1:
        frames = frames.reshape(1, -1)
    n = frames.shape[0]
    if n < 2:
        return np.zeros((horizon, frames.shape[1]))
    diffs = np.diff(frames, axis=0)
    pca = PCA(n_components=min(4, diffs.shape[1], diffs.shape[0]))
    latent = pca.fit_transform(diffs)
    noise_scale = float(np.std(latent)) + 1e-6
    traj = np.zeros((horizon, latent.shape[1]))
    cur = latent[-1].copy()
    for t in range(horizon):
        drift = np.mean(latent, axis=0) - cur
        cur = cur + 0.3 * drift + noise_scale * 0.1 * np.random.randn(*cur.shape)
        traj[t] = cur
    return pca.inverse_transform(traj)

def _direct_nash_optimize(self, candidate_actions, payoff_fn, iters=30, lr=0.05):
    import numpy as np
    acts = [np.asarray(a, dtype=np.float64) for a in candidate_actions]
    if not acts:
        return None
    n = len(acts)
    weights = np.ones(n) / n
    for _ in range(iters):
        payoffs = np.array([payoff_fn(a) for a in acts], dtype=np.float64)
        grad = weights * (payoffs - np.dot(weights, payoffs))
        weights = weights + lr * grad
        weights = np.clip(weights, 1e-6, None)
        weights = weights / weights.sum()
    best = int(np.argmax(weights))
    return acts[best], weights

def _enhanced_evolve_step(self, obs_sequence, candidate_actions, payoff_fn):
    latent_plan = self._video_diffusion_latent_action(obs_sequence)
    enriched = list(candidate_actions) + [latent_plan.flatten()]
    action, weights = self._direct_nash_optimize(enriched, payoff_fn)
    return {"action": action, "nash_weights": weights, "latent_plan": latent_plan}

self._video_diffusion_latent_action = _video_diffusion_latent_action.__get__(self)
self._direct_nash_optimize = _direct_nash_optimize.__get__(self)
self._enhanced_evolve_step = _enhanced_evolve_step.__get__(self)
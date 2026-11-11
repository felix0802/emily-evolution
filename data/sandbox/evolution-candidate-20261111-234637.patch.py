# Auto-generated code snippet by Emily Self-Modify
# Based on: RLVR（可验证奖励强化学习）, 训练时脚手架（Training-time Scaffolds）, 脉冲神经网络强化学习（SNN RL）
# Generated: 2026-11-11T23:46:37.024256

def _snn_rl_verify_and_scaffold(self, candidate_patch: str, task_spec: dict, max_rounds: int = 3) -> dict:
    import numpy as np
    from sklearn.feature_extraction.text import HashingVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    vec = HashingVectorizer(n_features=256, alternate_sign=False, norm='l2')
    def _embed(txt: str) -> np.ndarray:
        return vec.transform([txt]).toarray()[0]

    def _verifiable_reward(patch: str) -> float:
        checks = []
        try:
            compile(patch, "<candidate>", "exec")
            checks.append(1.0)
        except SyntaxError:
            checks.append(0.0)
        for token in task_spec.get("required_tokens", []):
            checks.append(1.0 if token in patch else 0.0)
        for bad in task_spec.get("forbidden_tokens", []):
            checks.append(0.0 if bad in patch else 1.0)
        if not checks:
            return 0.0
        return float(np.mean(checks))

    class _SpikingPolicy:
        def __init__(self, dim: int, lr: float = 0.05):
            self.w = np.zeros(dim)
            self.lr = lr
            self.mem = np.zeros(dim)
            self.threshold = 0.6

        def act(self, state: np.ndarray) -> int:
            self.mem = 0.7 * self.mem + state
            spikes = (self.mem > self.threshold).astype(float)
            score = float(np.dot(self.w, spikes))
            return 1 if score >= 0 else 0

        def update(self, state: np.ndarray, action: int, reward: float):
            spikes = (self.mem > self.threshold).astype(float)
            grad = (reward - 0.5) * (1 if action == 1 else -1) * spikes
            self.w += self.lr * grad
            self.mem *= 0.9

    state = _embed(candidate_patch)
    policy = _SpikingPolicy(dim=state.shape[0])
    best_patch, best_reward = candidate_patch, _verifiable_reward(candidate_patch)
    scaffold_log = []

    for rnd in range(max_rounds):
        action = policy.act(state)
        if action == 1:
            scaffold = task_spec.get("scaffold_hint", "")
            trial = candidate_patch + ("\n# scaffold: " + scaffold if scaffold else "")
        else:
            trial = candidate_patch
        reward = _verifiable_reward(trial)
        policy.update(state, action, reward)
        scaffold_log.append({"round": rnd, "action": action, "reward": reward})
        if reward > best_reward:
            best_reward, best_patch = reward, trial
        if best_reward >= 0.999:
            break

    return {
        "patch": best_patch,
        "reward": best_reward,
        "scaffold_log": scaffold_log,
        "method": "snn_rl_verifiable",
    }

self._snn_rl_verify_and_scaffold = _snn_rl_verify_and_scaffold.__get__(self)
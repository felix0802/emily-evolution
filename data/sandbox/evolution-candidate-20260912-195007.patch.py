# Auto-generated code snippet by Emily Self-Modify
# Based on: 多步转移前瞻, 生成式回放
# Generated: 2026-09-12T19:50:07.524664

def multi_step_lookahead_replay(agent, state, n_steps=3, replay_size=8, gamma=0.95):
    import random
    import numpy as np

    def rollout(s, depth):
        if depth == 0:
            return 0.0
        actions = agent.decision_layer.candidate_actions(s)
        if not actions:
            return 0.0
        best = -float("inf")
        for a in actions:
            ns, r = agent.action_layer.simulate(s, a)
            val = r + gamma * rollout(ns, depth - 1)
            if val > best:
                best = val
        return best

    lookahead_value = rollout(state, n_steps)

    replay_buffer = getattr(agent, "_generative_replay", [])
    if len(replay_buffer) >= replay_size:
        sampled = random.sample(replay_buffer, replay_size)
        gen_states = []
        for past in sampled:
            noise = np.random.normal(0, 0.05, size=len(past)) if hasattr(past, "__len__") else 0.0
            gen_states.append(np.array(past) + noise if hasattr(past, "__len__") else past)
        replay_bonus = float(np.mean([rollout(gs, 1) for gs in gen_states]))
    else:
        replay_bonus = 0.0

    combined = 0.7 * lookahead_value + 0.3 * replay_bonus
    agent._last_lookahead = combined
    return combined

# 插入到 evolve() 中：
# score = multi_step_lookahead_replay(self, current_state, n_steps=3, replay_size=8)
# if score > self.best_score:
#     self.best_score = score
#     self._generative_replay.append(current_state)
#     self._generative_replay = self._generative_replay[-64:]
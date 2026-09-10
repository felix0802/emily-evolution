# Auto-generated code snippet by Emily Self-Modify
# Based on: 多智能体强化学习, 合成奖励与RLVR
# Generated: 2026-09-10T06:45:01.131668

def synthesize_reward_and_evolve(state, trajectory, num_agents=4, gamma=0.97):
    import numpy as np
    from collections import deque

    # 多智能体策略梯度 + 合成奖励(RLVR: reward from verifiable reasoning)
    agents = [{"theta": np.random.randn(8) * 0.01, "baseline": 0.0} for _ in range(num_agents)]
    rewards = np.zeros(num_agents)
    for i, ag in enumerate(agents):
        logits = np.tanh(ag["theta"] @ np.array(state[:8], dtype=float))
        action = int(np.argmax(logits))
        # 合成奖励：可验证推理链一致性 + 轨迹回报
        consistency = 1.0 - abs(np.std(logits))
        verifiable = 1.0 if trajectory and trajectory[-1].get("verified", False) else 0.0
        rewards[i] = 0.6 * consistency + 0.4 * verifiable + 0.1 * np.random.randn()
        ag["baseline"] = gamma * ag["baseline"] + (1 - gamma) * rewards[i]
        adv = rewards[i] - ag["baseline"]
        ag["theta"] += 0.05 * adv * np.array(state[:8], dtype=float)

    # 合成奖励聚合 -> 全局进化信号
    synth_reward = float(np.mean(rewards) + 0.5 * np.std(rewards))
    best_agent = int(np.argmax(rewards))
    state["multi_agent"] = {
        "synth_reward": synth_reward,
        "best_agent": best_agent,
        "agent_rewards": rewards.tolist(),
        "policy_shift": float(np.linalg.norm(agents[best_agent]["theta"])),
    }
    return state, synth_reward
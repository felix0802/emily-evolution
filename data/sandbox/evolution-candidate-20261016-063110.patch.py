# Auto-generated code snippet by Emily Self-Modify
# Based on: 鲁棒强化学习, 隐藏上下文建模, 图书馆员智能体
# Generated: 2026-10-16T06:31:10.681104

def librarian_context_enhancement(papers, context_history, rl_state):
    import numpy as np
    from collections import deque

    # 隐藏上下文建模：维护潜在主题状态
    hidden_ctx = rl_state.get("hidden_context", deque(maxlen=32))
    topic_embeddings = []
    for p in papers:
        text = (p.get("title", "") + " " + p.get("summary", "")).lower()
        vec = np.zeros(64)
        for i, tok in enumerate(text.split()[:256]):
            vec[hash(tok) % 64] += 1.0 / (i + 1)
        norm = np.linalg.norm(vec) + 1e-8
        topic_embeddings.append(vec / norm)

    if topic_embeddings:
        latent = np.mean(topic_embeddings, axis=0)
        hidden_ctx.append(latent)

    # 图书馆员智能体：基于历史上下文做检索式重排序
    if len(hidden_ctx) >= 2:
        prev = hidden_ctx[-2]
        curr = hidden_ctx[-1]
        drift = float(np.linalg.norm(curr - prev))
    else:
        drift = 0.0

    # 鲁棒强化学习：对扰动敏感的论文降权
    scored = []
    for p, emb in zip(papers, topic_embeddings):
        base = p.get("score", 1.0)
        novelty = float(np.dot(emb, hidden_ctx[-1])) if hidden_ctx else 0.0
        robustness = 1.0 / (1.0 + drift)
        adjusted = base * (0.6 + 0.4 * novelty) * robustness
        scored.append((adjusted, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    rl_state["hidden_context"] = hidden_ctx
    rl_state["context_drift"] = drift
    return [p for _, p in scored]
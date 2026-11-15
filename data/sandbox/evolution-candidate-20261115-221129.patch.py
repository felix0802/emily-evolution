# Auto-generated code snippet by Emily Self-Modify
# Based on: 半监督/自监督学习与 MLE 智能体结合, 前瞻性内存估值（Prospective Valuation）
# Generated: 2026-11-15T22:11:29.684095

def prospective_memory_valuation(memory_bank, candidate_actions, horizon=5, gamma=0.9):
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

    if not memory_bank or not candidate_actions:
        return candidate_actions, {}

    def _embed(text):
        vec = np.zeros(64)
        for i, ch in enumerate(str(text)[:256]):
            vec[i % 64] += (ord(ch) % 31) / 31.0
        n = np.linalg.norm(vec)
        return vec / n if n > 0 else vec

    mem_vecs = np.array([_embed(m.get("content", m)) for m in memory_bank])
    act_vecs = np.array([_embed(a) for a in candidate_actions])

    sims = cosine_similarity(act_vecs, mem_vecs)
    novelty = 1.0 - sims.max(axis=1)

    values = {}
    for idx, action in enumerate(candidate_actions):
        v = 0.0
        for h in range(1, horizon + 1):
            decay = gamma ** h
            expected_gain = novelty[idx] * (1.0 - 1.0 / (h + 1))
            risk_penalty = sims[idx].mean() * (1.0 - novelty[idx])
            v += decay * (expected_gain - 0.3 * risk_penalty)
        values[idx] = float(v)

    ranked = sorted(range(len(candidate_actions)), key=lambda i: values[i], reverse=True)
    ranked_actions = [candidate_actions[i] for i in ranked]
    return ranked_actions, values


def self_supervised_memory_update(memory_bank, new_experiences, max_size=200):
    import numpy as np

    if not new_experiences:
        return memory_bank

    def _sig(exp):
        s = str(exp)
        return hash(s) % (10 ** 8)

    seen = {_sig(m.get("content", m)) for m in memory_bank}
    for exp in new_experiences:
        sig = _sig(exp.get("content", exp) if isinstance(exp, dict) else exp)
        if sig in seen:
            continue
        seen.add(sig)
        if isinstance(exp, dict):
            exp.setdefault("confidence", 0.5)
            exp["confidence"] = min(1.0, exp["confidence"] + 0.1)
            memory_bank.append(exp)
        else:
            memory_bank.append({"content": exp, "confidence": 0.5})

    if len(memory_bank) > max_size:
        memory_bank.sort(key=lambda m: m.get("confidence", 0.5), reverse=True)
        memory_bank = memory_bank[:max_size]
    return memory_bank


def evolve_with_prospective_valuation(self, candidate_actions, new_experiences=None):
    if new_experiences:
        self.memory_bank = self_supervised_memory_update(
            getattr(self, "memory_bank", []), new_experiences
        )
    ranked, values = prospective_memory_valuation(
        getattr(self, "memory_bank", []), candidate_actions
    )
    self.last_valuation = values
    return ranked
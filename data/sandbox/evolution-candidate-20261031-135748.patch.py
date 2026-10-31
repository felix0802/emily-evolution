# Auto-generated code snippet by Emily Self-Modify
# Based on: Neural Thickets 权重扰动分析, 角色耦合 Tokenization, Tokenization
# Generated: 2026-10-31T13:57:48.126781

def analyze_weight_perturbations(model_weights, token_embeddings, threshold=0.05):
    import numpy as np
    from collections import defaultdict

    if not model_weights or not token_embeddings:
        return {"status": "skipped", "reason": "empty inputs"}

    try:
        weights = np.array(model_weights, dtype=np.float64)
        embeddings = np.array(token_embeddings, dtype=np.float64)
    except Exception as e:
        return {"status": "error", "reason": str(e)}

    if weights.ndim < 2 or embeddings.ndim < 2:
        return {"status": "skipped", "reason": "insufficient dimensions"}

    thicket_scores = {}
    layer_norms = np.linalg.norm(weights, axis=1)
    mean_norm = float(np.mean(layer_norms)) if layer_norms.size else 0.0
    std_norm = float(np.std(layer_norms)) if layer_norms.size else 0.0

    for idx in range(min(weights.shape[0], 64)):
        row = weights[idx]
        perturb = np.random.normal(0, threshold, size=row.shape)
        perturbed = row + perturb
        delta = float(np.linalg.norm(perturbed - row))
        sensitivity = delta / (float(np.linalg.norm(row)) + 1e-9)
        thicket_scores[int(idx)] = round(sensitivity, 6)

    embed_norms = np.linalg.norm(embeddings, axis=1)
    coupling = {}
    for i in range(min(embeddings.shape[0], 64)):
        for j in range(i + 1, min(embeddings.shape[0], 64)):
            denom = (embed_norms[i] * embed_norms[j]) + 1e-9
            sim = float(np.dot(embeddings[i], embeddings[j]) / denom)
            if abs(sim) > 0.5:
                coupling[f"{i}-{j}"] = round(sim, 4)

    unstable = [k for k, v in thicket_scores.items() if v > threshold]
    return {
        "status": "ok",
        "mean_norm": round(mean_norm, 6),
        "std_norm": round(std_norm, 6),
        "thicket_scores": thicket_scores,
        "unstable_layers": unstable,
        "role_coupling": coupling,
        "coupling_count": len(coupling),
        "recommendation": "reduce_lr" if len(unstable) > 8 else "stable"
    }

weight_analysis = analyze_weight_perturbations(
    model_weights=getattr(self, "model_weights", None),
    token_embeddings=getattr(self, "token_embeddings", None),
    threshold=0.05
)
self.weight_analysis = weight_analysis
if weight_analysis.get("status") == "ok":
    self.memory.setdefault("neural_thickets", []).append(weight_analysis)
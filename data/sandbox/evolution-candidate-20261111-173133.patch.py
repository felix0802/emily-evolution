# Auto-generated code snippet by Emily Self-Modify
# Based on: Mechanistic Interpretability, Interpretability, Mechanistic
# Generated: 2026-11-11T17:31:33.962360

def _mechanistic_interpretability_probe(model_weights, activations, layer_names):
    import numpy as np
    from sklearn.decomposition import PCA
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score

    report = {"layers": {}, "circuits": [], "summary": {}}
    if not activations or not model_weights:
        return report

    for layer in layer_names:
        if layer not in activations:
            continue
        acts = np.asarray(activations[layer], dtype=np.float64)
        if acts.ndim != 2 or acts.shape[0] < 4:
            continue
        acts = acts - acts.mean(axis=0, keepdims=True)
        n_comp = min(8, acts.shape[0] - 1, acts.shape[1])
        pca = PCA(n_components=n_comp)
        reduced = pca.fit_transform(acts)
        var_explained = float(np.sum(pca.explained_variance_ratio_))
        sparsity = float(np.mean(np.abs(acts) < 1e-3))
        report["layers"][layer] = {
            "variance_explained": round(var_explained, 4),
            "activation_sparsity": round(sparsity, 4),
            "effective_rank": int(np.sum(pca.explained_variance_ratio_ > 0.05)),
        }
        if acts.shape[0] >= 8:
            labels = (reduced[:, 0] > np.median(reduced[:, 0])).astype(int)
            if len(np.unique(labels)) == 2:
                clf = LogisticRegression(max_iter=200)
                clf.fit(reduced, labels)
                acc = accuracy_score(labels, clf.predict(reduced))
                report["layers"][layer]["probe_accuracy"] = round(float(acc), 4)

    layer_scores = [(l, d.get("variance_explained", 0)) for l, d in report["layers"].items()]
    layer_scores.sort(key=lambda x: x[1], reverse=True)
    report["circuits"] = [{"layer": l, "score": s} for l, s in layer_scores[:3]]
    report["summary"] = {
        "num_layers_probed": len(report["layers"]),
        "top_circuit_layer": layer_scores[0][0] if layer_scores else None,
        "mean_sparsity": round(float(np.mean([d.get("activation_sparsity", 0) for d in report["layers"].values()])) if report["layers"] else 0.0, 4),
    }
    return report


def _apply_mechanistic_interpretability(context):
    try:
        weights = context.get("model_weights", {})
        acts = context.get("activations", {})
        layers = context.get("layer_names", list(acts.keys()))
        probe = _mechanistic_interpretability_probe(weights, acts, layers)
        context.setdefault("interpretability", {})["mechanistic_probe"] = probe
        if probe.get("summary", {}).get("top_circuit_layer"):
            context["decision_hint"] = {
                "focus_layer": probe["summary"]["top_circuit_layer"],
                "sparsity": probe["summary"]["mean_sparsity"],
            }
        return context
    except Exception as exc:
        context.setdefault("errors", []).append(f"mech_interp: {exc}")
        return context
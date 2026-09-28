# Auto-generated code snippet by Emily Self-Modify
# Based on: 自监督置信度训练, 输出后处理属性对齐
# Generated: 2026-09-28T10:15:26.548458

def _self_supervised_confidence_and_alignment(raw_outputs, context_embeddings, threshold=0.62):
    import numpy as np
    from sklearn.preprocessing import StandardScaler
    from sklearn.isotonic import IsotonicRegression

    if not raw_outputs:
        return []

    scores = np.array([float(o.get("score", 0.0)) for o in raw_outputs], dtype=float)
    feats = np.array(context_embeddings, dtype=float)
    if feats.ndim == 1:
        feats = feats.reshape(-1, 1)

    scaler = StandardScaler()
    feats_s = scaler.fit_transform(feats)

    pseudo_labels = (scores >= np.median(scores)).astype(int)
    if len(np.unique(pseudo_labels)) < 2:
        pseudo_labels = (scores >= scores.mean()).astype(int)

    try:
        from sklearn.linear_model import LogisticRegression
        clf = LogisticRegression(max_iter=200, solver="liblinear")
        clf.fit(feats_s, pseudo_labels)
        conf = clf.predict_proba(feats_s)[:, 1]
    except Exception:
        conf = 1.0 / (1.0 + np.exp(-(scores - scores.mean()) / (scores.std() + 1e-9)))

    try:
        iso = IsotonicRegression(out_of_bounds="clip")
        conf = iso.fit_transform(scores, conf)
    except Exception:
        pass

    aligned = []
    for out, c in zip(raw_outputs, conf):
        item = dict(out)
        item["confidence"] = float(np.clip(c, 0.0, 1.0))
        item["aligned"] = bool(item["confidence"] >= threshold)
        if "attributes" in item and isinstance(item["attributes"], dict):
            item["attributes"] = {
                k: (v if isinstance(v, (int, float, str, bool, type(None))) else str(v))
                for k, v in item["attributes"].items()
            }
        aligned.append(item)

    aligned.sort(key=lambda x: x["confidence"], reverse=True)
    return aligned
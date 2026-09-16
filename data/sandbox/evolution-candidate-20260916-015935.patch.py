# Auto-generated code snippet by Emily Self-Modify
# Based on: Joint Embedding Predictive Architecture (JEPA), Embedding
# Generated: 2026-09-16T01:59:35.299707

def jepa_embedding_predictor(perception_embeddings, action_embeddings, target_dim=128):
    import numpy as np
    from sklearn.decomposition import PCA
    from sklearn.linear_model import Ridge

    if len(perception_embeddings) < 2 or len(action_embeddings) < 2:
        return None

    X = np.asarray(perception_embeddings, dtype=np.float64)
    A = np.asarray(action_embeddings, dtype=np.float64)

    n = min(len(X), len(A))
    X, A = X[:n], A[:n]

    if X.ndim == 1:
        X = X.reshape(-1, 1)
    if A.ndim == 1:
        A = A.reshape(-1, 1)

    joint = np.concatenate([X, A], axis=1)

    dim = min(target_dim, joint.shape[1], max(2, joint.shape[0] - 1))
    pca = PCA(n_components=dim, random_state=42)
    z = pca.fit_transform(joint)

    context = z[:-1]
    target = z[1:]

    predictor = Ridge(alpha=1.0)
    predictor.fit(context, target)

    z_next_pred = predictor.predict(z[-1:].reshape(1, -1))[0]

    recon = pca.inverse_transform(z_next_pred.reshape(1, -1))[0]
    pred_perception = recon[:X.shape[1]]
    pred_action = recon[X.shape[1]:]

    pred_error = float(np.linalg.norm(z[-1] - z_next_pred))
    novelty = float(np.linalg.norm(pred_perception - X[-1]))

    return {
        "predicted_perception_embedding": pred_perception.tolist(),
        "predicted_action_embedding": pred_action.tolist(),
        "latent_prediction_error": pred_error,
        "novelty_score": novelty,
        "latent_dim": int(dim),
        "should_explore": novelty > float(np.mean(np.linalg.norm(np.diff(z, axis=0), axis=1)) + 1e-8),
    }
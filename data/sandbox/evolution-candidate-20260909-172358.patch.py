# Auto-generated code snippet by Emily Self-Modify
# Based on: Jacobian-based nonlinear information capacity preservation, Geometry-aware complementary diversity metrics
# Generated: 2026-09-09T17:23:58.083735

def _geometry_aware_diversity_guard(self, population, jacobian_threshold=0.15, diversity_floor=0.72):
    """Jacobian-based nonlinear capacity preservation + geometry-aware diversity metrics."""
    import numpy as np
    from sklearn.metrics import pairwise_distances
    
    # Extract feature vectors from population (assumes each has .embedding or .features)
    X = np.array([ind.get('embedding', ind.get('features', np.random.rand(64))) for ind in population])
    
    # Jacobian-based nonlinear information capacity (approximated via local curvature)
    if X.shape[0] > 3 and X.shape[1] > 2:
        # Compute pairwise distances and local neighborhood structure
        dist = pairwise_distances(X, metric='euclidean')
        k = min(3, X.shape[0]-1)
        neighbors = np.argsort(dist, axis=1)[:, 1:k+1]
        
        # Approximate Jacobian norm via local linearity deviation
        jacobian_norms = []
        for i in range(X.shape[0]):
            local_pts = X[neighbors[i]]
            if len(local_pts) >= 2:
                # Measure nonlinearity via variance of local direction changes
                diffs = local_pts - X[i]
                if len(diffs) > 1:
                    cos_sim = np.abs(np.dot(diffs[0], diffs[1]) / (np.linalg.norm(diffs[0])*np.linalg.norm(diffs[1])+1e-8))
                    jacobian_norms.append(1 - cos_sim)  # higher = more nonlinear capacity
        if jacobian_norms:
            nonlinear_capacity = np.mean(jacobian_norms)
            if nonlinear_capacity < jacobian_threshold:
                # Inject noise to increase nonlinear diversity
                for idx in np.random.choice(len(population), max(1, len(population)//5), replace=False):
                    population[idx]['embedding'] = X[idx] + np.random.normal(0, 0.05, X.shape[1])
    
    # Geometry-aware complementary diversity metric (pairwise angular diversity)
    if X.shape[0] > 1:
        norms = np.linalg.norm(X, axis=1, keepdims=True) + 1e-8
        normalized = X / norms
        cos_matrix = np.clip(np.dot(normalized, normalized.T), -1, 1)
        angles = np.arccos(cos_matrix) / np.pi  # normalized to [0,1]
        np.fill_diagonal(angles, 0)
        complementary_diversity = np.mean(angles[angles > 0])
        
        if complementary_diversity < diversity_floor:
            # Reposition most similar individuals to orthogonal directions
            sim_pairs = np.argwhere(angles > 0)
            if len(sim_pairs) > 0:
                # Find most similar pair
                flat_angles = angles.flatten()
                flat_angles[flat_angles == 0] = 1.0
                min_idx = np.argmin(flat_angles)
                i, j = min_idx // X.shape[0], min_idx % X.shape[0]
                if i != j:
                    # Push j away from i in orthogonal direction
                    direction = X[i] - np.dot(X[i], X[j])/(np.dot(X[j], X[j])+1e-8) * X[j]
                    if np.linalg.norm(direction) > 1e-6:
                        population[j]['embedding'] = X[j] + 0.3 * direction / np.linalg.norm(direction)
    
    return population
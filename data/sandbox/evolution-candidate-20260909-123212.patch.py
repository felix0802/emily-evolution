# Auto-generated code snippet by Emily Self-Modify
# Based on: 多任务学习 (MTL), 梯度手术 (Gradient Surgery)
# Generated: 2026-09-09T12:32:12.441195

def apply_gradient_surgery(self, gradients):
    """Apply gradient surgery to reconcile conflicting gradients from MTL tasks."""
    if len(gradients) < 2:
        return gradients[0] if gradients else None
    
    # Project each gradient onto the normal plane of others to reduce conflicts
    import numpy as np
    grads = [np.array(g) for g in gradients]
    dim = grads[0].shape
    flat_grads = [g.flatten() for g in grads]
    
    # Compute pairwise projections and subtract conflicting components
    for i in range(len(flat_grads)):
        for j in range(len(flat_grads)):
            if i != j:
                proj = np.dot(flat_grads[i], flat_grads[j]) / (np.linalg.norm(flat_grads[j])**2 + 1e-8)
                flat_grads[i] = flat_grads[i] - proj * flat_grads[j]
    
    # Average the surgically modified gradients
    final_grad = np.mean(flat_grads, axis=0).reshape(dim)
    return final_grad

# Call this in evolve() when aggregating task gradients
# combined_grad = self.apply_gradient_surgery([grad_task1, grad_task2, grad_task3])
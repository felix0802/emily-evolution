# Auto-generated code snippet by Emily Self-Modify
# Based on: 在线变点检测, 合成任务扩展
# Generated: 2026-09-07T13:44:48.294615

def online_change_detection(self, metric_stream):
    """Detect shifts in performance metrics to trigger adaptation."""
    if not hasattr(self, '_metric_buffer'):
        self._metric_buffer = []
        self._baseline_mean = None
        self._baseline_std = None
    
    self._metric_buffer.append(metric_stream)
    if len(self._metric_buffer) > 100:
        self._metric_buffer.pop(0)
    
    if len(self._metric_buffer) < 30:
        return False
    
    if self._baseline_mean is None:
        self._baseline_mean = np.mean(self._metric_buffer[:-10])
        self._baseline_std = np.std(self._metric_buffer[:-10]) + 1e-9
        return False
    
    recent_mean = np.mean(self._metric_buffer[-10:])
    z_score = abs(recent_mean - self._baseline_mean) / self._baseline_std
    
    if z_score > 3.0:
        self._baseline_mean = recent_mean
        self._baseline_std = np.std(self._metric_buffer[-10:]) + 1e-9
        return True
    return False

def synthetic_task_expansion(self, base_tasks):
    """Generate synthetic variants of tasks for robust training."""
    synthetic_tasks = []
    for task in base_tasks[:5]:
        # Perturb parameters slightly
        perturbed = task.copy()
        if 'params' in perturbed:
            for key in perturbed['params']:
                if isinstance(perturbed['params'][key], (int, float)):
                    perturbed['params'][key] *= (1 + np.random.uniform(-0.2, 0.2))
        synthetic_tasks.append(perturbed)
        
        # Create combinatorial variant
        if 'constraints' in perturbed:
            variant = perturbed.copy()
            variant['constraints'] = {k: v * np.random.uniform(0.8, 1.2) 
                                     for k, v in perturbed['constraints'].items()}
            synthetic_tasks.append(variant)
    
    return synthetic_tasks

# Integration point in evolve():
if self.online_change_detection(self.performance_history[-1] if self.performance_history else 0.5):
    self.logger.info("Change detected - triggering adaptive response")
    expanded = self.synthetic_task_expansion(self.task_queue)
    self.task_queue.extend(expanded)
    self.adaptation_strategy = 'exploration'
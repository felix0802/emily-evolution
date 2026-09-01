# Auto-generated code snippet by Emily Self-Modify
# Based on: 细粒度对象幻觉基准, 隐藏状态轨迹几何分析
# Generated: 2026-09-01T03:08:18.646976

```python
def enhance_with_geometry_analysis(self):
    """增强：隐藏状态轨迹几何分析 + 细粒度幻觉检测"""
    if not hasattr(self, 'llm') or not hasattr(self.llm, 'get_hidden_states'):
        return
    
    # 获取当前批次隐藏状态
    hidden_states = self.llm.get_hidden_states(self.current_input)
    if len(hidden_states) < 3:
        return
    
    # 计算轨迹几何特征
    import numpy as np
    trajectory = np.array(hidden_states)
    diffs = np.diff(trajectory, axis=0)
    speeds = np.linalg.norm(diffs, axis=1)
    accelerations = np.diff(speeds)
    
    # 检测异常轨迹（潜在幻觉）
    mean_speed = np.mean(speeds)
    std_speed = np.std(speeds)
    anomaly_threshold = mean_speed + 2 * std_speed
    
    # 细粒度幻觉基准：检查高曲率区域
    curvatures = []
    for i in range(1, len(diffs)-1):
        v1, v2 = diffs[i-1], diffs[i]
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
        curvatures.append(1 - cos_angle)
    
    high_curvature = [i for i, c in enumerate(curvatures) if c > 0.8]
    
    # 更新内部状态
    self.geometry_metrics = {
        'mean_speed': float(mean_speed),
        'anomaly_count': int(np.sum(speeds > anomaly_threshold)),
        'high_curvature_points': high_curvature,
        'trajectory_stability': float(1.0 / (1.0 + np.std(speeds)))
    }
    
    # 如果检测到幻觉风险，调整生成参数
    if self.geometry_metrics['anomaly_count'] > 2 or len(high_curvature) > 3:
        self.llm.temperature = min(0.9, self.llm.temperature * 0.8)
        self.llm.top_p = max(0.7, self.llm.top_p * 0.9)
        self.logger.info(f"检测到幻觉风险: {self.geometry_metrics}")
    
    return self.geometry_metrics
```
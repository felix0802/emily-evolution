# Auto-generated code snippet by Emily Self-Modify
# Based on: LLM适应选择, 马尔可夫毯因果发现
# Generated: 2026-09-08T01:43:21.629411

def adaptive_llm_selection(self, task_type):
    """LLM适应选择：根据任务类型动态选择最优LLM配置"""
    task_profiles = {
        'paper_summary': {'model': 'gpt-4', 'temperature': 0.3, 'max_tokens': 500},
        'code_generation': {'model': 'gpt-4', 'temperature': 0.7, 'max_tokens': 1000},
        'data_analysis': {'model': 'gpt-3.5-turbo', 'temperature': 0.1, 'max_tokens': 800},
        'creative_writing': {'model': 'gpt-4', 'temperature': 0.9, 'max_tokens': 600}
    }
    config = task_profiles.get(task_type, task_profiles['paper_summary'])
    
    # 马尔可夫毯因果发现：识别影响LLM输出的关键因素
    causal_factors = self.mb_causal_discovery(
        target='llm_quality',
        candidates=['model', 'temperature', 'max_tokens', 'task_complexity', 'context_length']
    )
    
    # 根据因果发现结果动态调整参数
    if 'temperature' in causal_factors['direct_causes']:
        config['temperature'] = min(1.0, config['temperature'] * 1.1)
    if 'max_tokens' in causal_factors['direct_causes']:
        config['max_tokens'] = min(2000, config['max_tokens'] + 100)
    
    self.llm_config = config
    return config

def mb_causal_discovery(self, target, candidates):
    """马尔可夫毯因果发现：识别目标变量的直接因果因素"""
    # 简化实现：基于历史性能数据
    if not hasattr(self, 'performance_history'):
        self.performance_history = []
    
    # 收集最近50次任务性能数据
    recent_data = self.performance_history[-50:] if self.performance_history else []
    
    # 计算各候选因素与目标的相关性
    correlations = {}
    for factor in candidates:
        if factor in recent_data:
            corr = self._calculate_correlation(recent_data, factor, target)
            correlations[factor] = corr
    
    # 马尔可夫毯：选择与目标直接相关且相互独立的因素
    direct_causes = []
    sorted_factors = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
    
    for factor, corr in sorted_factors:
        if abs(corr) > 0.3:  # 相关性阈值
            # 检查是否与已选因素独立
            independent = True
            for existing in direct_causes:
                if abs(self._calculate_correlation(recent_data, factor, existing)) > 0.7:
                    independent = False
                    break
            if independent:
                direct_causes.append(factor)
    
    return {'direct_causes': direct_causes, 'correlations': correlations}

def _calculate_correlation(self, data, var1, var2):
    """计算两个变量间的相关系数"""
    if not data or var1 not in data or var2 not in data:
        return 0.0
    import numpy as np
    v1 = np.array([d[var1] for d in data])
    v2 = np.array([d[var2] for d in data])
    if len(v1) < 2 or np.std(v1) == 0 or np.std(v2) == 0:
        return 0.0
    return np.corrcoef(v1, v2)[0, 1]

# 在evolve()中调用
self.adaptive_llm_selection('paper_summary')
# Auto-generated code snippet by Emily Self-Modify
# Based on: 自适应小-大模型协同, 加性图神经网络
# Generated: 2026-09-01T22:08:55.932347

```python
def adaptive_small_large_synergy(self, query: str, small_model: str = "gpt-4o-mini", large_model: str = "gpt-4o") -> str:
    """自适应小-大模型协同：先用小模型快速筛选，再用大模型深度分析"""
    # 小模型快速初筛（低延迟、低成本）
    quick_summary = self.llm_call(small_model, f"快速提取关键信息: {query[:500]}")
    
    # 基于初筛结果判断是否需要大模型深度处理
    complexity_score = len(quick_summary) / 100 + (1 if "复杂" in quick_summary or "多维度" in quick_summary else 0)
    
    if complexity_score > 0.8:
        # 高复杂度任务 → 大模型深度分析
        deep_analysis = self.llm_call(large_model, f"深度分析以下内容: {query}\n初步摘要: {quick_summary}")
        return f"[深度分析] {deep_analysis}"
    else:
        # 低复杂度任务 → 直接使用小模型结果
        return f"[快速响应] {quick_summary}"

def additive_gnn_enhancement(self, node_features: list, edge_index: list) -> list:
    """加性图神经网络：增强节点特征表示，用于决策层"""
    import numpy as np
    
    # 构建简单加性GNN层（无参数，纯拓扑聚合）
    features = np.array(node_features, dtype=float)
    adj_matrix = np.zeros((len(features), len(features)))
    for src, dst in edge_index:
        adj_matrix[src][dst] = 1.0
        adj_matrix[dst][src] = 1.0
    
    # 加性聚合（保留原始特征 + 邻居特征加权和）
    degree = adj_matrix.sum(axis=1, keepdims=True) + 1e-8
    normalized_adj = adj_matrix / degree
    aggregated = features + np.dot(normalized_adj, features)  # 加性更新
    
    # 归一化保持数值稳定
    return (aggregated / (np.linalg.norm(aggregated, axis=1, keepdims=True) + 1e-8)).tolist()

# 在evolve()中调用示例（需插入到合适位置）：
# enhanced_features = self.additive_gnn_enhancement(current_state_features, knowledge_graph_edges)
# final_decision = self.adaptive_small_large_synergy(str(enhanced_features), "gpt-4o-mini", "gpt-4o")
```
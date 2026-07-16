# Auto-generated code snippet by Emily Self-Modify
# Based on: 局部冗余度（Local Redundancy）, 显著性时间编辑（Salience-based Temporal Editing）
# Generated: 2026-07-16T07:51:52.743058

```python
def apply_salience_temporal_editing(self, papers):
    from collections import defaultdict
    import numpy as np
    salience_map = defaultdict(float)
    for i, paper in enumerate(papers):
        score = paper.get('relevance', 0.5) * (1.0 / (1.0 + i * 0.1))
        salience_map[paper['id']] = max(salience_map[paper['id']], score)
    sorted_papers = sorted(papers, key=lambda p: salience_map[p['id']], reverse=True)
    return sorted_papers[:max(1, len(sorted_papers) // 2)]
```
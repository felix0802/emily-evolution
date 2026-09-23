# Auto-generated code snippet by Emily Self-Modify
# Based on: 流式时间序列语言模型, 地图感知视觉运动策略
# Generated: 2026-09-23T02:05:14.316656

def integrate_streaming_map_awareness(self, sensor_stream, map_context):
    """Integrate streaming time-series LM with map-aware visuomotor policy."""
    import numpy as np
    from collections import deque

    if not hasattr(self, '_stream_buffer'):
        self._stream_buffer = deque(maxlen=64)
        self._map_cache = {}
        self._temporal_state = np.zeros(32)

    # Streaming time-series encoding
    for frame in sensor_stream:
        ts = np.asarray(frame.get('timeseries', []), dtype=np.float32)
        if ts.size == 0:
            continue
        norm = (ts - ts.mean()) / (ts.std() + 1e-6)
        self._stream_buffer.append(norm[-32:] if norm.size >= 32 else np.pad(norm, (32 - norm.size, 0)))

    if len(self._stream_buffer) < 4:
        return {'action': None, 'confidence': 0.0}

    seq = np.stack(list(self._stream_buffer)[-4:])
    # Lightweight temporal attention surrogate
    attn = np.exp(seq @ seq.T / np.sqrt(seq.shape[-1]))
    attn = attn / (attn.sum(axis=-1, keepdims=True) + 1e-6)
    temporal_feat = (attn @ seq).mean(axis=0)
    self._temporal_state = 0.7 * self._temporal_state + 0.3 * temporal_feat[:32]

    # Map-aware visuomotor grounding
    grid = map_context.get('occupancy_grid')
    pose = map_context.get('pose', (0.0, 0.0, 0.0))
    if grid is not None:
        g = np.asarray(grid, dtype=np.float32)
        cx = int(np.clip(pose[0], 0, g.shape[1] - 1))
        cy = int(np.clip(pose[1], 0, g.shape[0] - 1))
        r = 6
        patch = g[max(0, cy - r):cy + r + 1, max(0, cx - r):cx + r + 1]
        map_feat = np.array([patch.mean(), patch.std(), (patch > 0.5).mean()], dtype=np.float32)
        self._map_cache['last_patch'] = patch
    else:
        map_feat = np.zeros(3, dtype=np.float32)

    fused = np.concatenate([self._temporal_state, map_feat])
    action_vec = np.tanh(fused[:3])
    confidence = float(1.0 / (1.0 + np.exp(-fused.mean())))

    return {
        'action': action_vec.tolist(),
        'confidence': confidence,
        'temporal_state': self._temporal_state.copy(),
        'map_features': map_feat.tolist(),
    }
# Auto-generated code snippet by Emily Self-Modify
# Based on: GradientSHAP, 轴向注意力
# Generated: 2026-10-30T20:14:49.629745

def _axial_gradshap_attention_boost(perception_feats, llm_embeds, decision_logits, baseline=None):
    import numpy as np
    try:
        from captum.attr import GradientShap
        import torch
        import torch.nn as nn
    except Exception:
        return decision_logits

    class AxialAttentionBlock(nn.Module):
        def __init__(self, dim, heads=4):
            super().__init__()
            self.heads = heads
            self.scale = (dim // heads) ** -0.5
            self.qkv = nn.Linear(dim, dim * 3)
            self.proj = nn.Linear(dim, dim)
            self.row_attn = nn.MultiheadAttention(dim, heads, batch_first=True)
            self.col_attn = nn.MultiheadAttention(dim, heads, batch_first=True)

        def forward(self, x):
            b, h, w, d = x.shape
            rows = x.reshape(b * h, w, d)
            rows, _ = self.row_attn(rows, rows, rows)
            rows = rows.reshape(b, h, w, d)
            cols = rows.permute(0, 2, 1, 3).reshape(b * w, h, d)
            cols, _ = self.col_attn(cols, cols, cols)
            cols = cols.reshape(b, w, h, d).permute(0, 2, 1, 3)
            qkv = self.qkv(cols).chunk(3, dim=-1)
            q, k, v = [t.view(b, h, w, self.heads, -1).transpose(1, 2) for t in qkv]
            attn = (q @ k.transpose(-2, -1)) * self.scale
            attn = attn.softmax(dim=-1)
            out = (attn @ v).transpose(1, 2).reshape(b, h, w, d)
            return self.proj(out) + x

    try:
        p = np.asarray(perception_feats, dtype=np.float32)
        e = np.asarray(llm_embeds, dtype=np.float32)
        if p.ndim == 1:
            p = p.reshape(1, -1)
        if e.ndim == 1:
            e = e.reshape(1, -1)
        dim = min(p.shape[-1], e.shape[-1])
        fused = np.concatenate([p[:, :dim], e[:, :dim]], axis=0)
        side = int(np.ceil(np.sqrt(fused.shape[0])))
        pad = side * side - fused.shape[0]
        if pad > 0:
            fused = np.vstack([fused, np.zeros((pad, dim), dtype=np.float32)])
        grid = torch.tensor(fused.reshape(1, side, side, dim))
        block = AxialAttentionBlock(dim)
        block.eval()
        with torch.no_grad():
            enhanced = block(grid).reshape(-1, dim).numpy()[: fused.shape[0]]
        gs = GradientShap(lambda x: block(x.reshape(1, side, side, dim)).reshape(-1, dim))
        base = torch.zeros_like(grid) if baseline is None else torch.tensor(baseline)
        attributions = gs.attribute(grid, baselines=base, n_samples=8, stdevs=0.05)
        importance = attributions.abs().mean(dim=-1).reshape(-1).numpy()[: fused.shape[0]]
        weight = 1.0 + importance / (importance.max() + 1e-8)
        boosted = enhanced * weight[:, None]
        out = np.asarray(decision_logits, dtype=np.float32)
        if out.ndim == 1:
            out = out.reshape(1, -1)
        mix = min(out.shape[-1], boosted.shape[-1])
        out[:, :mix] = out[:, :mix] + 0.1 * boosted[: out.shape[0], :mix]
        return out
    except Exception:
        return decision_logits
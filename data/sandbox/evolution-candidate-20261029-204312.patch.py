# Auto-generated code snippet by Emily Self-Modify
# Based on: 离散视觉令牌, 自回归预训练+扩散后训练
# Generated: 2026-10-29T20:43:12.381526

def _discrete_visual_tokenizer(image_bytes, grid_size=16):
    import base64, math
    try:
        raw = base64.b64decode(image_bytes)
    except Exception:
        return []
    if not raw:
        return []
    n = len(raw)
    cell = max(1, n // (grid_size * grid_size))
    tokens = []
    for i in range(grid_size * grid_size):
        start = i * cell
        chunk = raw[start:start + cell]
        if not chunk:
            tokens.append(0)
            continue
        mean = sum(chunk) / len(chunk)
        var = sum((b - mean) ** 2 for b in chunk) / len(chunk)
        codebook_idx = int((mean / 256.0) * 8) * 8 + int(min(7, math.sqrt(var) / 16.0))
        tokens.append(codebook_idx)
    return tokens


def _autoregressive_diffusion_refine(tokens, steps=4, vocab=64):
    if not tokens:
        return tokens
    seq = list(tokens)
    n = len(seq)
    for step in range(steps):
        noise_scale = 1.0 / (step + 1)
        for i in range(n):
            ctx = seq[max(0, i - 2):i] + seq[i + 1:i + 3]
            if not ctx:
                continue
            pred = int(sum(ctx) / len(ctx))
            blended = int(seq[i] * (1 - noise_scale) + pred * noise_scale)
            seq[i] = max(0, min(vocab - 1, blended))
    return seq


def _enhance_with_visual_tokens(perception_output):
    if not isinstance(perception_output, dict):
        return perception_output
    img = perception_output.get("image_b64") or perception_output.get("image")
    if not img:
        return perception_output
    tokens = _discrete_visual_tokenizer(img)
    refined = _autoregressive_diffusion_refine(tokens)
    perception_output["visual_tokens"] = refined
    perception_output["visual_token_signature"] = hash(tuple(refined)) & 0xFFFFFFFF
    return perception_output


# 在 evolve() 中插入：
# perception_output = _enhance_with_visual_tokens(perception_output)
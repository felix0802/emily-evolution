# Auto-generated code snippet by Emily Self-Modify
# Based on: 不确定性 token 注入, 文本提示 3D 分割
# Generated: 2026-11-24T14:25:32.328582

def inject_uncertainty_tokens(perception_output, token_budget=8):
    import math, random
    if not perception_output or not isinstance(perception_output, dict):
        return perception_output
    feats = perception_output.get("features")
    if feats is None:
        return perception_output
    try:
        flat = []
        def _flatten(x):
            if isinstance(x, (list, tuple)):
                for i in x:
                    _flatten(i)
            elif isinstance(x, (int, float)):
                flat.append(float(x))
        _flatten(feats)
        if not flat:
            return perception_output
        mean = sum(flat) / len(flat)
        var = sum((v - mean) ** 2 for v in flat) / max(1, len(flat))
        std = math.sqrt(var) + 1e-8
        tokens = []
        for _ in range(min(token_budget, max(1, len(flat) // 4))):
            idx = random.randrange(len(flat))
            z = (flat[idx] - mean) / std
            conf = 1.0 / (1.0 + math.exp(-abs(z)))
            tokens.append({
                "idx": idx,
                "value": flat[idx],
                "z": round(z, 4),
                "confidence": round(conf, 4),
                "uncertain": conf < 0.6
            })
        perception_output["uncertainty_tokens"] = tokens
        perception_output["uncertainty_summary"] = {
            "mean": round(mean, 4),
            "std": round(std, 4),
            "n_uncertain": sum(1 for t in tokens if t["uncertain"])
        }
    except Exception:
        pass
    return perception_output


def text_prompt_3d_segment(scene, prompt, max_regions=5):
    import re
    if scene is None or not prompt:
        return {"regions": [], "prompt": prompt}
    keywords = [w.lower() for w in re.findall(r"[A-Za-z0-9_]+", prompt) if len(w) > 2]
    points = scene.get("points") if isinstance(scene, dict) else None
    if not points:
        return {"regions": [], "prompt": prompt, "keywords": keywords}
    regions = []
    try:
        n = len(points)
        chunk = max(1, n // max_regions)
        for r in range(max_regions):
            seg = points[r * chunk:(r + 1) * chunk]
            if not seg:
                continue
            cx = sum(p[0] for p in seg) / len(seg)
            cy = sum(p[1] for p in seg) / len(seg)
            cz = sum(p[2] for p in seg) / len(seg) if len(seg[0]) > 2 else 0.0
            regions.append({
                "region_id": r,
                "centroid": [round(cx, 3), round(cy, 3), round(cz, 3)],
                "size": len(seg),
                "matched_keywords": keywords[:2]
            })
    except Exception:
        pass
    return {"regions": regions, "prompt": prompt, "keywords": keywords}


def evolve_with_new_tech(perception_output, scene, prompt):
    perception_output = inject_uncertainty_tokens(perception_output)
    seg = text_prompt_3d_segment(scene, prompt)
    return {
        "perception": perception_output,
        "segmentation": seg,
        "tech": ["uncertainty_token_injection", "text_prompt_3d_segmentation"]
    }
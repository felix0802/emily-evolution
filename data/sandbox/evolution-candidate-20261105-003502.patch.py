# Auto-generated code snippet by Emily Self-Modify
# Based on: 视频扩散模型, 3D Gaussian Splatting 压缩
# Generated: 2026-11-05T00:35:02.043427

def _enhance_with_video_diffusion_and_3dgs(self, papers, repo_context):
    import hashlib
    import math

    def _hash_vec(text, dim=64):
        h = hashlib.sha256(text.encode("utf-8")).digest()
        return [((h[i % len(h)] / 255.0) * 2 - 1) for i in range(dim)]

    def _cosine(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a)) or 1e-9
        nb = math.sqrt(sum(y * y for y in b)) or 1e-9
        return dot / (na * nb)

    def _video_diffusion_score(paper):
        title = paper.get("title", "")
        abstract = paper.get("abstract", "")
        text = f"{title} {abstract}".lower()
        temporal_tokens = ["temporal", "video", "frame", "motion", "diffusion", "denois"]
        score = sum(1 for t in temporal_tokens if t in text) / len(temporal_tokens)
        vec = _hash_vec(text)
        coherence = abs(_cosine(vec, _hash_vec(title)))
        return 0.6 * score + 0.4 * coherence

    def _3dgs_compress_score(paper):
        text = f"{paper.get('title','')} {paper.get('abstract','')}".lower()
        tokens = ["gaussian", "splatting", "3d", "compress", "prune", "quantiz", "render"]
        hits = sum(1 for t in tokens if t in text)
        density = hits / len(tokens)
        vec = _hash_vec(text, dim=32)
        entropy = -sum((abs(v) + 1e-9) * math.log(abs(v) + 1e-9) for v in vec) / len(vec)
        return 0.7 * density + 0.3 * min(1.0, entropy)

    enriched = []
    for p in papers:
        vd = _video_diffusion_score(p)
        gs = _3dgs_compress_score(p)
        p["_vd_score"] = round(vd, 4)
        p["_3dgs_score"] = round(gs, 4)
        p["_combined_score"] = round(0.5 * vd + 0.5 * gs, 4)
        enriched.append(p)

    enriched.sort(key=lambda x: x["_combined_score"], reverse=True)
    top = enriched[:5]

    self.memory.setdefault("tech_signals", {})
    self.memory["tech_signals"]["video_diffusion"] = [
        {"title": p.get("title", ""), "score": p["_vd_score"]} for p in top
    ]
    self.memory["tech_signals"]["3dgs_compression"] = [
        {"title": p.get("title", ""), "score": p["_3dgs_score"]} for p in top
    ]

    if repo_context is not None:
        repo_context["suggested_focus"] = [
            "temporal-consistency-in-diffusion",
            "gaussian-pruning-and-quantization",
        ]
    return enriched